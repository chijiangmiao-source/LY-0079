from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class SelectionRecordBase(BaseModel):
    customer_name: str = Field(..., max_length=100)
    selected_count: int = 0
    selected_photo_ids: Optional[str] = None
    retouch_notes: Optional[str] = None


class SelectionCreate(SelectionRecordBase):
    sheet_id: int

    @field_validator("selected_count")
    @classmethod
    def check_selected_count(cls, v: int) -> int:
        if v < 0:
            raise ValueError("入选数量不能为负数")
        return v


class SelectionUpdate(BaseModel):
    customer_name: Optional[str] = Field(None, max_length=100)
    selected_count: Optional[int] = None
    selected_photo_ids: Optional[str] = None
    retouch_notes: Optional[str] = None

    @field_validator("selected_count")
    @classmethod
    def check_selected_count(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("入选数量不能为负数")
        return v


class SelectionResponse(SelectionRecordBase):
    id: int
    sheet_id: int
    selection_time: datetime
    final_confirm_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SelectionConfirmRequest(BaseModel):
    final_confirm_time: Optional[datetime] = None


class SelectionListItem(BaseModel):
    id: int
    sheet_id: int
    sheet_no: Optional[str]
    customer_name: str
    selected_count: int
    selection_time: datetime
    final_confirm_time: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
