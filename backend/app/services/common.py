from typing import Optional, List, Any, Type, TypeVar
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.models import User, UserRole, Order, PhotoSheet
from app.services.user_service import UserService
from app.services.order_service import OrderService, SheetService

ModelType = TypeVar("ModelType")
SchemaType = TypeVar("SchemaType", bound=BaseModel)


class PaginationParams:
    def __init__(self, skip: int = 0, limit: int = 100):
        self.skip = skip
        self.limit = limit


class ResponseAssembler:
    @staticmethod
    def enrich_order_list_item(item: Any, db: Session, order: Order) -> Any:
        customer = UserService.get_by_id(db, order.customer_id)
        photographer = UserService.get_by_id(db, order.photographer_id) if order.photographer_id else None
        item.customer_name = customer.full_name if customer else None
        item.photographer_name = photographer.full_name if photographer else None
        return item

    @staticmethod
    def enrich_sheet_list_item(item: Any, db: Session, sheet: PhotoSheet) -> Any:
        order = OrderService.get_by_id(db, sheet.order_id)
        retoucher = UserService.get_by_id(db, sheet.retoucher_id) if sheet.retoucher_id else None
        item.order_no = order.order_no if order else None
        item.retoucher_name = retoucher.full_name if retoucher else None
        return item

    @staticmethod
    def build_order_list_response(
        db: Session,
        orders: List[Order],
        item_schema: Type[SchemaType],
    ) -> List[SchemaType]:
        result = []
        for o in orders:
            item = item_schema.model_validate(o)
            ResponseAssembler.enrich_order_list_item(item, db, o)
            result.append(item)
        return result

    @staticmethod
    def build_sheet_list_response(
        db: Session,
        sheets: List[PhotoSheet],
        item_schema: Type[SchemaType],
    ) -> List[SchemaType]:
        result = []
        for s in sheets:
            item = item_schema.model_validate(s)
            ResponseAssembler.enrich_sheet_list_item(item, db, s)
            result.append(item)
        return result


class QueryFilter:
    @staticmethod
    def apply_pagination(query, skip: int = 0, limit: int = 100, order_by=None):
        if order_by is not None:
            query = query.order_by(order_by)
        return query.offset(skip).limit(limit)

    @staticmethod
    def apply_equality_filter(query, field, value):
        if value is not None:
            return query.filter(field == value)
        return query

    @staticmethod
    def apply_range_filter(query, field, min_value=None, max_value=None):
        if min_value is not None:
            query = query.filter(field >= min_value)
        if max_value is not None:
            query = query.filter(field <= max_value)
        return query

    @staticmethod
    def apply_customer_scope(query, user: User, order_model=Order, join_field=None):
        if user.role != UserRole.CUSTOMER:
            return query
        if join_field:
            return query.filter(join_field == user.id)
        return query.filter(order_model.customer_id == user.id)

    @staticmethod
    def apply_photographer_scope(query, user: User, photographer_field):
        if user.role != UserRole.PHOTOGRAPHER:
            return query
        return query.filter(
            (photographer_field == user.id) | (photographer_field.is_(None))
        )
