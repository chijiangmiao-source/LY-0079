from typing import List, Optional
from datetime import datetime, timedelta
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
    get_or_404,
    get_customer_order_ids,
)
from app.models import (
    User, UserRole, Order, PhotoSheet, LockStatus, DeliveryVersion, FollowUpRecord, FollowUpStatus, OrderStatus,
)
from app.services.order_service import OrderService
from app.schemas.delivery import (
    DeliveryVersionCreate,
    DeliveryVersionUpdate,
    DeliveryVersionResponse,
    DeliveryVersionListItem,
)


def provide_db() -> Session:
    return next(get_db())


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
        user = get_current_user(request, db)
        query = db.query(DeliveryVersion)

        if user.role == UserRole.CUSTOMER:
            customer_order_ids = get_customer_order_ids(db, user.id)
            query = query.filter(DeliveryVersion.order_id.in_(customer_order_ids))

        if order_id:
            query = query.filter(DeliveryVersion.order_id == order_id)

        versions = query.order_by(DeliveryVersion.created_at.desc()).offset(skip).limit(limit).all()
        result = []
        for v in versions:
            order = OrderService.get_by_id(db, v.order_id)
            item = DeliveryVersionListItem.model_validate(v)
            item.order_no = order.order_no if order else None
            result.append(item)
        return result

    @get("/{version_id:int}")
    async def get_version(self, request: Request, db: Session, version_id: int) -> DeliveryVersionResponse:
        user = get_current_user(request, db)
        version = get_or_404(db, DeliveryVersion, version_id, "交付版本")

        if user.role == UserRole.CUSTOMER:
            order = OrderService.get_by_id(db, version.order_id)
            if not order or order.customer_id != user.id:
                raise PermissionDeniedException("权限不足")

        return DeliveryVersionResponse.model_validate(version)

    @post("/")
    async def create_version(self, request: Request, db: Session, data: DeliveryVersionCreate) -> DeliveryVersionResponse:
        user = get_current_user(request, db)
        require_roles(user, UserRole.ADMIN, UserRole.PHOTOGRAPHER)

        order = get_or_404(db, Order, data.order_id, "订单")

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

        order.status = OrderStatus.DELIVERED

        existing_follow_up = db.query(FollowUpRecord).filter(FollowUpRecord.order_id == order.id).first()
        if not existing_follow_up:
            follow_up = FollowUpRecord(
                order_id=order.id,
                status=FollowUpStatus.PENDING,
                review_deadline=datetime.utcnow() + timedelta(days=7),
            )
            db.add(follow_up)

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
        user = get_current_user(request, db)
        require_roles(user, UserRole.ADMIN, UserRole.PHOTOGRAPHER)

        version = get_or_404(db, DeliveryVersion, version_id, "交付版本")

        if version.is_protected:
            raise HTTPException(status_code=400, detail="该版本为受保护版本，不可修改")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(version, key, value)

        db.commit()
        db.refresh(version)
        return DeliveryVersionResponse.model_validate(version)

    @delete("/{version_id:int}", status_code=200)
    async def delete_version(self, request: Request, db: Session, version_id: int) -> dict:
        user = get_current_user(request, db)
        require_admin(user)

        version = get_or_404(db, DeliveryVersion, version_id, "交付版本")

        if version.is_protected:
            raise HTTPException(status_code=400, detail="该版本为受保护版本，不可删除")

        db.delete(version)
        db.commit()
        return {"message": "交付版本已删除"}


delivery_router = Router(route_handlers=[DeliveryController], path="/api")
