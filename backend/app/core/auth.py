from typing import Optional, List
from litestar import Request
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException, HTTPException
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.models import User, UserRole, Order, PhotoSheet, ComplaintTicket


def get_current_user(request: Request, db: Session) -> User:
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


def require_roles(user: User, *roles: UserRole) -> None:
    if user.role not in roles:
        raise PermissionDeniedException("权限不足")


def require_any_role(user: User, roles: List[UserRole]) -> None:
    if user.role not in roles:
        raise PermissionDeniedException("权限不足")


def require_admin(user: User) -> None:
    if user.role != UserRole.ADMIN:
        raise PermissionDeniedException("需要管理员权限")


def check_order_permission(order: Order, user: User, allow_retoucher: bool = True) -> None:
    if user.role in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
        return
    if user.role == UserRole.CUSTOMER and order.customer_id == user.id:
        return
    if user.role == UserRole.RETOUCHER and allow_retoucher:
        return
    raise PermissionDeniedException("权限不足")


def check_sheet_permission(sheet: PhotoSheet, user: User, db: Session) -> None:
    if user.role in [UserRole.ADMIN, UserRole.PHOTOGRAPHER, UserRole.RETOUCHER]:
        return
    if user.role == UserRole.CUSTOMER:
        order = db.query(Order).filter(Order.id == sheet.order_id).first()
        if order and order.customer_id == user.id:
            return
    raise PermissionDeniedException("权限不足")


def check_customer_sheet_access(sheet: PhotoSheet, user: User, db: Session) -> None:
    if user.role != UserRole.CUSTOMER:
        return
    order = db.query(Order).filter(Order.id == sheet.order_id).first()
    if not order or order.customer_id != user.id:
        raise PermissionDeniedException("权限不足")


def check_ticket_permission(ticket: ComplaintTicket, user: User, db: Session) -> None:
    if user.role in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
        return
    if user.role == UserRole.CUSTOMER and ticket.customer_id == user.id:
        return
    if ticket.assigned_to == user.id:
        return
    raise PermissionDeniedException("权限不足")


def get_customer_order_ids(db: Session, user_id: int) -> List[int]:
    orders = db.query(Order).filter(Order.customer_id == user_id).all()
    return [o.id for o in orders]


def get_customer_sheet_ids(db: Session, user_id: int) -> List[int]:
    order_ids = get_customer_order_ids(db, user_id)
    if not order_ids:
        return []
    sheets = db.query(PhotoSheet).filter(PhotoSheet.order_id.in_(order_ids)).all()
    return [s.id for s in sheets]


def get_or_404(db: Session, model, entity_id: int, entity_name: str = "资源"):
    entity = db.query(model).filter(model.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_name}不存在")
    return entity
