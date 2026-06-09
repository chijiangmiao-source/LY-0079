from typing import List, Optional
from litestar import Router, get, put, delete, Request, post
from litestar.controller import Controller
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotAuthorizedException, PermissionDeniedException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_password_hash, decode_token
from app.models import User, UserRole
from app.schemas.auth import UserCreate, UserUpdate, UserResponse, UserListItem


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


class UsersController(Controller):
    path = "/users"
    dependencies = {"db": Provide(provide_db)}

    def _check_admin(self, request: Request, db: Session) -> User:
        user = get_current_user_from_request(request, db)
        if user.role != UserRole.ADMIN:
            raise PermissionDeniedException("需要管理员权限")
        return user

    @get("/")
    async def list_users(
        self,
        request: Request,
        db: Session,
        role: Optional[UserRole] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[UserListItem]:
        self._check_admin(request, db)
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
        get_current_user_from_request(request, db)
        retouchers = db.query(User).filter(User.role == UserRole.RETOUCHER, User.is_active == True).all()
        return [UserListItem.model_validate(u) for u in retouchers]

    @get("/customers")
    async def list_customers(
        self,
        request: Request,
        db: Session,
    ) -> List[UserListItem]:
        get_current_user_from_request(request, db)
        customers = db.query(User).filter(User.role == UserRole.CUSTOMER, User.is_active == True).all()
        return [UserListItem.model_validate(u) for u in customers]

    @get("/{user_id:int}")
    async def get_user(self, request: Request, db: Session, user_id: int) -> UserResponse:
        current_user = get_current_user_from_request(request, db)
        if current_user.id != user_id and current_user.role != UserRole.ADMIN:
            raise PermissionDeniedException("权限不足")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return UserResponse.model_validate(user)

    @post("/")
    async def create_user(self, request: Request, db: Session, data: UserCreate) -> UserResponse:
        self._check_admin(request, db)
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
        current_user = get_current_user_from_request(request, db)
        if current_user.id != user_id and current_user.role != UserRole.ADMIN:
            raise PermissionDeniedException("权限不足")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

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

    @delete("/{user_id:int}")
    async def delete_user(self, request: Request, db: Session, user_id: int) -> dict:
        self._check_admin(request, db)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        if user.id == get_current_user_from_request(request, db).id:
            raise HTTPException(status_code=400, detail="不能删除自己")
        user.is_active = False
        db.commit()
        return {"message": "用户已禁用"}


users_router = Router(route_handlers=[UsersController], path="/api")
