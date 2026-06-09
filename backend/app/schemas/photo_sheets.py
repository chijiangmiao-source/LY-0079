from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.models import RetouchStatus, LockStatus


class PhotoSheetBase(BaseModel):
    total_photos: int = 0
    selectable_count: int = 0
    selection_deadline: Optional[datetime] = None
    notes: Optional[str] = None


class PhotoSheetCreate(PhotoSheetBase):
    order_id: int
    retoucher_id: Optional[int] = None


class PhotoSheetUpdate(BaseModel):
    retoucher_id: Optional[int] = None
    total_photos: Optional[int] = None
    selectable_count: Optional[int] = None
    retouch_status: Optional[RetouchStatus] = None
    selection_deadline: Optional[datetime] = None
    notes: Optional[str] = None


class PhotoSheetResponse(PhotoSheetBase):
    id: int
    sheet_no: str
    order_id: int
    retoucher_id: Optional[int]
    retouch_status: RetouchStatus
    lock_status: LockStatus
    locked_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PhotoSheetDetailResponse(PhotoSheetResponse):
    order_no: Optional[str] = None
    retoucher_name: Optional[str] = None
    customer_name: Optional[str] = None
    selection_count: int = 0
    is_overdue: bool = False


class PhotoSheetListItem(BaseModel):
    id: int
    sheet_no: str
    order_id: int
    order_no: Optional[str]
    total_photos: int
    retouch_status: RetouchStatus
    lock_status: LockStatus
    selection_deadline: Optional[datetime]
    retoucher_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
