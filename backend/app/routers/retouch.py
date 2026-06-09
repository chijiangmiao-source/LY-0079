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
    SelectionRecord, RetouchRequest, RetouchRequestStatus,
)
from app.services.user_service import UserService
from app.services.order_service import SheetService
from app.schemas.retouch import (
    RetouchRequestCreate,
    RetouchRequestUpdate,
    RetouchRequestResponse,
    RetouchRequestDetailResponse,
    RetouchRequestListItem,
)


def provide_db() -> Session:
    return next(get_db())


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
        user = get_current_user(request, db)
        query = db.query(RetouchRequest)

        if user.role == UserRole.CUSTOMER:
            customer_sheet_ids = get_customer_sheet_ids(db, user.id)
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
            sheet = SheetService.get_by_id(db, r.sheet_id)
            retoucher = UserService.get_by_id(db, r.retoucher_id) if r.retoucher_id else None
            item = RetouchRequestListItem.model_validate(r)
            item.sheet_no = sheet.sheet_no if sheet else None
            item.retoucher_name = retoucher.full_name if retoucher else None
            result.append(item)
        return result

    @get("/{request_id:int}")
    async def get_request(self, request: Request, db: Session, request_id: int) -> RetouchRequestDetailResponse:
        user = get_current_user(request, db)
        retouch = get_or_404(db, RetouchRequest, request_id, "加修请求")

        if user.role == UserRole.CUSTOMER:
            sheet = SheetService.get_by_id(db, retouch.sheet_id)
            check_customer_sheet_access(sheet, user, db) if sheet else None

        sheet = SheetService.get_by_id(db, retouch.sheet_id)
        retoucher = UserService.get_by_id(db, retouch.retoucher_id) if retouch.retoucher_id else None

        resp = RetouchRequestDetailResponse.model_validate(retouch)
        resp.sheet_no = sheet.sheet_no if sheet else None
        resp.retoucher_name = retoucher.full_name if retoucher else None
        return resp

    @post("/")
    async def create_request(self, request: Request, db: Session, data: RetouchRequestCreate) -> RetouchRequestResponse:
        user = get_current_user(request, db)
        require_roles(user, UserRole.ADMIN, UserRole.PHOTOGRAPHER, UserRole.CUSTOMER)

        sheet = get_or_404(db, PhotoSheet, data.sheet_id, "片单")

        if sheet.lock_status == LockStatus.LOCKED:
            raise HTTPException(status_code=400, detail="片单已锁定")

        selection = get_or_404(db, SelectionRecord, data.selection_id, "选片记录")

        if user.role == UserRole.CUSTOMER:
            check_customer_sheet_access(sheet, user, db)

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
        user = get_current_user(request, db)
        retouch = get_or_404(db, RetouchRequest, request_id, "加修请求")

        require_roles(user, UserRole.ADMIN, UserRole.PHOTOGRAPHER, UserRole.RETOUCHER)

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
        user = get_current_user(request, db)
        require_roles(user, UserRole.ADMIN, UserRole.PHOTOGRAPHER, UserRole.RETOUCHER)

        old_retouch = get_or_404(db, RetouchRequest, request_id, "原加修请求")

        sheet = SheetService.get_by_id(db, old_retouch.sheet_id)
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
