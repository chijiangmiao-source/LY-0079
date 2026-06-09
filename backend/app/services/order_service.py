from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import (
    Order, OrderStatus, User, UserRole, PhotoSheet,
)
from app.services.user_service import UserService


class OrderService:
    @staticmethod
    def get_by_id(db: Session, order_id: int) -> Optional[Order]:
        return db.query(Order).filter(Order.id == order_id).first()

    @staticmethod
    def get_order_no(db: Session, order_id: Optional[int]) -> Optional[str]:
        if not order_id:
            return None
        order = OrderService.get_by_id(db, order_id)
        return order.order_no if order else None

    @staticmethod
    def apply_role_filter(query, user: User):
        if user.role == UserRole.CUSTOMER:
            return query.filter(Order.customer_id == user.id)
        elif user.role == UserRole.PHOTOGRAPHER:
            return query.filter(
                (Order.photographer_id == user.id) | (Order.photographer_id.is_(None))
            )
        return query

    @staticmethod
    def check_schedule_conflict(
        db: Session,
        photographer_id: int,
        shoot_time_start: datetime,
        shoot_time_end: datetime,
        exclude_order_id: Optional[int] = None,
    ) -> List[Order]:
        if not photographer_id or not shoot_time_start or not shoot_time_end:
            return []

        from sqlalchemy import and_

        query = db.query(Order).filter(
            Order.photographer_id == photographer_id,
            Order.shoot_time_start.isnot(None),
            Order.shoot_time_end.isnot(None),
            Order.status != OrderStatus.CANCELLED,
            or_(
                and_(
                    Order.shoot_time_start <= shoot_time_start,
                    Order.shoot_time_end > shoot_time_start,
                ),
                and_(
                    Order.shoot_time_start < shoot_time_end,
                    Order.shoot_time_end >= shoot_time_end,
                ),
                and_(
                    Order.shoot_time_start >= shoot_time_start,
                    Order.shoot_time_end <= shoot_time_end,
                ),
            ),
        )

        if exclude_order_id:
            query = query.filter(Order.id != exclude_order_id)

        return query.all()

    @staticmethod
    def format_conflict_info(db: Session, conflicts: List[Order]) -> str:
        conflict_info = []
        for o in conflicts:
            customer = UserService.get_by_id(db, o.customer_id)
            time_str = o.shoot_time_start.strftime("%Y-%m-%d %H:%M") if o.shoot_time_start else ""
            if o.shoot_time_end:
                time_str += " - " + o.shoot_time_end.strftime("%H:%M")
            conflict_info.append(
                f"{o.order_no}({customer.full_name if customer else '未知客户'} {time_str})"
            )
        return "; ".join(conflict_info)


class SheetService:
    @staticmethod
    def get_by_id(db: Session, sheet_id: int) -> Optional[PhotoSheet]:
        return db.query(PhotoSheet).filter(PhotoSheet.id == sheet_id).first()

    @staticmethod
    def get_sheet_no(db: Session, sheet_id: Optional[int]) -> Optional[str]:
        if not sheet_id:
            return None
        sheet = SheetService.get_by_id(db, sheet_id)
        return sheet.sheet_no if sheet else None

    @staticmethod
    def apply_role_filter(query, user: User, db: Session):
        from app.core.auth import get_customer_order_ids

        if user.role == UserRole.CUSTOMER:
            customer_order_ids = get_customer_order_ids(db, user.id)
            return query.filter(PhotoSheet.order_id.in_(customer_order_ids))
        elif user.role == UserRole.RETOUCHER:
            return query.filter(
                (PhotoSheet.retoucher_id == user.id) | (PhotoSheet.retoucher_id.is_(None))
            )
        return query
