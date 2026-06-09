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
from app.models import User, UserRole, Order, PhotoSheet, PhotoBatch, LockStatus
from app.schemas.batches import (
    PhotoBatchCreate,
    PhotoBatchUpdate,
    PhotoBatchResponse,
    PhotoBatchListItem,
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


def generate_batch_no() -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"BAT{timestamp}{uuid.uuid4().hex[:6].upper()}"


class BatchesController(Controller):
    path = "/batches"
    dependencies = {"db": Provide(provide_db)}

    @get("/")
    async def list_batches(
        self,
        request: Request,
        db: Session,
        order_id: Optional[int] = None,
        sheet_id: Optional[int] = None,
        batch_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PhotoBatchListItem]:
        user = get_current_user_from_request(request, db)
        query = db.query(PhotoBatch)

        if user.role == UserRole.CUSTOMER:
            customer_orders = db.query(Order).filter(Order.customer_id == user.id).all()
            customer_order_ids = [o.id for o in customer_orders]
            query = query.filter(PhotoBatch.order_id.in_(customer_order_ids))

        if order_id:
            query = query.filter(PhotoBatch.order_id == order_id)
        if sheet_id:
            query = query.filter(PhotoBatch.sheet_id == sheet_id)
        if batch_type:
            query = query.filter(PhotoBatch.batch_type == batch_type)

        batches = query.order_by(PhotoBatch.created_at.desc()).offset(skip).limit(limit).all()
        return [PhotoBatchListItem.model_validate(b) for b in batches]

    @get("/{batch_id:int}")
    async def get_batch(self, request: Request, db: Session, batch_id: int) -> PhotoBatchResponse:
        user = get_current_user_from_request(request, db)
        batch = db.query(PhotoBatch).filter(PhotoBatch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="批次不存在")

        if user.role == UserRole.CUSTOMER:
            order = db.query(Order).filter(Order.id == batch.order_id).first()
            if not order or order.customer_id != user.id:
                raise PermissionDeniedException("权限不足")

        return PhotoBatchResponse.model_validate(batch)

    @post("/")
    async def create_batch(self, request: Request, db: Session, data: PhotoBatchCreate) -> PhotoBatchResponse:
        user = get_current_user_from_request(request, db)
        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER, UserRole.RETOUCHER]:
            raise PermissionDeniedException("权限不足")

        order = db.query(Order).filter(Order.id == data.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="关联订单不存在")

        if data.sheet_id:
            sheet = db.query(PhotoSheet).filter(PhotoSheet.id == data.sheet_id).first()
            if not sheet:
                raise HTTPException(status_code=404, detail="关联片单不存在")
            if sheet.lock_status == LockStatus.LOCKED:
                raise HTTPException(status_code=400, detail="片单已锁定，无法添加批次")

        batch_data = data.model_dump()
        if not batch_data.get("uploaded_by"):
            batch_data["uploaded_by"] = user.id

        batch = PhotoBatch(
            batch_no=generate_batch_no(),
            **batch_data,
        )
        db.add(batch)

        if data.sheet_id:
            sheet = db.query(PhotoSheet).filter(PhotoSheet.id == data.sheet_id).first()
            if sheet:
                sheet.total_photos += data.photo_count

        db.commit()
        db.refresh(batch)
        return PhotoBatchResponse.model_validate(batch)

    @put("/{batch_id:int}")
    async def update_batch(
        self,
        request: Request,
        db: Session,
        batch_id: int,
        data: PhotoBatchUpdate,
    ) -> PhotoBatchResponse:
        user = get_current_user_from_request(request, db)
        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER, UserRole.RETOUCHER]:
            raise PermissionDeniedException("权限不足")

        batch = db.query(PhotoBatch).filter(PhotoBatch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="批次不存在")

        if batch.sheet_id:
            sheet = db.query(PhotoSheet).filter(PhotoSheet.id == batch.sheet_id).first()
            if sheet and sheet.lock_status == LockStatus.LOCKED:
                raise HTTPException(status_code=400, detail="片单已锁定，无法修改批次")

        update_data = data.model_dump(exclude_unset=True)
        if "photo_count" in update_data and batch.sheet_id:
            sheet = db.query(PhotoSheet).filter(PhotoSheet.id == batch.sheet_id).first()
            if sheet:
                sheet.total_photos += (update_data["photo_count"] - batch.photo_count)

        for key, value in update_data.items():
            setattr(batch, key, value)

        db.commit()
        db.refresh(batch)
        return PhotoBatchResponse.model_validate(batch)

    @delete("/{batch_id:int}", status_code=200)
    async def delete_batch(self, request: Request, db: Session, batch_id: int) -> dict:
        user = get_current_user_from_request(request, db)
        if user.role != UserRole.ADMIN:
            raise PermissionDeniedException("只有管理员可以删除批次")

        batch = db.query(PhotoBatch).filter(PhotoBatch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="批次不存在")

        if batch.sheet_id:
            sheet = db.query(PhotoSheet).filter(PhotoSheet.id == batch.sheet_id).first()
            if sheet and sheet.lock_status == LockStatus.LOCKED:
                raise HTTPException(status_code=400, detail="片单已锁定，无法删除批次")
            if sheet:
                sheet.total_photos = max(0, sheet.total_photos - batch.photo_count)

        db.delete(batch)
        db.commit()
        return {"message": "批次已删除"}


batches_router = Router(route_handlers=[BatchesController], path="/api")
