from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

from app.models import ComplaintType, ComplaintStatus, ComplaintSource, CompensationType


class CompensationBase(BaseModel):
    compensation_type: CompensationType
    amount: float = 0.0
    description: Optional[str] = None


class CompensationCreate(CompensationBase):
    pass


class CompensationUpdate(BaseModel):
    compensation_type: Optional[CompensationType] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    is_executed: Optional[bool] = None


class CompensationResponse(CompensationBase):
    id: int
    complaint_id: int
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    is_executed: bool = False
    executed_at: Optional[datetime] = None
    executed_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompensationDetail(CompensationResponse):
    approver_name: Optional[str] = None
    executor_name: Optional[str] = None


class ComplaintTicketBase(BaseModel):
    complaint_type: ComplaintType
    title: str = Field(..., max_length=200)
    description: str


class ComplaintTicketCreate(ComplaintTicketBase):
    order_id: int
    source: ComplaintSource = ComplaintSource.CUSTOMER_INITIATED


class ComplaintTicketManualCreate(ComplaintTicketBase):
    order_id: int
    customer_id: int
    source: ComplaintSource = ComplaintSource.MANUAL


class ComplaintTicketUpdate(BaseModel):
    complaint_type: Optional[ComplaintType] = None
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    status: Optional[ComplaintStatus] = None
    assigned_to: Optional[int] = None
    process_deadline: Optional[datetime] = None
    progress_notes: Optional[str] = None
    final_conclusion: Optional[str] = None


class ComplaintAssign(BaseModel):
    assigned_to: int
    process_deadline: Optional[datetime] = None


class ComplaintProcess(BaseModel):
    progress_notes: str
    status: Optional[ComplaintStatus] = None


class ComplaintResolve(BaseModel):
    final_conclusion: str
    status: ComplaintStatus = ComplaintStatus.RESOLVED


class ComplaintTicketResponse(ComplaintTicketBase):
    id: int
    ticket_no: str
    order_id: int
    customer_id: int
    source: ComplaintSource
    status: ComplaintStatus
    rating_trigger: Optional[int] = None
    assigned_to: Optional[int] = None
    assigned_at: Optional[datetime] = None
    process_deadline: Optional[datetime] = None
    progress_notes: Optional[str] = None
    final_conclusion: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ComplaintTicketListItem(BaseModel):
    id: int
    ticket_no: str
    order_id: int
    order_no: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    photographer_id: Optional[int] = None
    photographer_name: Optional[str] = None
    complaint_type: ComplaintType
    source: ComplaintSource
    title: str
    status: ComplaintStatus
    rating_trigger: Optional[int] = None
    assigned_to: Optional[int] = None
    assignee_name: Optional[str] = None
    process_deadline: Optional[datetime] = None
    has_compensation: bool = False
    is_overdue: bool = False
    created_at: datetime
    updated_at: datetime


class ComplaintTicketDetail(ComplaintTicketResponse):
    order_no: Optional[str] = None
    customer_name: Optional[str] = None
    photographer_id: Optional[int] = None
    photographer_name: Optional[str] = None
    shoot_date: Optional[date] = None
    assignee_name: Optional[str] = None
    creator_name: Optional[str] = None
    compensation: Optional[CompensationDetail] = None
    is_overdue: bool = False


class ComplaintTrendItem(BaseModel):
    date: date
    complaint_count: int
    resolved_count: int


class OverdueComplaintItem(BaseModel):
    id: int
    ticket_no: str
    order_no: Optional[str] = None
    customer_name: Optional[str] = None
    status: ComplaintStatus
    overdue_days: int
    process_deadline: Optional[datetime] = None
    assigned_to: Optional[int] = None
    assignee_name: Optional[str] = None


class ComplaintDashboardStats(BaseModel):
    total_complaints_30d: int = 0
    pending_count: int = 0
    processing_count: int = 0
    resolved_count_30d: int = 0
    overdue_count: int = 0
    total_compensation_amount: float = 0.0
    compensation_count: int = 0
    avg_resolve_hours: float = 0.0
    complaint_trend: List[ComplaintTrendItem] = []
    overdue_complaints: List[OverdueComplaintItem] = []
    type_distribution: dict = {}
