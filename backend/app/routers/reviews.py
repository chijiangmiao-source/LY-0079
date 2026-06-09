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
    User, UserRole, Order, OrderStatus, CustomerReview, FollowUpRecord,
    FollowUpStatus, AfterSalesResult,
)
from app.schemas.reviews import (
    CustomerReviewCreate,
    CustomerReviewUpdate,
    CustomerReviewResponse,
    CustomerReviewDetail,
    FollowUpRecordCreate,
    FollowUpRecordUpdate,
    FollowUpRecordResponse,
    FollowUpRecordDetail,
    FollowUpListItem,
    SatisfactionTrendItem,
    LowScoreOrder,
    PendingFollowUpStat,
    ReviewDashboardStats,
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


REVIEW_DEADLINE_DAYS = 7


class ReviewsController(Controller):
    path = "/reviews"
    dependencies = {"db": Provide(provide_db)}

    def _check_order_permission(self, order: Order, user: User) -> None:
        if user.role in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            return
        if user.role == UserRole.CUSTOMER and order.customer_id == user.id:
            return
        raise PermissionDeniedException("权限不足")

    @get("/follow-ups")
    async def list_follow_ups(
        self,
        request: Request,
        db: Session,
        status: Optional[FollowUpStatus] = None,
        satisfaction_min: Optional[int] = None,
        satisfaction_max: Optional[int] = None,
        photographer_id: Optional[int] = None,
        order_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[FollowUpListItem]:
        user = get_current_user_from_request(request, db)
        query = db.query(FollowUpRecord).join(Order, FollowUpRecord.order_id == Order.id)

        if user.role == UserRole.CUSTOMER:
            query = query.filter(Order.customer_id == user.id)
        elif user.role == UserRole.PHOTOGRAPHER:
            query = query.filter(
                (Order.photographer_id == user.id) | (Order.photographer_id.is_(None))
            )

        if status:
            query = query.filter(FollowUpRecord.status == status)
        if satisfaction_min is not None:
            query = query.filter(FollowUpRecord.satisfaction >= satisfaction_min)
        if satisfaction_max is not None:
            query = query.filter(FollowUpRecord.satisfaction <= satisfaction_max)
        if photographer_id and user.role in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            query = query.filter(Order.photographer_id == photographer_id)
        if order_id:
            query = query.filter(FollowUpRecord.order_id == order_id)

        records = query.order_by(FollowUpRecord.created_at.desc()).offset(skip).limit(limit).all()
        result: List[FollowUpListItem] = []
        for r in records:
            order = db.query(Order).filter(Order.id == r.order_id).first()
            customer = db.query(User).filter(User.id == order.customer_id).first() if order else None
            photographer = db.query(User).filter(User.id == order.photographer_id).first() if order and order.photographer_id else None
            review = db.query(CustomerReview).filter(CustomerReview.order_id == r.order_id).first()

            item = FollowUpListItem.model_validate(r)
            item.order_no = order.order_no if order else None
            item.customer_name = customer.full_name if customer else None
            item.photographer_id = order.photographer_id if order else None
            item.photographer_name = photographer.full_name if photographer else None
            item.shoot_date = order.shoot_date if order else None
            item.customer_rating = review.rating if review else None
            result.append(item)
        return result

    @get("/follow-ups/{record_id:int}")
    async def get_follow_up(
        self, request: Request, db: Session, record_id: int
    ) -> FollowUpRecordDetail:
        user = get_current_user_from_request(request, db)
        record = db.query(FollowUpRecord).filter(FollowUpRecord.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="回访记录不存在")

        order = db.query(Order).filter(Order.id == record.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="关联订单不存在")
        self._check_order_permission(order, user)

        customer = db.query(User).filter(User.id == order.customer_id).first()
        photographer = db.query(User).filter(User.id == order.photographer_id).first() if order.photographer_id else None
        follow_up_user = db.query(User).filter(User.id == record.follow_up_by).first() if record.follow_up_by else None
        review = db.query(CustomerReview).filter(CustomerReview.order_id == record.order_id).first()

        resp = FollowUpRecordDetail.model_validate(record)
        resp.order_no = order.order_no
        resp.customer_name = customer.full_name if customer else None
        resp.photographer_id = order.photographer_id
        resp.photographer_name = photographer.full_name if photographer else None
        resp.shoot_date = order.shoot_date
        resp.follow_up_by_name = follow_up_user.full_name if follow_up_user else None
        resp.customer_rating = review.rating if review else None
        resp.review_submitted = review is not None
        return resp

    @post("/follow-ups")
    async def create_follow_up(
        self, request: Request, db: Session, data: FollowUpRecordCreate
    ) -> FollowUpRecordResponse:
        user = get_current_user_from_request(request, db)
        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            raise PermissionDeniedException("只有管理员和摄影师可以创建回访记录")

        order = db.query(Order).filter(Order.id == data.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        existing = db.query(FollowUpRecord).filter(FollowUpRecord.order_id == data.order_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="该订单已存在回访记录")

        record_data = data.model_dump()
        record_data["follow_up_by"] = user.id

        record = FollowUpRecord(**record_data)
        db.add(record)
        db.commit()
        db.refresh(record)
        return FollowUpRecordResponse.model_validate(record)

    @put("/follow-ups/{record_id:int}")
    async def update_follow_up(
        self,
        request: Request,
        db: Session,
        record_id: int,
        data: FollowUpRecordUpdate,
    ) -> FollowUpRecordResponse:
        user = get_current_user_from_request(request, db)
        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            raise PermissionDeniedException("权限不足")

        record = db.query(FollowUpRecord).filter(FollowUpRecord.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="回访记录不存在")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(record, key, value)

        if "status" in update_data and update_data["status"] in [FollowUpStatus.IN_PROGRESS, FollowUpStatus.COMPLETED]:
            record.follow_up_by = user.id
            if not record.follow_up_time:
                record.follow_up_time = datetime.utcnow()

        db.commit()
        db.refresh(record)
        return FollowUpRecordResponse.model_validate(record)

    @delete("/follow-ups/{record_id:int}", status_code=200)
    async def delete_follow_up(self, request: Request, db: Session, record_id: int) -> dict:
        user = get_current_user_from_request(request, db)
        if user.role != UserRole.ADMIN:
            raise PermissionDeniedException("只有管理员可以删除回访记录")

        record = db.query(FollowUpRecord).filter(FollowUpRecord.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="回访记录不存在")

        db.delete(record)
        db.commit()
        return {"message": "回访记录已删除"}

    @get("/customer")
    async def list_customer_reviews(
        self,
        request: Request,
        db: Session,
        order_id: Optional[int] = None,
        rating_min: Optional[int] = None,
        rating_max: Optional[int] = None,
        photographer_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CustomerReviewDetail]:
        user = get_current_user_from_request(request, db)
        query = db.query(CustomerReview).join(Order, CustomerReview.order_id == Order.id)

        if user.role == UserRole.CUSTOMER:
            query = query.filter(Order.customer_id == user.id)
        elif user.role == UserRole.PHOTOGRAPHER:
            query = query.filter(
                (Order.photographer_id == user.id) | (Order.photographer_id.is_(None))
            )

        if order_id:
            query = query.filter(CustomerReview.order_id == order_id)
        if rating_min is not None:
            query = query.filter(CustomerReview.rating >= rating_min)
        if rating_max is not None:
            query = query.filter(CustomerReview.rating <= rating_max)
        if photographer_id and user.role in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            query = query.filter(Order.photographer_id == photographer_id)

        reviews = query.order_by(CustomerReview.submitted_at.desc()).offset(skip).limit(limit).all()
        result: List[CustomerReviewDetail] = []
        for r in reviews:
            order = db.query(Order).filter(Order.id == r.order_id).first()
            customer = db.query(User).filter(User.id == order.customer_id).first() if order else None
            photographer = db.query(User).filter(User.id == order.photographer_id).first() if order and order.photographer_id else None

            item = CustomerReviewDetail.model_validate(r)
            item.order_no = order.order_no if order else None
            item.customer_name = "匿名用户" if r.is_anonymous else (customer.full_name if customer else None)
            item.photographer_name = photographer.full_name if photographer else None
            result.append(item)
        return result

    @get("/customer/{review_id:int}")
    async def get_customer_review(
        self, request: Request, db: Session, review_id: int
    ) -> CustomerReviewDetail:
        user = get_current_user_from_request(request, db)
        review = db.query(CustomerReview).filter(CustomerReview.id == review_id).first()
        if not review:
            raise HTTPException(status_code=404, detail="客户评价不存在")

        order = db.query(Order).filter(Order.id == review.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="关联订单不存在")
        self._check_order_permission(order, user)

        customer = db.query(User).filter(User.id == order.customer_id).first()
        photographer = db.query(User).filter(User.id == order.photographer_id).first() if order.photographer_id else None

        resp = CustomerReviewDetail.model_validate(review)
        resp.order_no = order.order_no
        resp.customer_name = "匿名用户" if review.is_anonymous else (customer.full_name if customer else None)
        resp.photographer_name = photographer.full_name if photographer else None
        return resp

    @post("/customer")
    async def create_customer_review(
        self, request: Request, db: Session, data: CustomerReviewCreate
    ) -> CustomerReviewResponse:
        user = get_current_user_from_request(request, db)

        order = db.query(Order).filter(Order.id == data.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        if user.role == UserRole.CUSTOMER and order.customer_id != user.id:
            raise PermissionDeniedException("只能评价自己的订单")

        if order.status != OrderStatus.DELIVERED:
            raise HTTPException(status_code=400, detail="只有已交付的订单才能评价")

        existing = db.query(CustomerReview).filter(CustomerReview.order_id == data.order_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="该订单已评价，无法重复提交")

        follow_up = db.query(FollowUpRecord).filter(FollowUpRecord.order_id == data.order_id).first()
        if follow_up and follow_up.review_deadline:
            if datetime.utcnow() > follow_up.review_deadline:
                raise HTTPException(status_code=400, detail="评价已超过截止时间")

        review_data = data.model_dump()
        review = CustomerReview(**review_data)
        db.add(review)
        db.commit()
        db.refresh(review)
        return CustomerReviewResponse.model_validate(review)

    @put("/customer/{review_id:int}")
    async def update_customer_review(
        self,
        request: Request,
        db: Session,
        review_id: int,
        data: CustomerReviewUpdate,
    ) -> CustomerReviewResponse:
        user = get_current_user_from_request(request, db)
        review = db.query(CustomerReview).filter(CustomerReview.id == review_id).first()
        if not review:
            raise HTTPException(status_code=404, detail="客户评价不存在")

        order = db.query(Order).filter(Order.id == review.order_id).first()
        if user.role == UserRole.CUSTOMER:
            if not order or order.customer_id != user.id:
                raise PermissionDeniedException("权限不足")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(review, key, value)

        db.commit()
        db.refresh(review)
        return CustomerReviewResponse.model_validate(review)

    @get("/dashboard-stats")
    async def get_review_dashboard_stats(
        self, request: Request, db: Session
    ) -> ReviewDashboardStats:
        user = get_current_user_from_request(request, db)
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)

        reviews_query = db.query(CustomerReview).filter(
            CustomerReview.submitted_at >= thirty_days_ago
        )
        follow_ups_query = db.query(FollowUpRecord)

        if user.role == UserRole.PHOTOGRAPHER:
            reviews_query = reviews_query.join(Order).filter(Order.photographer_id == user.id)
            follow_ups_query = follow_ups_query.join(Order).filter(
                (Order.photographer_id == user.id) | (Order.photographer_id.is_(None))
            )
        elif user.role == UserRole.CUSTOMER:
            reviews_query = reviews_query.join(Order).filter(Order.customer_id == user.id)
            follow_ups_query = follow_ups_query.join(Order).filter(Order.customer_id == user.id)

        reviews_30d = reviews_query.all()
        avg_rating = 0.0
        if reviews_30d:
            avg_rating = sum(r.rating for r in reviews_30d) / len(reviews_30d)

        trend_map = {}
        for r in reviews_30d:
            d = r.submitted_at.date()
            if d not in trend_map:
                trend_map[d] = {"total": 0, "count": 0}
            trend_map[d]["total"] += r.rating
            trend_map[d]["count"] += 1

        satisfaction_trend: List[SatisfactionTrendItem] = []
        for i in range(29, -1, -1):
            d = (now - timedelta(days=i)).date()
            if d in trend_map:
                avg = trend_map[d]["total"] / trend_map[d]["count"]
                satisfaction_trend.append(
                    SatisfactionTrendItem(
                        date=d,
                        avg_satisfaction=round(avg, 2),
                        review_count=trend_map[d]["count"],
                    )
                )
            else:
                satisfaction_trend.append(
                    SatisfactionTrendItem(date=d, avg_satisfaction=0.0, review_count=0)
                )

        low_score_query = db.query(CustomerReview).filter(
            CustomerReview.rating <= 3,
            CustomerReview.submitted_at >= thirty_days_ago,
        )
        if user.role == UserRole.PHOTOGRAPHER:
            low_score_query = low_score_query.join(Order).filter(Order.photographer_id == user.id)
        elif user.role == UserRole.CUSTOMER:
            low_score_query = low_score_query.join(Order).filter(Order.customer_id == user.id)
        low_score_reviews = low_score_query.order_by(CustomerReview.rating.asc()).all()

        low_score_orders: List[LowScoreOrder] = []
        for r in low_score_reviews:
            order = db.query(Order).filter(Order.id == r.order_id).first()
            customer = db.query(User).filter(User.id == order.customer_id).first() if order else None
            photographer = db.query(User).filter(User.id == order.photographer_id).first() if order and order.photographer_id else None
            follow_up = db.query(FollowUpRecord).filter(FollowUpRecord.order_id == r.order_id).first()

            low_score_orders.append(
                LowScoreOrder(
                    order_id=r.order_id,
                    order_no=order.order_no if order else None,
                    customer_name="匿名用户" if r.is_anonymous else (customer.full_name if customer else None),
                    photographer_name=photographer.full_name if photographer else None,
                    rating=r.rating,
                    feedback=r.feedback,
                    tags=r.tags,
                    submitted_at=r.submitted_at,
                    follow_up_status=follow_up.status.value if follow_up else None,
                )
            )

        all_follow_ups = follow_ups_query.all()
        total_pending = sum(1 for f in all_follow_ups if f.status == FollowUpStatus.PENDING)
        in_progress = sum(1 for f in all_follow_ups if f.status == FollowUpStatus.IN_PROGRESS)
        pending_7d = 0
        pending_overdue = 0
        completed_last_7d = 0
        for f in all_follow_ups:
            if f.status == FollowUpStatus.PENDING:
                days_since = (now - f.created_at).days
                if days_since <= 7:
                    pending_7d += 1
                else:
                    pending_overdue += 1
            elif f.status == FollowUpStatus.COMPLETED:
                if f.follow_up_time and (now - f.follow_up_time).days <= 7:
                    completed_last_7d += 1

        return ReviewDashboardStats(
            avg_rating_30d=round(avg_rating, 2),
            review_count_30d=len(reviews_30d),
            satisfaction_trend=satisfaction_trend,
            low_score_orders=low_score_orders,
            pending_follow_up=PendingFollowUpStat(
                total_pending=total_pending,
                pending_7d=pending_7d,
                pending_overdue=pending_overdue,
                in_progress=in_progress,
                completed_last_7d=completed_last_7d,
            ),
        )


reviews_router = Router(route_handlers=[ReviewsController], path="/api")
