from typing import List, Optional
from datetime import datetime, date, timedelta
from litestar import Router, get, post, put, delete, Request
from litestar.controller import Controller
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotAuthorizedException, PermissionDeniedException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.core.database import get_db
from app.core.security import decode_token
from app.models import (
    User, UserRole, Order, OrderStatus, CustomerReview,
    ComplaintType, ComplaintStatus, ComplaintSource, CompensationType,
    ComplaintTicket, CompensationRecord,
)
from app.schemas.complaints import (
    ComplaintTicketCreate,
    ComplaintTicketManualCreate,
    ComplaintTicketUpdate,
    ComplaintTicketResponse,
    ComplaintTicketListItem,
    ComplaintTicketDetail,
    ComplaintAssign,
    ComplaintProcess,
    ComplaintResolve,
    CompensationCreate,
    CompensationUpdate,
    CompensationResponse,
    CompensationDetail,
    ComplaintDashboardStats,
    ComplaintTrendItem,
    OverdueComplaintItem,
)


def provide_db() -> Session:
    return next(get_db())


def get_current_user_from_request(request: Request, db: Session) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise NotAuthorizedException("未提供认证令牌")
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise NotAuthorizedException("认证方案无效")
    except ValueError:
        raise NotAuthorizedException("认证头格式无效")

    payload = decode_token(token)
    if not payload:
        raise NotAuthorizedException("令牌无效或已过期")

    user_id = payload.get("sub")
    if not user_id:
        raise NotAuthorizedException("令牌内容无效")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise NotAuthorizedException("用户不存在")
    if not user.is_active:
        raise NotAuthorizedException("用户已被禁用")
    return user


LOW_RATING_THRESHOLD = 3
COMPLAINT_PROCESS_DAYS = 3


def generate_ticket_no() -> str:
    now = datetime.utcnow()
    return f"TS{now.strftime('%Y%m%d%H%M%S')}{now.microsecond // 1000:03d}"


def auto_create_complaint_from_review(db: Session, review: CustomerReview) -> Optional[ComplaintTicket]:
    if review.rating > LOW_RATING_THRESHOLD:
        return None

    existing = db.query(ComplaintTicket).filter(
        ComplaintTicket.order_id == review.order_id,
        ComplaintTicket.source == ComplaintSource.AUTO_LOW_RATING,
    ).first()
    if existing:
        return None

    order = db.query(Order).filter(Order.id == review.order_id).first()
    if not order:
        return None

    type_map = {
        "quality": ComplaintType.QUALITY,
        "service": ComplaintType.SERVICE,
        "delivery": ComplaintType.DELIVERY,
        "attitude": ComplaintType.ATTITUDE,
    }
    complaint_type = ComplaintType.OTHER
    if review.tags:
        for tag in review.tags.split(","):
            tag_lower = tag.strip().lower()
            for key, ct in type_map.items():
                if key in tag_lower:
                    complaint_type = ct
                    break
            if complaint_type != ComplaintType.OTHER:
                break

    title_map = {
        ComplaintType.QUALITY: "照片质量问题投诉",
        ComplaintType.SERVICE: "服务态度问题投诉",
        ComplaintType.DELIVERY: "交付延迟问题投诉",
        ComplaintType.ATTITUDE: "工作人员态度投诉",
        ComplaintType.OTHER: "客户低分评价投诉",
    }

    ticket = ComplaintTicket(
        ticket_no=generate_ticket_no(),
        order_id=review.order_id,
        customer_id=order.customer_id,
        complaint_type=complaint_type,
        source=ComplaintSource.AUTO_LOW_RATING,
        title=title_map[complaint_type],
        description=review.feedback or f"客户给出{review.rating}星低分评价，系统自动生成投诉工单。",
        status=ComplaintStatus.PENDING,
        rating_trigger=review.rating,
        process_deadline=datetime.utcnow() + timedelta(days=COMPLAINT_PROCESS_DAYS),
        created_at=datetime.utcnow(),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


class ComplaintsController(Controller):
    path = "/complaints"
    dependencies = {"db": Provide(provide_db)}

    def _check_ticket_permission(self, ticket: ComplaintTicket, user: User, db: Session) -> None:
        if user.role in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            return
        if user.role == UserRole.CUSTOMER and ticket.customer_id == user.id:
            return
        if ticket.assigned_to == user.id:
            return
        raise PermissionDeniedException("权限不足")

    @get("/")
    async def list_complaints(
        self,
        request: Request,
        db: Session,
        complaint_type: Optional[ComplaintType] = None,
        status: Optional[ComplaintStatus] = None,
        photographer_id: Optional[int] = None,
        has_compensation: Optional[bool] = None,
        order_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ComplaintTicketListItem]:
        user = get_current_user_from_request(request, db)
        query = db.query(ComplaintTicket).join(Order, ComplaintTicket.order_id == Order.id)

        if user.role == UserRole.CUSTOMER:
            query = query.filter(Order.customer_id == user.id)
        elif user.role == UserRole.PHOTOGRAPHER:
            query = query.filter(
                (Order.photographer_id == user.id) | (Order.photographer_id.is_(None))
            )

        if complaint_type:
            query = query.filter(ComplaintTicket.complaint_type == complaint_type)
        if status:
            query = query.filter(ComplaintTicket.status == status)
        if photographer_id and user.role in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            query = query.filter(Order.photographer_id == photographer_id)
        if order_id:
            query = query.filter(ComplaintTicket.order_id == order_id)

        tickets = query.order_by(ComplaintTicket.created_at.desc()).offset(skip).limit(limit).all()
        now = datetime.utcnow()
        result: List[ComplaintTicketListItem] = []
        for t in tickets:
            order = db.query(Order).filter(Order.id == t.order_id).first()
            customer = db.query(User).filter(User.id == t.customer_id).first()
            photographer = db.query(User).filter(User.id == order.photographer_id).first() if order and order.photographer_id else None
            assignee = db.query(User).filter(User.id == t.assigned_to).first() if t.assigned_to else None
            compensation = db.query(CompensationRecord).filter(CompensationRecord.complaint_id == t.id).first()

            is_overdue = False
            if t.process_deadline and t.status not in [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED, ComplaintStatus.CANCELLED]:
                is_overdue = t.process_deadline < now

            item = ComplaintTicketListItem(
                id=t.id,
                ticket_no=t.ticket_no,
                order_id=t.order_id,
                order_no=order.order_no if order else None,
                customer_id=t.customer_id,
                customer_name=customer.full_name if customer else None,
                photographer_id=order.photographer_id if order else None,
                photographer_name=photographer.full_name if photographer else None,
                complaint_type=t.complaint_type,
                source=t.source,
                title=t.title,
                status=t.status,
                rating_trigger=t.rating_trigger,
                assigned_to=t.assigned_to,
                assignee_name=assignee.full_name if assignee else None,
                process_deadline=t.process_deadline,
                has_compensation=compensation is not None,
                is_overdue=is_overdue,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )

            if has_compensation is not None:
                if has_compensation and not item.has_compensation:
                    continue
                if not has_compensation and item.has_compensation:
                    continue

            result.append(item)
        return result

    @get("/{ticket_id:int}")
    async def get_complaint(
        self, request: Request, db: Session, ticket_id: int
    ) -> ComplaintTicketDetail:
        user = get_current_user_from_request(request, db)
        ticket = db.query(ComplaintTicket).filter(ComplaintTicket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="投诉工单不存在")

        order = db.query(Order).filter(Order.id == ticket.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="关联订单不存在")
        self._check_ticket_permission(ticket, user, db)

        customer = db.query(User).filter(User.id == ticket.customer_id).first()
        photographer = db.query(User).filter(User.id == order.photographer_id).first() if order.photographer_id else None
        assignee = db.query(User).filter(User.id == ticket.assigned_to).first() if ticket.assigned_to else None
        creator = db.query(User).filter(User.id == ticket.created_by).first() if ticket.created_by else None
        compensation = db.query(CompensationRecord).filter(CompensationRecord.complaint_id == ticket.id).first()

        now = datetime.utcnow()
        is_overdue = False
        if ticket.process_deadline and ticket.status not in [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED, ComplaintStatus.CANCELLED]:
            is_overdue = ticket.process_deadline < now

        comp_detail = None
        if compensation:
            approver = db.query(User).filter(User.id == compensation.approved_by).first() if compensation.approved_by else None
            executor = db.query(User).filter(User.id == compensation.executed_by).first() if compensation.executed_by else None
            comp_detail = CompensationDetail(
                **CompensationResponse.model_validate(compensation).model_dump(),
                approver_name=approver.full_name if approver else None,
                executor_name=executor.full_name if executor else None,
            )

        resp = ComplaintTicketDetail(
            **ComplaintTicketResponse.model_validate(ticket).model_dump(),
            order_no=order.order_no,
            customer_name=customer.full_name if customer else None,
            photographer_id=order.photographer_id,
            photographer_name=photographer.full_name if photographer else None,
            shoot_date=order.shoot_date,
            assignee_name=assignee.full_name if assignee else None,
            creator_name=creator.full_name if creator else None,
            compensation=comp_detail,
            is_overdue=is_overdue,
        )
        return resp

    @post("/")
    async def create_complaint(
        self, request: Request, db: Session, data: ComplaintTicketCreate
    ) -> ComplaintTicketResponse:
        user = get_current_user_from_request(request, db)

        order = db.query(Order).filter(Order.id == data.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        if user.role == UserRole.CUSTOMER:
            if order.customer_id != user.id:
                raise PermissionDeniedException("只能对自己的订单提交投诉")
            customer_id = user.id
            source = ComplaintSource.CUSTOMER_INITIATED
        else:
            customer_id = order.customer_id
            source = data.source if data.source != ComplaintSource.CUSTOMER_INITIATED else ComplaintSource.MANUAL

        existing_open = db.query(ComplaintTicket).filter(
            ComplaintTicket.order_id == data.order_id,
            ComplaintTicket.status.notin_([ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED, ComplaintStatus.CANCELLED]),
        ).first()
        if existing_open and user.role == UserRole.CUSTOMER:
            raise HTTPException(status_code=400, detail="该订单已有未关闭的投诉工单")

        ticket = ComplaintTicket(
            ticket_no=generate_ticket_no(),
            order_id=data.order_id,
            customer_id=customer_id,
            complaint_type=data.complaint_type,
            source=source,
            title=data.title,
            description=data.description,
            status=ComplaintStatus.PENDING,
            process_deadline=datetime.utcnow() + timedelta(days=COMPLAINT_PROCESS_DAYS),
            created_by=user.id if user.role != UserRole.CUSTOMER else None,
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ComplaintTicketResponse.model_validate(ticket)

    @post("/manual")
    async def create_complaint_manual(
        self, request: Request, db: Session, data: ComplaintTicketManualCreate
    ) -> ComplaintTicketResponse:
        user = get_current_user_from_request(request, db)
        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            raise PermissionDeniedException("只有管理员和摄影师可以手动创建投诉工单")

        order = db.query(Order).filter(Order.id == data.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        ticket = ComplaintTicket(
            ticket_no=generate_ticket_no(),
            order_id=data.order_id,
            customer_id=data.customer_id,
            complaint_type=data.complaint_type,
            source=ComplaintSource.MANUAL,
            title=data.title,
            description=data.description,
            status=ComplaintStatus.PENDING,
            process_deadline=datetime.utcnow() + timedelta(days=COMPLAINT_PROCESS_DAYS),
            created_by=user.id,
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ComplaintTicketResponse.model_validate(ticket)

    @put("/{ticket_id:int}")
    async def update_complaint(
        self,
        request: Request,
        db: Session,
        ticket_id: int,
        data: ComplaintTicketUpdate,
    ) -> ComplaintTicketResponse:
        user = get_current_user_from_request(request, db)
        ticket = db.query(ComplaintTicket).filter(ComplaintTicket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="投诉工单不存在")

        if user.role == UserRole.CUSTOMER:
            if ticket.customer_id != user.id:
                raise PermissionDeniedException("权限不足")
            allowed_fields = {"description", "title", "complaint_type"}
            update_data = {k: v for k, v in data.model_dump(exclude_unset=True).items() if k in allowed_fields}
        else:
            update_data = data.model_dump(exclude_unset=True)

        if "status" in update_data and update_data["status"] in [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED]:
            ticket.resolved_at = datetime.utcnow()

        if "assigned_to" in update_data and update_data["assigned_to"]:
            ticket.assigned_at = datetime.utcnow()
            if ticket.status == ComplaintStatus.PENDING:
                ticket.status = ComplaintStatus.ASSIGNED

        for key, value in update_data.items():
            setattr(ticket, key, value)

        db.commit()
        db.refresh(ticket)
        return ComplaintTicketResponse.model_validate(ticket)

    @post("/{ticket_id:int}/assign")
    async def assign_complaint(
        self,
        request: Request,
        db: Session,
        ticket_id: int,
        data: ComplaintAssign,
    ) -> ComplaintTicketResponse:
        user = get_current_user_from_request(request, db)
        if user.role not in [UserRole.ADMIN]:
            raise PermissionDeniedException("只有管理员可以分配投诉工单")

        ticket = db.query(ComplaintTicket).filter(ComplaintTicket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="投诉工单不存在")

        assignee = db.query(User).filter(User.id == data.assigned_to).first()
        if not assignee:
            raise HTTPException(status_code=404, detail="处理人不存在")

        ticket.assigned_to = data.assigned_to
        ticket.assigned_at = datetime.utcnow()
        if data.process_deadline:
            ticket.process_deadline = data.process_deadline
        elif not ticket.process_deadline:
            ticket.process_deadline = datetime.utcnow() + timedelta(days=COMPLAINT_PROCESS_DAYS)

        if ticket.status == ComplaintStatus.PENDING:
            ticket.status = ComplaintStatus.ASSIGNED

        db.commit()
        db.refresh(ticket)
        return ComplaintTicketResponse.model_validate(ticket)

    @post("/{ticket_id:int}/process")
    async def process_complaint(
        self,
        request: Request,
        db: Session,
        ticket_id: int,
        data: ComplaintProcess,
    ) -> ComplaintTicketResponse:
        user = get_current_user_from_request(request, db)
        ticket = db.query(ComplaintTicket).filter(ComplaintTicket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="投诉工单不存在")

        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            raise PermissionDeniedException("权限不足")
        if ticket.assigned_to and ticket.assigned_to != user.id and user.role != UserRole.ADMIN:
            raise PermissionDeniedException("只有被指定的处理人或管理员可以处理此工单")

        if ticket.progress_notes:
            new_note = f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] {user.full_name}: {data.progress_notes}\n"
            ticket.progress_notes = new_note + ticket.progress_notes
        else:
            ticket.progress_notes = f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] {user.full_name}: {data.progress_notes}"

        if data.status:
            ticket.status = data.status
        elif ticket.status in [ComplaintStatus.PENDING, ComplaintStatus.ASSIGNED]:
            ticket.status = ComplaintStatus.PROCESSING

        if data.status in [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED]:
            ticket.resolved_at = datetime.utcnow()

        db.commit()
        db.refresh(ticket)
        return ComplaintTicketResponse.model_validate(ticket)

    @post("/{ticket_id:int}/resolve")
    async def resolve_complaint(
        self,
        request: Request,
        db: Session,
        ticket_id: int,
        data: ComplaintResolve,
    ) -> ComplaintTicketResponse:
        user = get_current_user_from_request(request, db)
        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            raise PermissionDeniedException("权限不足")

        ticket = db.query(ComplaintTicket).filter(ComplaintTicket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="投诉工单不存在")

        ticket.final_conclusion = data.final_conclusion
        ticket.status = data.status if data.status else ComplaintStatus.RESOLVED
        ticket.resolved_at = datetime.utcnow()

        db.commit()
        db.refresh(ticket)
        return ComplaintTicketResponse.model_validate(ticket)

    @delete("/{ticket_id:int}", status_code=200)
    async def delete_complaint(self, request: Request, db: Session, ticket_id: int) -> dict:
        user = get_current_user_from_request(request, db)
        if user.role != UserRole.ADMIN:
            raise PermissionDeniedException("只有管理员可以删除投诉工单")

        ticket = db.query(ComplaintTicket).filter(ComplaintTicket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="投诉工单不存在")

        db.delete(ticket)
        db.commit()
        return {"message": "投诉工单已删除"}

    @post("/{ticket_id:int}/compensation")
    async def create_compensation(
        self,
        request: Request,
        db: Session,
        ticket_id: int,
        data: CompensationCreate,
    ) -> CompensationResponse:
        user = get_current_user_from_request(request, db)
        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            raise PermissionDeniedException("权限不足")

        ticket = db.query(ComplaintTicket).filter(ComplaintTicket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="投诉工单不存在")

        existing = db.query(CompensationRecord).filter(CompensationRecord.complaint_id == ticket_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="该投诉工单已有补偿方案")

        compensation = CompensationRecord(
            complaint_id=ticket_id,
            compensation_type=data.compensation_type,
            amount=data.amount,
            description=data.description,
        )
        db.add(compensation)

        if ticket.status not in [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED]:
            ticket.status = ComplaintStatus.COMPENSATED

        db.commit()
        db.refresh(compensation)
        return CompensationResponse.model_validate(compensation)

    @put("/{ticket_id:int}/compensation")
    async def update_compensation(
        self,
        request: Request,
        db: Session,
        ticket_id: int,
        data: CompensationUpdate,
    ) -> CompensationResponse:
        user = get_current_user_from_request(request, db)
        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            raise PermissionDeniedException("权限不足")

        compensation = db.query(CompensationRecord).filter(CompensationRecord.complaint_id == ticket_id).first()
        if not compensation:
            raise HTTPException(status_code=404, detail="补偿方案不存在")

        update_data = data.model_dump(exclude_unset=True)

        if "is_executed" in update_data and update_data["is_executed"] and not compensation.is_executed:
            compensation.executed_at = datetime.utcnow()
            compensation.executed_by = user.id

        for key, value in update_data.items():
            setattr(compensation, key, value)

        db.commit()
        db.refresh(compensation)
        return CompensationResponse.model_validate(compensation)

    @post("/{ticket_id:int}/compensation/approve")
    async def approve_compensation(
        self,
        request: Request,
        db: Session,
        ticket_id: int,
    ) -> CompensationResponse:
        user = get_current_user_from_request(request, db)
        if user.role != UserRole.ADMIN:
            raise PermissionDeniedException("只有管理员可以审批补偿方案")

        compensation = db.query(CompensationRecord).filter(CompensationRecord.complaint_id == ticket_id).first()
        if not compensation:
            raise HTTPException(status_code=404, detail="补偿方案不存在")

        compensation.approved_by = user.id
        compensation.approved_at = datetime.utcnow()

        db.commit()
        db.refresh(compensation)
        return CompensationResponse.model_validate(compensation)

    @post("/{ticket_id:int}/compensation/execute")
    async def execute_compensation(
        self,
        request: Request,
        db: Session,
        ticket_id: int,
    ) -> CompensationResponse:
        user = get_current_user_from_request(request, db)
        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            raise PermissionDeniedException("权限不足")

        compensation = db.query(CompensationRecord).filter(CompensationRecord.complaint_id == ticket_id).first()
        if not compensation:
            raise HTTPException(status_code=404, detail="补偿方案不存在")

        compensation.is_executed = True
        compensation.executed_at = datetime.utcnow()
        compensation.executed_by = user.id

        ticket = db.query(ComplaintTicket).filter(ComplaintTicket.id == ticket_id).first()
        if ticket and ticket.status not in [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED]:
            ticket.status = ComplaintStatus.COMPENSATED

        db.commit()
        db.refresh(compensation)
        return CompensationResponse.model_validate(compensation)

    @get("/dashboard-stats")
    async def get_complaint_dashboard_stats(
        self, request: Request, db: Session
    ) -> ComplaintDashboardStats:
        user = get_current_user_from_request(request, db)
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)

        query_30d = db.query(ComplaintTicket).filter(ComplaintTicket.created_at >= thirty_days_ago)
        all_query = db.query(ComplaintTicket)

        if user.role == UserRole.PHOTOGRAPHER:
            query_30d = query_30d.join(Order).filter(Order.photographer_id == user.id)
            all_query = all_query.join(Order).filter(
                (Order.photographer_id == user.id) | (Order.photographer_id.is_(None))
            )
        elif user.role == UserRole.CUSTOMER:
            query_30d = query_30d.filter(ComplaintTicket.customer_id == user.id)
            all_query = all_query.filter(ComplaintTicket.customer_id == user.id)

        tickets_30d = query_30d.all()
        total_complaints_30d = len(tickets_30d)
        resolved_count_30d = sum(1 for t in tickets_30d if t.status in [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED, ComplaintStatus.COMPENSATED])

        all_tickets = all_query.all()
        pending_count = sum(1 for t in all_tickets if t.status == ComplaintStatus.PENDING)
        processing_count = sum(1 for t in all_tickets if t.status in [ComplaintStatus.ASSIGNED, ComplaintStatus.PROCESSING])

        overdue_complaints_list: List[OverdueComplaintItem] = []
        overdue_count = 0
        for t in all_tickets:
            if t.status not in [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED, ComplaintStatus.CANCELLED]:
                if t.process_deadline and t.process_deadline < now:
                    overdue_count += 1
                    order = db.query(Order).filter(Order.id == t.order_id).first()
                    customer = db.query(User).filter(User.id == t.customer_id).first()
                    assignee = db.query(User).filter(User.id == t.assigned_to).first() if t.assigned_to else None
                    overdue_days = (now - t.process_deadline).days
                    if len(overdue_complaints_list) < 10:
                        overdue_complaints_list.append(OverdueComplaintItem(
                            id=t.id,
                            ticket_no=t.ticket_no,
                            order_no=order.order_no if order else None,
                            customer_name=customer.full_name if customer else None,
                            status=t.status,
                            overdue_days=overdue_days,
                            process_deadline=t.process_deadline,
                            assigned_to=t.assigned_to,
                            assignee_name=assignee.full_name if assignee else None,
                        ))

        comp_query = db.query(CompensationRecord).join(ComplaintTicket).filter(
            CompensationRecord.created_at >= thirty_days_ago
        )
        if user.role == UserRole.PHOTOGRAPHER:
            comp_query = comp_query.join(Order, ComplaintTicket.order_id == Order.id).filter(
                (Order.photographer_id == user.id) | (Order.photographer_id.is_(None))
            )
        elif user.role == UserRole.CUSTOMER:
            comp_query = comp_query.filter(ComplaintTicket.customer_id == user.id)
        compensations = comp_query.all()
        total_compensation_amount = sum(c.amount for c in compensations)
        compensation_count = len(compensations)

        resolve_hours = []
        for t in tickets_30d:
            if t.status in [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED, ComplaintStatus.COMPENSATED] and t.resolved_at:
                hours = (t.resolved_at - t.created_at).total_seconds() / 3600
                resolve_hours.append(hours)
        avg_resolve_hours = round(sum(resolve_hours) / len(resolve_hours), 1) if resolve_hours else 0.0

        trend_map = {}
        for t in tickets_30d:
            d = t.created_at.date()
            if d not in trend_map:
                trend_map[d] = {"complaint_count": 0, "resolved_count": 0}
            trend_map[d]["complaint_count"] += 1
            if t.status in [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED, ComplaintStatus.COMPENSATED] and t.resolved_at:
                rd = t.resolved_at.date()
                if rd not in trend_map:
                    trend_map[rd] = {"complaint_count": 0, "resolved_count": 0}
                trend_map[rd]["resolved_count"] += 1

        complaint_trend: List[ComplaintTrendItem] = []
        for i in range(29, -1, -1):
            d = (now - timedelta(days=i)).date()
            if d in trend_map:
                complaint_trend.append(ComplaintTrendItem(
                    date=d,
                    complaint_count=trend_map[d]["complaint_count"],
                    resolved_count=trend_map[d]["resolved_count"],
                ))
            else:
                complaint_trend.append(ComplaintTrendItem(date=d, complaint_count=0, resolved_count=0))

        type_dist = {}
        for ct in ComplaintType:
            count = sum(1 for t in tickets_30d if t.complaint_type == ct)
            type_dist[ct.value] = count

        return ComplaintDashboardStats(
            total_complaints_30d=total_complaints_30d,
            pending_count=pending_count,
            processing_count=processing_count,
            resolved_count_30d=resolved_count_30d,
            overdue_count=overdue_count,
            total_compensation_amount=round(total_compensation_amount, 2),
            compensation_count=compensation_count,
            avg_resolve_hours=avg_resolve_hours,
            complaint_trend=complaint_trend,
            overdue_complaints=overdue_complaints_list,
            type_distribution=type_dist,
        )


complaints_router = Router(route_handlers=[ComplaintsController], path="/api")
