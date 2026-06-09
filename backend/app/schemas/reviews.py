from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

from app.models import FollowUpStatus, AfterSalesResult


class CustomerReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    tags: Optional[str] = Field(None, max_length=500)
    feedback: Optional[str] = None
    is_anonymous: bool = False


class CustomerReviewCreate(CustomerReviewBase):
    order_id: int


class CustomerReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    tags: Optional[str] = Field(None, max_length=500)
    feedback: Optional[str] = None
    is_anonymous: Optional[bool] = None


class CustomerReviewResponse(CustomerReviewBase):
    id: int
    order_id: int
    submitted_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerReviewDetail(CustomerReviewResponse):
    order_no: Optional[str] = None
    customer_name: Optional[str] = None
    photographer_name: Optional[str] = None


class FollowUpRecordBase(BaseModel):
    follow_up_time: Optional[datetime] = None
    satisfaction: Optional[int] = Field(None, ge=1, le=5)
    tags: Optional[str] = Field(None, max_length=500)
    feedback: Optional[str] = None
    after_sales_result: Optional[AfterSalesResult] = None
    after_sales_notes: Optional[str] = None
    status: FollowUpStatus = FollowUpStatus.PENDING
    review_deadline: Optional[datetime] = None


class FollowUpRecordCreate(FollowUpRecordBase):
    order_id: int


class FollowUpRecordUpdate(BaseModel):
    follow_up_time: Optional[datetime] = None
    satisfaction: Optional[int] = Field(None, ge=1, le=5)
    tags: Optional[str] = Field(None, max_length=500)
    feedback: Optional[str] = None
    after_sales_result: Optional[AfterSalesResult] = None
    after_sales_notes: Optional[str] = None
    status: Optional[FollowUpStatus] = None
    review_deadline: Optional[datetime] = None


class FollowUpRecordResponse(FollowUpRecordBase):
    id: int
    order_id: int
    follow_up_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FollowUpRecordDetail(FollowUpRecordResponse):
    order_no: Optional[str] = None
    customer_name: Optional[str] = None
    photographer_id: Optional[int] = None
    photographer_name: Optional[str] = None
    shoot_date: Optional[date] = None
    follow_up_by_name: Optional[str] = None
    customer_rating: Optional[int] = None
    review_submitted: bool = False


class FollowUpListItem(BaseModel):
    id: int
    order_id: int
    order_no: str
    customer_name: Optional[str] = None
    photographer_id: Optional[int] = None
    photographer_name: Optional[str] = None
    shoot_date: Optional[date] = None
    status: FollowUpStatus
    satisfaction: Optional[int] = None
    follow_up_time: Optional[datetime] = None
    review_deadline: Optional[datetime] = None
    customer_rating: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SatisfactionTrendItem(BaseModel):
    date: date
    avg_satisfaction: float
    review_count: int


class LowScoreOrder(BaseModel):
    order_id: int
    order_no: str
    customer_name: Optional[str] = None
    photographer_name: Optional[str] = None
    rating: int
    feedback: Optional[str] = None
    tags: Optional[str] = None
    submitted_at: datetime
    follow_up_status: Optional[str] = None


class PendingFollowUpStat(BaseModel):
    total_pending: int = 0
    pending_7d: int = 0
    pending_overdue: int = 0
    in_progress: int = 0
    completed_last_7d: int = 0


class ReviewDashboardStats(BaseModel):
    avg_rating_30d: float = 0.0
    review_count_30d: int = 0
    satisfaction_trend: List[SatisfactionTrendItem] = []
    low_score_orders: List[LowScoreOrder] = []
    pending_follow_up: PendingFollowUpStat = PendingFollowUpStat()
