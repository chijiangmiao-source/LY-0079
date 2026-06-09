from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PhotoBatchBase(BaseModel):
    photo_count: int = 0
    storage_path: Optional[str] = Field(None, max_length=500)
    batch_type: str = Field("original", max_length=50)
    description: Optional[str] = None


class PhotoBatchCreate(PhotoBatchBase):
    order_id: int
    sheet_id: Optional[int] = None
    uploaded_by: Optional[int] = None


class PhotoBatchUpdate(BaseModel):
    sheet_id: Optional[int] = None
    photo_count: Optional[int] = None
    storage_path: Optional[str] = Field(None, max_length=500)
    batch_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class PhotoBatchResponse(PhotoBatchBase):
    id: int
    batch_no: str
    order_id: int
    sheet_id: Optional[int]
    uploaded_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class PhotoBatchListItem(BaseModel):
    id: int
    batch_no: str
    order_id: int
    sheet_id: Optional[int]
    photo_count: int
    batch_type: str
    created_at: datetime

    class Config:
        from_attributes = True
