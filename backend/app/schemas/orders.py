from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

from app.models import OrderStatus


class OrderBase(BaseModel):
    shoot_type: Optional[str] = Field(None, max_length=100)
    shoot_date: Optional[date] = None
    location: Optional[str] = Field(None, max_length=255)
    total_photos: int = 0
    included_retouches: int = 0
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    customer_id: int
    photographer_id: Optional[int] = None


class OrderUpdate(BaseModel):
    customer_id: Optional[int] = None
    photographer_id: Optional[int] = None
    shoot_type: Optional[str] = Field(None, max_length=100)
    shoot_date: Optional[date] = None
    location: Optional[str] = Field(None, max_length=255)
    total_photos: Optional[int] = None
    included_retouches: Optional[int] = None
    status: Optional[OrderStatus] = None
    notes: Optional[str] = None


class OrderResponse(OrderBase):
    id: int
    order_no: str
    customer_id: int
    photographer_id: Optional[int]
    status: OrderStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderDetailResponse(OrderResponse):
    customer_name: Optional[str] = None
    photographer_name: Optional[str] = None
    sheet_count: int = 0
    photo_count: int = 0


class OrderListItem(BaseModel):
    id: int
    order_no: str
    customer_name: Optional[str]
    shoot_type: Optional[str]
    shoot_date: Optional[date]
    status: OrderStatus
    total_photos: int
    created_at: datetime

    class Config:
        from_attributes = True
