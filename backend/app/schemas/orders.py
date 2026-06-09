from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import datetime, date

from app.models import OrderStatus


class OrderBase(BaseModel):
    shoot_type: Optional[str] = Field(None, max_length=100)
    shoot_date: Optional[date] = None
    shoot_time_start: Optional[datetime] = None
    shoot_time_end: Optional[datetime] = None
    city: Optional[str] = Field(None, max_length=100)
    service_package: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = Field(None, max_length=255)
    total_photos: int = Field(0, ge=0)
    included_retouches: int = Field(0, ge=0)
    notes: Optional[str] = None

    @model_validator(mode="after")
    def check_retouches(self):
        if self.included_retouches > self.total_photos:
            raise ValueError("精修数量不能超过照片总数")
        return self

    @model_validator(mode="after")
    def check_time_range(self):
        if self.shoot_time_start and self.shoot_time_end:
            if self.shoot_time_end <= self.shoot_time_start:
                raise ValueError("拍摄结束时间必须晚于开始时间")
        return self

    @model_validator(mode="after")
    def check_shoot_date_match(self):
        if self.shoot_date and self.shoot_time_start:
            if self.shoot_date != self.shoot_time_start.date():
                raise ValueError("拍摄日期必须与开始时间的日期一致")
        if self.shoot_date and self.shoot_time_end:
            if self.shoot_date != self.shoot_time_end.date():
                raise ValueError("拍摄日期必须与结束时间的日期一致")
        return self


class OrderCreate(OrderBase):
    customer_id: int
    photographer_id: Optional[int] = None


class OrderUpdate(BaseModel):
    customer_id: Optional[int] = None
    photographer_id: Optional[int] = None
    shoot_type: Optional[str] = Field(None, max_length=100)
    shoot_date: Optional[date] = None
    shoot_time_start: Optional[datetime] = None
    shoot_time_end: Optional[datetime] = None
    city: Optional[str] = Field(None, max_length=100)
    service_package: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = Field(None, max_length=255)
    total_photos: Optional[int] = Field(None, ge=0)
    included_retouches: Optional[int] = Field(None, ge=0)
    status: Optional[OrderStatus] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def check_retouches(self):
        if self.total_photos is not None and self.included_retouches is not None:
            if self.included_retouches > self.total_photos:
                raise ValueError("精修数量不能超过照片总数")
        return self

    @model_validator(mode="after")
    def check_time_range(self):
        if self.shoot_time_start and self.shoot_time_end:
            if self.shoot_time_end <= self.shoot_time_start:
                raise ValueError("拍摄结束时间必须晚于开始时间")
        return self

    @model_validator(mode="after")
    def check_shoot_date_match(self):
        if self.shoot_date and self.shoot_time_start:
            if self.shoot_date != self.shoot_time_start.date():
                raise ValueError("拍摄日期必须与开始时间的日期一致")
        if self.shoot_date and self.shoot_time_end:
            if self.shoot_date != self.shoot_time_end.date():
                raise ValueError("拍摄日期必须与结束时间的日期一致")
        return self


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
    photographer_name: Optional[str]
    photographer_id: Optional[int]
    shoot_type: Optional[str]
    shoot_date: Optional[date]
    shoot_time_start: Optional[datetime]
    shoot_time_end: Optional[datetime]
    city: Optional[str]
    service_package: Optional[str]
    status: OrderStatus
    total_photos: int
    created_at: datetime

    class Config:
        from_attributes = True


class ScheduleConflict(BaseModel):
    has_conflict: bool
    conflicting_orders: List["ScheduleConflictOrder"] = []


class ScheduleConflictOrder(BaseModel):
    order_id: int
    order_no: str
    customer_name: Optional[str]
    shoot_time_start: Optional[datetime]
    shoot_time_end: Optional[datetime]
    city: Optional[str]
