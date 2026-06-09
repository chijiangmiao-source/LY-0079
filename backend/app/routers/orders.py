import uuid
from typing import List, Optional
from datetime import datetime, date
from litestar import Router, get, post, put, delete, Request
from litestar.controller import Controller
from litestar.di import Provide
from litestar.exceptions import HTTPException, PermissionDeniedException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import (
    get_current_user,
    require_roles,
    require_admin,
    check_order_permission,
    get_or_404,
)
from app.models import User, UserRole, Order, OrderStatus, PhotoSheet
from app.services.user_service import UserService
from app.services.order_service import OrderService
from app.services.common import ResponseAssembler
from app.schemas.orders import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderDetailResponse,
    OrderListItem,
    ScheduleConflict,
    ScheduleConflictOrder,
)


def provide_db() -> Session:
    return next(get_db())


def generate_order_no() -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"ORD{timestamp}{uuid.uuid4().hex[:6].upper()}"


class OrdersController(Controller):
    path = "/orders"
    dependencies = {"db": Provide(provide_db)}

    @get("/")
    async def list_orders(
        self,
        request: Request,
        db: Session,
        status: Optional[OrderStatus] = None,
        customer_id: Optional[int] = None,
        photographer_id: Optional[int] = None,
        shoot_date_from: Optional[date] = None,
        shoot_date_to: Optional[date] = None,
        city: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[OrderListItem]:
        user = get_current_user(request, db)
        query = db.query(Order)
        query = OrderService.apply_role_filter(query, user)

        if status:
            query = query.filter(Order.status == status)
        if customer_id and user.role in [UserRole.ADMIN]:
            query = query.filter(Order.customer_id == customer_id)
        if photographer_id:
            if user.role in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
                query = query.filter(Order.photographer_id == photographer_id)
        if shoot_date_from:
            query = query.filter(Order.shoot_date >= shoot_date_from)
        if shoot_date_to:
            query = query.filter(Order.shoot_date <= shoot_date_to)
        if city:
            query = query.filter(Order.city == city)

        orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
        return ResponseAssembler.build_order_list_response(db, orders, OrderListItem)

    @get("/check-schedule")
    async def check_schedule(
        self,
        request: Request,
        db: Session,
        photographer_id: int,
        shoot_time_start: datetime,
        shoot_time_end: datetime,
        order_id: Optional[int] = None,
    ) -> ScheduleConflict:
        user = get_current_user(request, db)
        require_roles(user, UserRole.ADMIN, UserRole.PHOTOGRAPHER)

        conflicts = OrderService.check_schedule_conflict(
            db, photographer_id, shoot_time_start, shoot_time_end, order_id
        )

        conflicting_orders: List[ScheduleConflictOrder] = []
        for o in conflicts:
            customer = UserService.get_by_id(db, o.customer_id)
            conflicting_orders.append(
                ScheduleConflictOrder(
                    order_id=o.id,
                    order_no=o.order_no,
                    customer_name=customer.full_name if customer else None,
                    shoot_time_start=o.shoot_time_start,
                    shoot_time_end=o.shoot_time_end,
                    city=o.city,
                )
            )

        return ScheduleConflict(
            has_conflict=len(conflicting_orders) > 0,
            conflicting_orders=conflicting_orders,
        )

    @get("/{order_id:int}")
    async def get_order(self, request: Request, db: Session, order_id: int) -> OrderDetailResponse:
        user = get_current_user(request, db)
        order = get_or_404(db, Order, order_id, "订单")
        check_order_permission(order, user)

        customer = UserService.get_by_id(db, order.customer_id)
        photographer = UserService.get_by_id(db, order.photographer_id) if order.photographer_id else None
        sheet_count = db.query(PhotoSheet).filter(PhotoSheet.order_id == order.id).count()
        photo_count = sum(s.total_photos for s in db.query(PhotoSheet).filter(PhotoSheet.order_id == order.id).all())

        resp = OrderDetailResponse.model_validate(order)
        resp.customer_name = customer.full_name if customer else None
        resp.photographer_name = photographer.full_name if photographer else None
        resp.sheet_count = sheet_count
        resp.photo_count = photo_count
        return resp

    @post("/")
    async def create_order(self, request: Request, db: Session, data: OrderCreate) -> OrderResponse:
        user = get_current_user(request, db)
        require_roles(user, UserRole.ADMIN, UserRole.PHOTOGRAPHER)

        if user.role == UserRole.PHOTOGRAPHER and not data.photographer_id:
            data.photographer_id = user.id

        if data.photographer_id and data.shoot_time_start and data.shoot_time_end:
            conflicts = OrderService.check_schedule_conflict(
                db, data.photographer_id, data.shoot_time_start, data.shoot_time_end
            )
            if conflicts:
                raise HTTPException(
                    status_code=400,
                    detail=f"摄影师档期冲突：{OrderService.format_conflict_info(db, conflicts)}",
                )

        order = Order(
            order_no=generate_order_no(),
            **data.model_dump(),
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return OrderResponse.model_validate(order)

    @put("/{order_id:int}")
    async def update_order(
        self,
        request: Request,
        db: Session,
        order_id: int,
        data: OrderUpdate,
    ) -> OrderResponse:
        user = get_current_user(request, db)
        order = get_or_404(db, Order, order_id, "订单")
        require_roles(user, UserRole.ADMIN, UserRole.PHOTOGRAPHER)

        update_data = data.model_dump(exclude_unset=True)

        photographer_id = update_data.get("photographer_id", order.photographer_id)
        shoot_time_start = update_data.get("shoot_time_start", order.shoot_time_start)
        shoot_time_end = update_data.get("shoot_time_end", order.shoot_time_end)

        if photographer_id and shoot_time_start and shoot_time_end:
            conflicts = OrderService.check_schedule_conflict(
                db, photographer_id, shoot_time_start, shoot_time_end, order_id
            )
            if conflicts:
                raise HTTPException(
                    status_code=400,
                    detail=f"摄影师档期冲突：{OrderService.format_conflict_info(db, conflicts)}",
                )

        for key, value in update_data.items():
            setattr(order, key, value)

        db.commit()
        db.refresh(order)
        return OrderResponse.model_validate(order)

    @delete("/{order_id:int}", status_code=200)
    async def delete_order(self, request: Request, db: Session, order_id: int) -> dict:
        user = get_current_user(request, db)
        require_admin(user)
        order = get_or_404(db, Order, order_id, "订单")
        db.delete(order)
        db.commit()
        return {"message": "订单已删除"}


orders_router = Router(route_handlers=[OrdersController], path="/api")
