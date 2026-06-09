from typing import Generator, Optional
from litestar import Request
from litestar.exceptions import PermissionDeniedException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user as auth_get_current_user
from app.models import User, UserRole


def get_current_user(request: Request, db: Session = next(get_db())) -> User:
    return auth_get_current_user(request, db)


def require_roles(*roles: UserRole):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            db = next(get_db())
            user = auth_get_current_user(request, db)
            if user.role not in roles:
                raise PermissionDeniedException("权限不足")
            kwargs["current_user"] = user
            kwargs["db"] = db
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator
