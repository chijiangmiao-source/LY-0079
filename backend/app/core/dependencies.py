from typing import Generator, Optional
from litestar import Request
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models import User, UserRole


def get_current_user(request: Request, db: Session = next(get_db())) -> User:
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

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise NotAuthorizedException("令牌内容无效")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise NotAuthorizedException("用户不存在")
    if not user.is_active:
        raise NotAuthorizedException("用户已被禁用")

    return user


def require_roles(*roles: UserRole):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            db = next(get_db())
            user = get_current_user(request, db)
            if user.role not in roles:
                raise PermissionDeniedException("权限不足")
            kwargs["current_user"] = user
            kwargs["db"] = db
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator
