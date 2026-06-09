from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class RetoucherWorkload(BaseModel):
    retoucher_id: int
    retoucher_name: str
    assigned_sheets: int = 0
    in_progress_sheets: int = 0
    completed_sheets: int = 0
    total_photos: int = 0


class OrderSelectionProgress(BaseModel):
    order_id: int
    order_no: str
    customer_name: Optional[str]
    total_sheets: int = 0
    locked_sheets: int = 0
    unlocked_sheets: int = 0
    follow_up_sheets: int = 0
    progress: float = 0.0


class OverdueSheet(BaseModel):
    sheet_id: int
    sheet_no: str
    order_id: int
    order_no: str
    customer_name: Optional[str]
    selection_deadline: Optional[datetime]
    overdue_days: int = 0
    lock_status: str


class DashboardStats(BaseModel):
    total_orders: int = 0
    total_sheets: int = 0
    locked_sheets: int = 0
    unlocked_sheets: int = 0
    follow_up_sheets: int = 0
    total_deliveries: int = 0
    retouchers_workload: List[RetoucherWorkload] = []
    selection_progress: List[OrderSelectionProgress] = []
    overdue_sheets: List[OverdueSheet] = []


class DashboardResponse(BaseModel):
    stats: DashboardStats
    generated_at: datetime
