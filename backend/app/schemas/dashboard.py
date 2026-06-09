from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


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


class UpcomingShootOrder(BaseModel):
    order_id: int
    order_no: str
    customer_name: Optional[str]
    photographer_id: Optional[int]
    photographer_name: Optional[str]
    shoot_date: Optional[date]
    shoot_time_start: Optional[datetime]
    shoot_time_end: Optional[datetime]
    city: Optional[str]
    service_package: Optional[str]
    status: str


class PhotographerScheduleStat(BaseModel):
    photographer_id: int
    photographer_name: str
    total_orders: int = 0
    occupied_days: int = 0
    upcoming_orders: List[UpcomingShootOrder] = []


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
    upcoming_shoots: List[UpcomingShootOrder] = []
    photographer_schedule_stats: List[PhotographerScheduleStat] = []


class DashboardResponse(BaseModel):
    stats: DashboardStats
    generated_at: datetime
