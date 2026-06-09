import uuid
from typing import List, Optional
from datetime import datetime
from litestar import Router, get, post, put, delete, Request
from litestar.controller import Controller
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotAuthorizedException, PermissionDeniedException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models import User, UserRole, Order, OrderStatus, PhotoSheet
from app.schemas.orders import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderDetailResponse,
    OrderListItem,
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


def generate_order_no() -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"ORD{timestamp}{uuid.uuid4().hex[:6].upper()}"


class OrdersController(Controller):
    path = "/orders"
    dependencies = {"db": Provide(provide_db)}

    def _check_permission(self, order: Order, user: User) -> None:
        if user.role in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            return
        if user.role == UserRole.CUSTOMER and order.customer_id == user.id:
            return
        if user.role == UserRole.RETOUCHER:
            return
        raise PermissionDeniedException("权限不足")

    @get("/")
    async def list_orders(
        self,
        request: Request,
        db: Session,
        status: Optional[OrderStatus] = None,
        customer_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[OrderListItem]:
        user = get_current_user_from_request(request, db)
        query = db.query(Order)

        if user.role == UserRole.CUSTOMER:
            query = query.filter(Order.customer_id == user.id)
        elif user.role == UserRole.PHOTOGRAPHER:
            query = query.filter(
                (Order.photographer_id == user.id) | (Order.photographer_id.is_(None))
            )
        if status:
            query = query.filter(Order.status == status)
        if customer_id and user.role in [UserRole.ADMIN]:
            query = query.filter(Order.customer_id == customer_id)

        orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
        result = []
        for o in orders:
            customer = db.query(User).filter(User.id == o.customer_id).first()
            item = OrderListItem.model_validate(o)
            item.customer_name = customer.full_name if customer else None
            result.append(item)
        return result

    @get("/{order_id:int}")
    async def get_order(self, request: Request, db: Session, order_id: int) -> OrderDetailResponse:
        user = get_current_user_from_request(request, db)
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        self._check_permission(order, user)

        customer = db.query(User).filter(User.id == order.customer_id).first()
        photographer = db.query(User).filter(User.id == order.photographer_id).first() if order.photographer_id else None
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
        user = get_current_user_from_request(request, db)
        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            raise PermissionDeniedException("只有管理员和摄影师可以创建订单")

        if user.role == UserRole.PHOTOGRAPHER and not data.photographer_id:
            data.photographer_id = user.id

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
        user = get_current_user_from_request(request, db)
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            raise PermissionDeniedException("权限不足")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(order, key, value)

        db.commit()
        db.refresh(order)
        return OrderResponse.model_validate(order)

    @delete("/{order_id:int}")
    async def delete_order(self, request: Request, db: Session, order_id: int) -> dict:
        user = get_current_user_from_request(request, db)
        if user.role != UserRole.ADMIN:
            raise PermissionDeniedException("只有管理员可以删除订单")
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        db.delete(order)
        db.commit()
        return {"message": "订单已删除"}


orders_router = Router(route_handlers=[OrdersController], path="/api")
