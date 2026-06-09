from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.models import RetouchRequestStatus


class RetouchRequestBase(BaseModel):
    description: Optional[str] = None
    storage_path: Optional[str] = Field(None, max_length=500)


class RetouchRequestCreate(RetouchRequestBase):
    sheet_id: int
    selection_id: int
    retoucher_id: Optional[int] = None


class RetouchRequestUpdate(BaseModel):
    retoucher_id: Optional[int] = None
    description: Optional[str] = None
    status: Optional[RetouchRequestStatus] = None
    storage_path: Optional[str] = Field(None, max_length=500)


class RetouchRequestResponse(RetouchRequestBase):
    id: int
    sheet_id: int
    selection_id: int
    version: int
    retoucher_id: Optional[int]
    status: RetouchRequestStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RetouchRequestDetailResponse(RetouchRequestResponse):
    retoucher_name: Optional[str] = None
    sheet_no: Optional[str] = None


class RetouchRequestListItem(BaseModel):
    id: int
    sheet_id: int
    sheet_no: Optional[str]
    selection_id: int
    version: int
    status: RetouchRequestStatus
    retoucher_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
