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
    SelectionRecord, RetouchRequest, RetouchRequestStatus,
)
from app.schemas.retouch import (
    RetouchRequestCreate,
    RetouchRequestUpdate,
    RetouchRequestResponse,
    RetouchRequestDetailResponse,
    RetouchRequestListItem,
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


class RetouchController(Controller):
    path = "/retouch"
    dependencies = {"db": Provide(provide_db)}

    @get("/")
    async def list_requests(
        self,
        request: Request,
        db: Session,
        sheet_id: Optional[int] = None,
        selection_id: Optional[int] = None,
        status: Optional[RetouchRequestStatus] = None,
        retoucher_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[RetouchRequestListItem]:
        user = get_current_user_from_request(request, db)
        query = db.query(RetouchRequest)

        if user.role == UserRole.CUSTOMER:
            customer_orders = db.query(Order).filter(Order.customer_id == user.id).all()
            customer_order_ids = [o.id for o in customer_orders]
            customer_sheets = db.query(PhotoSheet).filter(PhotoSheet.order_id.in_(customer_order_ids)).all()
            customer_sheet_ids = [s.id for s in customer_sheets]
            query = query.filter(RetouchRequest.sheet_id.in_(customer_sheet_ids))
        elif user.role == UserRole.RETOUCHER:
            query = query.filter(
                (RetouchRequest.retoucher_id == user.id) | (RetouchRequest.retoucher_id.is_(None))
            )

        if sheet_id:
            query = query.filter(RetouchRequest.sheet_id == sheet_id)
        if selection_id:
            query = query.filter(RetouchRequest.selection_id == selection_id)
        if status:
            query = query.filter(RetouchRequest.status == status)
        if retoucher_id:
            query = query.filter(RetouchRequest.retoucher_id == retoucher_id)

        requests = query.order_by(RetouchRequest.created_at.desc()).offset(skip).limit(limit).all()
        result = []
        for r in requests:
            sheet = db.query(PhotoSheet).filter(PhotoSheet.id == r.sheet_id).first()
            retoucher = db.query(User).filter(User.id == r.retoucher_id).first() if r.retoucher_id else None
            item = RetouchRequestListItem.model_validate(r)
            item.sheet_no = sheet.sheet_no if sheet else None
            item.retoucher_name = retoucher.full_name if retoucher else None
            result.append(item)
        return result

    @get("/{request_id:int}")
    async def get_request(self, request: Request, db: Session, request_id: int) -> RetouchRequestDetailResponse:
        user = get_current_user_from_request(request, db)
        retouch = db.query(RetouchRequest).filter(RetouchRequest.id == request_id).first()
        if not retouch:
            raise HTTPException(status_code=404, detail="加修请求不存在")

        if user.role == UserRole.CUSTOMER:
            sheet = db.query(PhotoSheet).filter(PhotoSheet.id == retouch.sheet_id).first()
            order = db.query(Order).filter(Order.id == sheet.order_id).first() if sheet else None
            if not order or order.customer_id != user.id:
                raise PermissionDeniedException("权限不足")

        sheet = db.query(PhotoSheet).filter(PhotoSheet.id == retouch.sheet_id).first()
        retoucher = db.query(User).filter(User.id == retouch.retoucher_id).first() if retouch.retoucher_id else None

        resp = RetouchRequestDetailResponse.model_validate(retouch)
        resp.sheet_no = sheet.sheet_no if sheet else None
        resp.retoucher_name = retoucher.full_name if retoucher else None
        return resp

    @post("/")
    async def create_request(self, request: Request, db: Session, data: RetouchRequestCreate) -> RetouchRequestResponse:
        user = get_current_user_from_request(request, db)
        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER, UserRole.CUSTOMER]:
            raise PermissionDeniedException("权限不足")

        sheet = db.query(PhotoSheet).filter(PhotoSheet.id == data.sheet_id).first()
        if not sheet:
            raise HTTPException(status_code=404, detail="片单不存在")

        if sheet.lock_status == LockStatus.LOCKED:
            raise HTTPException(status_code=400, detail="片单已锁定")

        selection = db.query(SelectionRecord).filter(SelectionRecord.id == data.selection_id).first()
        if not selection:
            raise HTTPException(status_code=404, detail="选片记录不存在")

        if user.role == UserRole.CUSTOMER:
            order = db.query(Order).filter(Order.id == sheet.order_id).first()
            if not order or order.customer_id != user.id:
                raise PermissionDeniedException("权限不足")

        existing_count = (
            db.query(RetouchRequest)
            .filter(
                RetouchRequest.sheet_id == data.sheet_id,
                RetouchRequest.selection_id == data.selection_id,
            )
            .count()
        )
        next_version = existing_count + 1

        retouch = RetouchRequest(
            **data.model_dump(),
            version=next_version,
        )
        db.add(retouch)
        db.commit()
        db.refresh(retouch)
        return RetouchRequestResponse.model_validate(retouch)

    @put("/{request_id:int}")
    async def update_request(
        self,
        request: Request,
        db: Session,
        request_id: int,
        data: RetouchRequestUpdate,
    ) -> RetouchRequestResponse:
        user = get_current_user_from_request(request, db)
        retouch = db.query(RetouchRequest).filter(RetouchRequest.id == request_id).first()
        if not retouch:
            raise HTTPException(status_code=404, detail="加修请求不存在")

        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER, UserRole.RETOUCHER]:
            raise PermissionDeniedException("权限不足")

        if retouch.status == RetouchRequestStatus.COMPLETED and retouch.version <= 1:
            update_data = data.model_dump(exclude_unset=True)
            if "status" in update_data and update_data["status"] == RetouchRequestStatus.COMPLETED:
                pass
            elif "description" in update_data or "storage_path" in update_data:
                if retouch.version == 1:
                    raise HTTPException(status_code=400, detail="第一版历史记录不可覆盖，请创建新版本")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(retouch, key, value)

        db.commit()
        db.refresh(retouch)
        return RetouchRequestResponse.model_validate(retouch)

    @post("/{request_id:int}/new-version")
    async def create_new_version(
        self,
        request: Request,
        db: Session,
        request_id: int,
        data: RetouchRequestCreate,
    ) -> RetouchRequestResponse:
        user = get_current_user_from_request(request, db)
        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER, UserRole.RETOUCHER]:
            raise PermissionDeniedException("权限不足")

        old_retouch = db.query(RetouchRequest).filter(RetouchRequest.id == request_id).first()
        if not old_retouch:
            raise HTTPException(status_code=404, detail="原加修请求不存在")

        sheet = db.query(PhotoSheet).filter(PhotoSheet.id == old_retouch.sheet_id).first()
        if sheet and sheet.lock_status == LockStatus.LOCKED:
            raise HTTPException(status_code=400, detail="片单已锁定")

        existing_count = (
            db.query(RetouchRequest)
            .filter(
                RetouchRequest.sheet_id == old_retouch.sheet_id,
                RetouchRequest.selection_id == old_retouch.selection_id,
            )
            .count()
        )
        next_version = existing_count + 1

        new_retouch = RetouchRequest(
            sheet_id=old_retouch.sheet_id,
            selection_id=old_retouch.selection_id,
            version=next_version,
            description=data.description,
            retoucher_id=data.retoucher_id or old_retouch.retoucher_id,
            storage_path=data.storage_path,
            status=RetouchRequestStatus.PENDING,
        )
        db.add(new_retouch)
        db.commit()
        db.refresh(new_retouch)
        return RetouchRequestResponse.model_validate(new_retouch)


retouch_router = Router(route_handlers=[RetouchController], path="/api")
