import uuid
from typing import List, Optional
from datetime import datetime
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
    check_sheet_permission,
    get_or_404,
)
from app.models import (
    User, UserRole, Order, PhotoSheet, RetouchStatus, LockStatus, SelectionRecord,
)
from app.services.user_service import UserService
from app.services.order_service import OrderService, SheetService
from app.services.common import ResponseAssembler
from app.schemas.photo_sheets import (
    PhotoSheetCreate,
    PhotoSheetUpdate,
    PhotoSheetResponse,
    PhotoSheetDetailResponse,
    PhotoSheetListItem,
)


def provide_db() -> Session:
    return next(get_db())


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
        user = get_current_user(request, db)
        check_and_mark_overdue(db)
        query = db.query(PhotoSheet)
        query = SheetService.apply_role_filter(query, user, db)

        if order_id:
            query = query.filter(PhotoSheet.order_id == order_id)
        if retouch_status:
            query = query.filter(PhotoSheet.retouch_status == retouch_status)
        if lock_status:
            query = query.filter(PhotoSheet.lock_status == lock_status)
        if retoucher_id:
            query = query.filter(PhotoSheet.retoucher_id == retoucher_id)

        sheets = query.order_by(PhotoSheet.created_at.desc()).offset(skip).limit(limit).all()
        return ResponseAssembler.build_sheet_list_response(db, sheets, PhotoSheetListItem)

    @get("/{sheet_id:int}")
    async def get_sheet(self, request: Request, db: Session, sheet_id: int) -> PhotoSheetDetailResponse:
        user = get_current_user(request, db)
        check_and_mark_overdue(db)
        sheet = get_or_404(db, PhotoSheet, sheet_id, "片单")
        check_sheet_permission(sheet, user, db)

        order = OrderService.get_by_id(db, sheet.order_id)
        retoucher = UserService.get_by_id(db, sheet.retoucher_id) if sheet.retoucher_id else None
        customer = UserService.get_by_id(db, order.customer_id) if order else None
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
        user = get_current_user(request, db)
        require_roles(user, UserRole.ADMIN, UserRole.PHOTOGRAPHER)

        order = get_or_404(db, Order, data.order_id, "关联订单")

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
        user = get_current_user(request, db)
        sheet = get_or_404(db, PhotoSheet, sheet_id, "片单")
        require_roles(user, UserRole.ADMIN, UserRole.PHOTOGRAPHER)
        self._check_sheet_locked(sheet)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(sheet, key, value)

        db.commit()
        db.refresh(sheet)
        return PhotoSheetResponse.model_validate(sheet)

    @post("/{sheet_id:int}/lock")
    async def lock_sheet(self, request: Request, db: Session, sheet_id: int) -> PhotoSheetResponse:
        user = get_current_user(request, db)
        require_roles(user, UserRole.ADMIN, UserRole.PHOTOGRAPHER)

        sheet = get_or_404(db, PhotoSheet, sheet_id, "片单")
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

        order = OrderService.get_by_id(db, sheet.order_id)
        if order:
            all_sheets = db.query(PhotoSheet).filter(PhotoSheet.order_id == order.id).all()
            if all(s.lock_status == LockStatus.LOCKED for s in all_sheets):
                from app.models import OrderStatus
                order.status = OrderStatus.LOCKED

        db.commit()
        db.refresh(sheet)
        return PhotoSheetResponse.model_validate(sheet)

    @delete("/{sheet_id:int}", status_code=200)
    async def delete_sheet(self, request: Request, db: Session, sheet_id: int) -> dict:
        user = get_current_user(request, db)
        require_admin(user)
        sheet = get_or_404(db, PhotoSheet, sheet_id, "片单")
        self._check_sheet_locked(sheet)
        db.delete(sheet)
        db.commit()
        return {"message": "片单已删除"}


photo_sheets_router = Router(route_handlers=[PhotoSheetsController], path="/api")
