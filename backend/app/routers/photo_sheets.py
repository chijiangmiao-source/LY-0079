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
from app.models import User, UserRole, Order, PhotoSheet, RetouchStatus, LockStatus, SelectionRecord
from app.schemas.photo_sheets import (
    PhotoSheetCreate,
    PhotoSheetUpdate,
    PhotoSheetResponse,
    PhotoSheetDetailResponse,
    PhotoSheetListItem,
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


def generate_sheet_no() -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"SHT{timestamp}{uuid.uuid4().hex[:6].upper()}"


def check_and_mark_overdue(db: Session) -> None:
    now = datetime.utcnow()
    overdue_sheets = (
        db.query(PhotoSheet)
        .filter(
            PhotoSheet.lock_status == LockStatus.UNLOCKED,
            PhotoSheet.selection_deadline.isnot(None),
            PhotoSheet.selection_deadline < now,
        )
        .all()
    )
    for sheet in overdue_sheets:
        has_confirmed = (
            db.query(SelectionRecord)
            .filter(
                SelectionRecord.sheet_id == sheet.id,
                SelectionRecord.final_confirm_time.isnot(None),
            )
            .first()
        )
        if not has_confirmed:
            sheet.lock_status = LockStatus.FOLLOW_UP
    db.commit()


class PhotoSheetsController(Controller):
    path = "/photo-sheets"
    dependencies = {"db": Provide(provide_db)}

    def _check_sheet_locked(self, sheet: PhotoSheet) -> None:
        if sheet.lock_status == LockStatus.LOCKED:
            raise HTTPException(status_code=400, detail="片单已锁定，无法修改")

    def _check_permission(self, sheet: PhotoSheet, user: User, db: Session) -> None:
        if user.role in [UserRole.ADMIN, UserRole.PHOTOGRAPHER, UserRole.RETOUCHER]:
            return
        if user.role == UserRole.CUSTOMER:
            order = db.query(Order).filter(Order.id == sheet.order_id).first()
            if order and order.customer_id == user.id:
                return
        raise PermissionDeniedException("权限不足")

    @get("/")
    async def list_sheets(
        self,
        request: Request,
        db: Session,
        order_id: Optional[int] = None,
        retouch_status: Optional[RetouchStatus] = None,
        lock_status: Optional[LockStatus] = None,
        retoucher_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PhotoSheetListItem]:
        user = get_current_user_from_request(request, db)
        check_and_mark_overdue(db)
        query = db.query(PhotoSheet)

        if user.role == UserRole.CUSTOMER:
            customer_orders = db.query(Order).filter(Order.customer_id == user.id).all()
            customer_order_ids = [o.id for o in customer_orders]
            query = query.filter(PhotoSheet.order_id.in_(customer_order_ids))
        elif user.role == UserRole.RETOUCHER:
            query = query.filter(
                (PhotoSheet.retoucher_id == user.id) | (PhotoSheet.retoucher_id.is_(None))
            )

        if order_id:
            query = query.filter(PhotoSheet.order_id == order_id)
        if retouch_status:
            query = query.filter(PhotoSheet.retouch_status == retouch_status)
        if lock_status:
            query = query.filter(PhotoSheet.lock_status == lock_status)
        if retoucher_id:
            query = query.filter(PhotoSheet.retoucher_id == retoucher_id)

        sheets = query.order_by(PhotoSheet.created_at.desc()).offset(skip).limit(limit).all()
        result = []
        for s in sheets:
            order = db.query(Order).filter(Order.id == s.order_id).first()
            retoucher = db.query(User).filter(User.id == s.retoucher_id).first() if s.retoucher_id else None
            item = PhotoSheetListItem.model_validate(s)
            item.order_no = order.order_no if order else None
            item.retoucher_name = retoucher.full_name if retoucher else None
            result.append(item)
        return result

    @get("/{sheet_id:int}")
    async def get_sheet(self, request: Request, db: Session, sheet_id: int) -> PhotoSheetDetailResponse:
        user = get_current_user_from_request(request, db)
        check_and_mark_overdue(db)
        sheet = db.query(PhotoSheet).filter(PhotoSheet.id == sheet_id).first()
        if not sheet:
            raise HTTPException(status_code=404, detail="片单不存在")
        self._check_permission(sheet, user, db)

        order = db.query(Order).filter(Order.id == sheet.order_id).first()
        retoucher = db.query(User).filter(User.id == sheet.retoucher_id).first() if sheet.retoucher_id else None
        customer = db.query(User).filter(User.id == order.customer_id).first() if order else None
        selection_count = db.query(SelectionRecord).filter(SelectionRecord.sheet_id == sheet.id).count()
        is_overdue = (
            sheet.selection_deadline is not None
            and sheet.selection_deadline < datetime.utcnow()
            and sheet.lock_status != LockStatus.LOCKED
        )

        resp = PhotoSheetDetailResponse.model_validate(sheet)
        resp.order_no = order.order_no if order else None
        resp.retoucher_name = retoucher.full_name if retoucher else None
        resp.customer_name = customer.full_name if customer else None
        resp.selection_count = selection_count
        resp.is_overdue = is_overdue
        return resp

    @post("/")
    async def create_sheet(self, request: Request, db: Session, data: PhotoSheetCreate) -> PhotoSheetResponse:
        user = get_current_user_from_request(request, db)
        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            raise PermissionDeniedException("只有管理员和摄影师可以创建片单")

        order = db.query(Order).filter(Order.id == data.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="关联订单不存在")

        sheet = PhotoSheet(
            sheet_no=generate_sheet_no(),
            **data.model_dump(),
        )
        db.add(sheet)
        db.commit()
        db.refresh(sheet)
        return PhotoSheetResponse.model_validate(sheet)

    @put("/{sheet_id:int}")
    async def update_sheet(
        self,
        request: Request,
        db: Session,
        sheet_id: int,
        data: PhotoSheetUpdate,
    ) -> PhotoSheetResponse:
        user = get_current_user_from_request(request, db)
        sheet = db.query(PhotoSheet).filter(PhotoSheet.id == sheet_id).first()
        if not sheet:
            raise HTTPException(status_code=404, detail="片单不存在")
        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            raise PermissionDeniedException("权限不足")
        self._check_sheet_locked(sheet)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(sheet, key, value)

        db.commit()
        db.refresh(sheet)
        return PhotoSheetResponse.model_validate(sheet)

    @post("/{sheet_id:int}/lock")
    async def lock_sheet(self, request: Request, db: Session, sheet_id: int) -> PhotoSheetResponse:
        user = get_current_user_from_request(request, db)
        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            raise PermissionDeniedException("只有管理员和摄影师可以锁定片单")

        sheet = db.query(PhotoSheet).filter(PhotoSheet.id == sheet_id).first()
        if not sheet:
            raise HTTPException(status_code=404, detail="片单不存在")
        if sheet.lock_status == LockStatus.LOCKED:
            raise HTTPException(status_code=400, detail="片单已锁定")

        has_confirmed = (
            db.query(SelectionRecord)
            .filter(
                SelectionRecord.sheet_id == sheet.id,
                SelectionRecord.final_confirm_time.isnot(None),
            )
            .first()
        )
        if not has_confirmed:
            raise HTTPException(status_code=400, detail="片单尚无最终确认的选片记录，无法锁定")

        sheet.lock_status = LockStatus.LOCKED
        sheet.locked_at = datetime.utcnow()
        sheet.locked_by = user.id

        order = db.query(Order).filter(Order.id == sheet.order_id).first()
        if order:
            all_sheets = db.query(PhotoSheet).filter(PhotoSheet.order_id == order.id).all()
            if all(s.lock_status == LockStatus.LOCKED for s in all_sheets):
                from app.models import OrderStatus
                order.status = OrderStatus.LOCKED

        db.commit()
        db.refresh(sheet)
        return PhotoSheetResponse.model_validate(sheet)

    @delete("/{sheet_id:int}")
    async def delete_sheet(self, request: Request, db: Session, sheet_id: int) -> dict:
        user = get_current_user_from_request(request, db)
        if user.role != UserRole.ADMIN:
            raise PermissionDeniedException("只有管理员可以删除片单")
        sheet = db.query(PhotoSheet).filter(PhotoSheet.id == sheet_id).first()
        if not sheet:
            raise HTTPException(status_code=404, detail="片单不存在")
        self._check_sheet_locked(sheet)
        db.delete(sheet)
        db.commit()
        return {"message": "片单已删除"}


photo_sheets_router = Router(route_handlers=[PhotoSheetsController], path="/api")
