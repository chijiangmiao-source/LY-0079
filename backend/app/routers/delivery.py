from typing import List, Optional
from datetime import datetime
from litestar import Router, get, post, put, delete, Request
from litestar.controller import Controller
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotAuthorizedException, PermissionDeniedException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models import User, UserRole, Order, PhotoSheet, LockStatus, DeliveryVersion
from app.schemas.delivery import (
    DeliveryVersionCreate,
    DeliveryVersionUpdate,
    DeliveryVersionResponse,
    DeliveryVersionListItem,
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


class DeliveryController(Controller):
    path = "/delivery"
    dependencies = {"db": Provide(provide_db)}

    @get("/")
    async def list_versions(
        self,
        request: Request,
        db: Session,
        order_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DeliveryVersionListItem]:
        user = get_current_user_from_request(request, db)
        query = db.query(DeliveryVersion)

        if user.role == UserRole.CUSTOMER:
            customer_orders = db.query(Order).filter(Order.customer_id == user.id).all()
            customer_order_ids = [o.id for o in customer_orders]
            query = query.filter(DeliveryVersion.order_id.in_(customer_order_ids))

        if order_id:
            query = query.filter(DeliveryVersion.order_id == order_id)

        versions = query.order_by(DeliveryVersion.created_at.desc()).offset(skip).limit(limit).all()
        result = []
        for v in versions:
            order = db.query(Order).filter(Order.id == v.order_id).first()
            item = DeliveryVersionListItem.model_validate(v)
            item.order_no = order.order_no if order else None
            result.append(item)
        return result

    @get("/{version_id:int}")
    async def get_version(self, request: Request, db: Session, version_id: int) -> DeliveryVersionResponse:
        user = get_current_user_from_request(request, db)
        version = db.query(DeliveryVersion).filter(DeliveryVersion.id == version_id).first()
        if not version:
            raise HTTPException(status_code=404, detail="交付版本不存在")

        if user.role == UserRole.CUSTOMER:
            order = db.query(Order).filter(Order.id == version.order_id).first()
            if not order or order.customer_id != user.id:
                raise PermissionDeniedException("权限不足")

        return DeliveryVersionResponse.model_validate(version)

    @post("/")
    async def create_version(self, request: Request, db: Session, data: DeliveryVersionCreate) -> DeliveryVersionResponse:
        user = get_current_user_from_request(request, db)
        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            raise PermissionDeniedException("权限不足")

        order = db.query(Order).filter(Order.id == data.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        all_sheets = db.query(PhotoSheet).filter(PhotoSheet.order_id == order.id).all()
        if all_sheets and not all(s.lock_status == LockStatus.LOCKED for s in all_sheets):
            raise HTTPException(status_code=400, detail="订单存在未锁定的片单，无法交付")

        existing_count = (
            db.query(DeliveryVersion).filter(DeliveryVersion.order_id == data.order_id).count()
        )
        next_version = existing_count + 1

        version_data = data.model_dump()
        if not version_data.get("delivered_by"):
            version_data["delivered_by"] = user.id

        version = DeliveryVersion(
            **version_data,
            version=next_version,
            delivery_date=datetime.utcnow(),
        )
        db.add(version)

        order.status = "delivered"
        db.commit()
        db.refresh(version)
        return DeliveryVersionResponse.model_validate(version)

    @put("/{version_id:int}")
    async def update_version(
        self,
        request: Request,
        db: Session,
        version_id: int,
        data: DeliveryVersionUpdate,
    ) -> DeliveryVersionResponse:
        user = get_current_user_from_request(request, db)
        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            raise PermissionDeniedException("权限不足")

        version = db.query(DeliveryVersion).filter(DeliveryVersion.id == version_id).first()
        if not version:
            raise HTTPException(status_code=404, detail="交付版本不存在")

        if version.is_protected:
            raise HTTPException(status_code=400, detail="该版本为受保护版本，不可修改")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(version, key, value)

        db.commit()
        db.refresh(version)
        return DeliveryVersionResponse.model_validate(version)

    @delete("/{version_id:int}")
    async def delete_version(self, request: Request, db: Session, version_id: int) -> dict:
        user = get_current_user_from_request(request, db)
        if user.role != UserRole.ADMIN:
            raise PermissionDeniedException("只有管理员可以删除交付版本")

        version = db.query(DeliveryVersion).filter(DeliveryVersion.id == version_id).first()
        if not version:
            raise HTTPException(status_code=404, detail="交付版本不存在")

        if version.is_protected:
            raise HTTPException(status_code=400, detail="该版本为受保护版本，不可删除")

        db.delete(version)
        db.commit()
        return {"message": "交付版本已删除"}


delivery_router = Router(route_handlers=[DeliveryController], path="/api")
