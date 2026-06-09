from typing import List, Optional
from datetime import datetime
from litestar import Router, get, post, put, Request
from litestar.controller import Controller
from litestar.di import Provide
from litestar.exceptions import HTTPException, PermissionDeniedException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import (
    get_current_user,
    require_roles,
    check_customer_sheet_access,
    get_or_404,
    get_customer_sheet_ids,
)
from app.models import (
    User, UserRole, Order, PhotoSheet, LockStatus,
    SelectionRecord,
)
from app.services.order_service import SheetService
from app.schemas.selections import (
    SelectionCreate,
    SelectionUpdate,
    SelectionResponse,
    SelectionConfirmRequest,
    SelectionListItem,
)


def provide_db() -> Session:
    return next(get_db())


class SelectionsController(Controller):
    path = "/selections"
    dependencies = {"db": Provide(provide_db)}

    def _check_sheet_locked(self, sheet: PhotoSheet) -> None:
        if sheet.lock_status == LockStatus.LOCKED:
            raise HTTPException(status_code=400, detail="片单已锁定，无法修改选片")

    @get("/")
    async def list_selections(
        self,
        request: Request,
        db: Session,
        sheet_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SelectionListItem]:
        user = get_current_user(request, db)
        query = db.query(SelectionRecord)

        if user.role == UserRole.CUSTOMER:
            customer_sheet_ids = get_customer_sheet_ids(db, user.id)
            query = query.filter(SelectionRecord.sheet_id.in_(customer_sheet_ids))

        if sheet_id:
            query = query.filter(SelectionRecord.sheet_id == sheet_id)

        selections = query.order_by(SelectionRecord.created_at.desc()).offset(skip).limit(limit).all()
        result = []
        for sel in selections:
            sheet = SheetService.get_by_id(db, sel.sheet_id)
            item = SelectionListItem.model_validate(sel)
            item.sheet_no = sheet.sheet_no if sheet else None
            result.append(item)
        return result

    @get("/{selection_id:int}")
    async def get_selection(self, request: Request, db: Session, selection_id: int) -> SelectionResponse:
        user = get_current_user(request, db)
        selection = get_or_404(db, SelectionRecord, selection_id, "选片记录")

        if user.role == UserRole.CUSTOMER:
            sheet = SheetService.get_by_id(db, selection.sheet_id)
            check_customer_sheet_access(sheet, user, db) if sheet else None

        return SelectionResponse.model_validate(selection)

    @post("/")
    async def create_selection(self, request: Request, db: Session, data: SelectionCreate) -> SelectionResponse:
        user = get_current_user(request, db)

        sheet = get_or_404(db, PhotoSheet, data.sheet_id, "片单")

        if user.role == UserRole.CUSTOMER:
            check_customer_sheet_access(sheet, user, db)
        elif user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            raise PermissionDeniedException("权限不足")

        self._check_sheet_locked(sheet)

        if sheet.selectable_count > 0 and data.selected_count > sheet.selectable_count:
            raise HTTPException(
                status_code=400,
                detail=f"入选数量({data.selected_count})不能超过可选总数({sheet.selectable_count})",
            )

        selection = SelectionRecord(
            **data.model_dump(),
            selection_time=datetime.utcnow(),
        )
        db.add(selection)
        db.commit()
        db.refresh(selection)
        return SelectionResponse.model_validate(selection)

    @put("/{selection_id:int}")
    async def update_selection(
        self,
        request: Request,
        db: Session,
        selection_id: int,
        data: SelectionUpdate,
    ) -> SelectionResponse:
        user = get_current_user(request, db)
        selection = get_or_404(db, SelectionRecord, selection_id, "选片记录")

        if selection.final_confirm_time:
            raise HTTPException(status_code=400, detail="选片已最终确认，无法修改")

        sheet = get_or_404(db, PhotoSheet, selection.sheet_id, "关联片单")
        self._check_sheet_locked(sheet)

        if user.role == UserRole.CUSTOMER:
            check_customer_sheet_access(sheet, user, db)
        elif user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            raise PermissionDeniedException("权限不足")

        update_data = data.model_dump(exclude_unset=True)
        if "selected_count" in update_data and sheet.selectable_count > 0:
            if update_data["selected_count"] > sheet.selectable_count:
                raise HTTPException(
                    status_code=400,
                    detail=f"入选数量({update_data['selected_count']})不能超过可选总数({sheet.selectable_count})",
                )

        for key, value in update_data.items():
            setattr(selection, key, value)

        db.commit()
        db.refresh(selection)
        return SelectionResponse.model_validate(selection)

    @post("/{selection_id:int}/confirm")
    async def confirm_selection(
        self,
        request: Request,
        db: Session,
        selection_id: int,
        data: SelectionConfirmRequest,
    ) -> SelectionResponse:
        user = get_current_user(request, db)
        selection = get_or_404(db, SelectionRecord, selection_id, "选片记录")

        sheet = get_or_404(db, PhotoSheet, selection.sheet_id, "关联片单")
        self._check_sheet_locked(sheet)

        if user.role == UserRole.CUSTOMER:
            check_customer_sheet_access(sheet, user, db)
        elif user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            raise PermissionDeniedException("权限不足")

        confirm_time = data.final_confirm_time or datetime.utcnow()
        if confirm_time < selection.selection_time:
            raise HTTPException(status_code=400, detail="最终确认时间不能早于首次选片时间")

        selection.final_confirm_time = confirm_time
        db.commit()
        db.refresh(selection)
        return SelectionResponse.model_validate(selection)


selections_router = Router(route_handlers=[SelectionsController], path="/api")
