from datetime import timedelta
from typing import Annotated
from litestar import Router, post, get, Request
from litestar.controller import Controller
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotAuthorizedException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash, decode_token
from app.core.config import settings
from app.models import User, UserRole
from app.schemas.auth import (
    LoginRequest,
    Token,
    UserCreate,
    UserResponse,
)


def provide_db() -> Session:
    return next(get_db())


class AuthController(Controller):
    path = "/auth"
    dependencies = {"db": Provide(provide_db)}

    @post("/login")
    async def login(self, data: LoginRequest, db: Session) -> Token:
        user = db.query(User).filter(User.username == data.username).first()
        if not user or not verify_password(data.password, user.hashed_password):
            raise NotAuthorizedException("用户名或密码错误")
        if not user.is_active:
            raise NotAuthorizedException("用户已被禁用")

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(subject=user.id, expires_delta=access_token_expires)
        return Token(access_token=access_token)

    @post("/register")
    async def register(self, data: UserCreate, db: Session) -> UserResponse:
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

    @get("/me")
    async def get_me(self, request: Request, db: Session) -> UserResponse:
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
        return UserResponse.model_validate(user)


auth_router = Router(route_handlers=[AuthController], path="/api")
