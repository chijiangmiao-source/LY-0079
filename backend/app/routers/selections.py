from typing import List, Optional
from datetime import datetime
from litestar import Router, get, post, put, Request
from litestar.controller import Controller
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotAuthorizedException, PermissionDeniedException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models import (
    User, UserRole, Order, PhotoSheet, LockStatus,
    SelectionRecord,
)
from app.schemas.selections import (
    SelectionCreate,
    SelectionUpdate,
    SelectionResponse,
    SelectionConfirmRequest,
    SelectionListItem,
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
        user = get_current_user_from_request(request, db)
        query = db.query(SelectionRecord)

        if user.role == UserRole.CUSTOMER:
            customer_orders = db.query(Order).filter(Order.customer_id == user.id).all()
            customer_order_ids = [o.id for o in customer_orders]
            customer_sheets = db.query(PhotoSheet).filter(PhotoSheet.order_id.in_(customer_order_ids)).all()
            customer_sheet_ids = [s.id for s in customer_sheets]
            query = query.filter(SelectionRecord.sheet_id.in_(customer_sheet_ids))

        if sheet_id:
            query = query.filter(SelectionRecord.sheet_id == sheet_id)

        selections = query.order_by(SelectionRecord.created_at.desc()).offset(skip).limit(limit).all()
        result = []
        for sel in selections:
            sheet = db.query(PhotoSheet).filter(PhotoSheet.id == sel.sheet_id).first()
            item = SelectionListItem.model_validate(sel)
            item.sheet_no = sheet.sheet_no if sheet else None
            result.append(item)
        return result

    @get("/{selection_id:int}")
    async def get_selection(self, request: Request, db: Session, selection_id: int) -> SelectionResponse:
        user = get_current_user_from_request(request, db)
        selection = db.query(SelectionRecord).filter(SelectionRecord.id == selection_id).first()
        if not selection:
            raise HTTPException(status_code=404, detail="选片记录不存在")

        if user.role == UserRole.CUSTOMER:
            sheet = db.query(PhotoSheet).filter(PhotoSheet.id == selection.sheet_id).first()
            order = db.query(Order).filter(Order.id == sheet.order_id).first() if sheet else None
            if not order or order.customer_id != user.id:
                raise PermissionDeniedException("权限不足")

        return SelectionResponse.model_validate(selection)

    @post("/")
    async def create_selection(self, request: Request, db: Session, data: SelectionCreate) -> SelectionResponse:
        user = get_current_user_from_request(request, db)

        sheet = db.query(PhotoSheet).filter(PhotoSheet.id == data.sheet_id).first()
        if not sheet:
            raise HTTPException(status_code=404, detail="片单不存在")

        if user.role == UserRole.CUSTOMER:
            order = db.query(Order).filter(Order.id == sheet.order_id).first()
            if not order or order.customer_id != user.id:
                raise PermissionDeniedException("权限不足")
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
        user = get_current_user_from_request(request, db)
        selection = db.query(SelectionRecord).filter(SelectionRecord.id == selection_id).first()
        if not selection:
            raise HTTPException(status_code=404, detail="选片记录不存在")

        if selection.final_confirm_time:
            raise HTTPException(status_code=400, detail="选片已最终确认，无法修改")

        sheet = db.query(PhotoSheet).filter(PhotoSheet.id == selection.sheet_id).first()
        if not sheet:
            raise HTTPException(status_code=404, detail="关联片单不存在")
        self._check_sheet_locked(sheet)

        if user.role == UserRole.CUSTOMER:
            order = db.query(Order).filter(Order.id == sheet.order_id).first()
            if not order or order.customer_id != user.id:
                raise PermissionDeniedException("权限不足")
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
        user = get_current_user_from_request(request, db)
        selection = db.query(SelectionRecord).filter(SelectionRecord.id == selection_id).first()
        if not selection:
            raise HTTPException(status_code=404, detail="选片记录不存在")

        sheet = db.query(PhotoSheet).filter(PhotoSheet.id == selection.sheet_id).first()
        if not sheet:
            raise HTTPException(status_code=404, detail="关联片单不存在")
        self._check_sheet_locked(sheet)

        if user.role == UserRole.CUSTOMER:
            order = db.query(Order).filter(Order.id == sheet.order_id).first()
            if not order or order.customer_id != user.id:
                raise PermissionDeniedException("权限不足")
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
