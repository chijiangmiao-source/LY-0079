from typing import List, Optional
import uuid
from litestar import Router, get, put, delete, Request, post
from litestar.controller import Controller
from litestar.di import Provide
from litestar.exceptions import HTTPException, PermissionDeniedException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import (
    get_current_user,
    require_admin,
    require_roles,
    get_or_404,
)
from app.core.security import get_password_hash
from app.models import User, UserRole
from app.services.user_service import UserService
from app.schemas.auth import UserCreate, UserUpdate, UserResponse, UserListItem, QuickCustomerCreate


def provide_db() -> Session:
    return next(get_db())


class UsersController(Controller):
    path = "/users"
    dependencies = {"db": Provide(provide_db)}

    @get("/")
    async def list_users(
        self,
        request: Request,
        db: Session,
        role: Optional[UserRole] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[UserListItem]:
        user = get_current_user(request, db)
        require_admin(user)
        query = db.query(User)
        if role:
            query = query.filter(User.role == role)
        users = query.offset(skip).limit(limit).all()
        return [UserListItem.model_validate(u) for u in users]

    @get("/retouchers")
    async def list_retouchers(
        self,
        request: Request,
        db: Session,
    ) -> List[UserListItem]:
        get_current_user(request, db)
        retouchers = UserService.list_retouchers(db)
        return [UserListItem.model_validate(u) for u in retouchers]

    @get("/photographers")
    async def list_photographers(
        self,
        request: Request,
        db: Session,
    ) -> List[UserListItem]:
        get_current_user(request, db)
        photographers = UserService.list_photographers(db)
        return [UserListItem.model_validate(u) for u in photographers]

    @get("/customers")
    async def list_customers(
        self,
        request: Request,
        db: Session,
    ) -> List[UserListItem]:
        get_current_user(request, db)
        customers = UserService.list_customers(db)
        return [UserListItem.model_validate(u) for u in customers]

    @get("/{user_id:int}")
    async def get_user(self, request: Request, db: Session, user_id: int) -> UserResponse:
        current_user = get_current_user(request, db)
        if current_user.id != user_id and current_user.role != UserRole.ADMIN:
            raise PermissionDeniedException("权限不足")
        user = get_or_404(db, User, user_id, "用户")
        return UserResponse.model_validate(user)

    @post("/")
    async def create_user(self, request: Request, db: Session, data: UserCreate) -> UserResponse:
        user = get_current_user(request, db)
        require_admin(user)
        existing = db.query(User).filter(
            (User.username == data.username) | (User.email == data.email)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="用户名或邮箱已存在")

        user = User(
            username=data.username,
            email=data.email,
            full_name=data.full_name,
            hashed_password=get_password_hash(data.password),
            role=data.role,
            phone=data.phone,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return UserResponse.model_validate(user)

    @put("/{user_id:int}")
    async def update_user(
        self,
        request: Request,
        db: Session,
        user_id: int,
        data: UserUpdate,
    ) -> UserResponse:
        current_user = get_current_user(request, db)
        if current_user.id != user_id and current_user.role != UserRole.ADMIN:
            raise PermissionDeniedException("权限不足")

        user = get_or_404(db, User, user_id, "用户")

        update_data = data.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        if current_user.role != UserRole.ADMIN and "role" in update_data:
            update_data.pop("role")
            update_data.pop("is_active", None)

        for key, value in update_data.items():
            setattr(user, key, value)

        db.commit()
        db.refresh(user)
        return UserResponse.model_validate(user)

    @delete("/{user_id:int}", status_code=200)
    async def delete_user(self, request: Request, db: Session, user_id: int) -> dict:
        current_user = get_current_user(request, db)
        require_admin(current_user)
        user = get_or_404(db, User, user_id, "用户")
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="不能删除自己")
        user.is_active = False
        db.commit()
        return {"message": "用户已禁用"}

    @post("/quick-customer")
    async def create_quick_customer(self, request: Request, db: Session, data: QuickCustomerCreate) -> UserListItem:
        user = get_current_user(request, db)
        require_roles(user, UserRole.ADMIN, UserRole.PHOTOGRAPHER)

        base_username = f"cust_{uuid.uuid4().hex[:8]}"
        username = base_username
        counter = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{base_username}_{counter}"
            counter += 1

        customer = User(
            username=username,
            full_name=data.full_name,
            phone=data.phone,
            hashed_password=get_password_hash("123456"),
            role=UserRole.CUSTOMER,
            is_active=True,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return UserListItem.model_validate(customer)


users_router = Router(route_handlers=[UsersController], path="/api")
