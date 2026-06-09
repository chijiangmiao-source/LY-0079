from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DeliveryVersionBase(BaseModel):
    storage_path: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    photo_count: int = 0


class DeliveryVersionCreate(DeliveryVersionBase):
    order_id: int
    delivered_by: Optional[int] = None
    is_protected: bool = False


class DeliveryVersionUpdate(BaseModel):
    description: Optional[str] = None
    storage_path: Optional[str] = Field(None, max_length=500)
    photo_count: Optional[int] = None


class DeliveryVersionResponse(DeliveryVersionBase):
    id: int
    order_id: int
    version: int
    delivery_date: datetime
    delivered_by: Optional[int]
    is_protected: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DeliveryVersionListItem(BaseModel):
    id: int
    order_id: int
    order_no: Optional[str]
    version: int
    photo_count: int
    delivery_date: datetime
    is_protected: bool
    created_at: datetime

    class Config:
        from_attributes = True
