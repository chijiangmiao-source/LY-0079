from datetime import datetime, timedelta, date
from typing import List
from litestar import Router, get, Request
from litestar.controller import Controller
from litestar.di import Provide
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.auth import (
    get_current_user,
    require_roles,
)
from app.models import (
    User, UserRole, Order, OrderStatus, PhotoSheet, LockStatus, RetouchStatus,
    SelectionRecord, RetouchRequest, RetouchRequestStatus, DeliveryVersion,
)
from app.services.user_service import UserService
from app.services.order_service import OrderService
from app.schemas.dashboard import (
    RetoucherWorkload,
    OrderSelectionProgress,
    OverdueSheet,
    DashboardStats,
    DashboardResponse,
    UpcomingShootOrder,
    PhotographerScheduleStat,
)


def provide_db() -> Session:
    return next(get_db())


class DashboardController(Controller):
    path = "/dashboard"
    dependencies = {"db": Provide(provide_db)}

    @get("/stats")
    async def get_stats(self, request: Request, db: Session) -> DashboardResponse:
        user = get_current_user(request, db)

        now = datetime.utcnow()
        today_start = datetime.combine(date.today(), datetime.min.time())
        seven_days_later = today_start + timedelta(days=7)

        total_orders = db.query(Order).count()
        total_sheets = db.query(PhotoSheet).count()
        locked_sheets = db.query(PhotoSheet).filter(PhotoSheet.lock_status == LockStatus.LOCKED).count()
        unlocked_sheets = db.query(PhotoSheet).filter(PhotoSheet.lock_status == LockStatus.UNLOCKED).count()
        follow_up_sheets = db.query(PhotoSheet).filter(PhotoSheet.lock_status == LockStatus.FOLLOW_UP).count()
        total_deliveries = db.query(DeliveryVersion).count()

        retouchers = UserService.list_retouchers(db)
        retouchers_workload: List[RetoucherWorkload] = []
        for ret in retouchers:
            assigned = db.query(PhotoSheet).filter(PhotoSheet.retoucher_id == ret.id).count()
            in_progress = db.query(PhotoSheet).filter(
                PhotoSheet.retoucher_id == ret.id,
                PhotoSheet.retouch_status == RetouchStatus.IN_PROGRESS,
            ).count()
            completed = db.query(PhotoSheet).filter(
                PhotoSheet.retoucher_id == ret.id,
                PhotoSheet.retouch_status == RetouchStatus.COMPLETED,
            ).count()
            total_photos = (
                db.query(func.sum(PhotoSheet.total_photos))
                .filter(PhotoSheet.retoucher_id == ret.id)
                .scalar()
                or 0
            )
            retouchers_workload.append(
                RetoucherWorkload(
                    retoucher_id=ret.id,
                    retoucher_name=ret.full_name,
                    assigned_sheets=assigned,
                    in_progress_sheets=in_progress,
                    completed_sheets=completed,
                    total_photos=total_photos,
                )
            )

        orders = db.query(Order).all()
        selection_progress: List[OrderSelectionProgress] = []
        for ord in orders:
            sheets = db.query(PhotoSheet).filter(PhotoSheet.order_id == ord.id).all()
            total = len(sheets)
            locked = sum(1 for s in sheets if s.lock_status == LockStatus.LOCKED)
            unlocked = sum(1 for s in sheets if s.lock_status == LockStatus.UNLOCKED)
            follow_up = sum(1 for s in sheets if s.lock_status == LockStatus.FOLLOW_UP)
            progress = (locked / total * 100) if total > 0 else 0.0
            customer = UserService.get_by_id(db, ord.customer_id)
            selection_progress.append(
                OrderSelectionProgress(
                    order_id=ord.id,
                    order_no=ord.order_no,
                    customer_name=customer.full_name if customer else None,
                    total_sheets=total,
                    locked_sheets=locked,
                    unlocked_sheets=unlocked,
                    follow_up_sheets=follow_up,
                    progress=round(progress, 2),
                )
            )

        overdue_sheets_query = (
            db.query(PhotoSheet)
            .filter(
                PhotoSheet.selection_deadline.isnot(None),
                PhotoSheet.selection_deadline < now,
                PhotoSheet.lock_status != LockStatus.LOCKED,
            )
            .all()
        )
        overdue_sheets: List[OverdueSheet] = []
        for s in overdue_sheets_query:
            order = OrderService.get_by_id(db, s.order_id)
            customer = UserService.get_by_id(db, order.customer_id) if order else None
            overdue_days = (now - s.selection_deadline).days if s.selection_deadline else 0
            overdue_sheets.append(
                OverdueSheet(
                    sheet_id=s.id,
                    sheet_no=s.sheet_no,
                    order_id=s.order_id,
                    order_no=order.order_no if order else None,
                    customer_name=customer.full_name if customer else None,
                    selection_deadline=s.selection_deadline,
                    overdue_days=overdue_days,
                    lock_status=s.lock_status.value,
                )
            )

        upcoming_query = db.query(Order).filter(
            Order.shoot_date.isnot(None),
            Order.shoot_date >= today_start.date(),
            Order.shoot_date <= seven_days_later.date(),
            Order.status != OrderStatus.CANCELLED,
        )
        if user.role == UserRole.PHOTOGRAPHER:
            upcoming_query = upcoming_query.filter(Order.photographer_id == user.id)
        elif user.role == UserRole.CUSTOMER:
            upcoming_query = upcoming_query.filter(Order.customer_id == user.id)
        upcoming_orders = upcoming_query.order_by(Order.shoot_date.asc(), Order.shoot_time_start.asc()).all()

        upcoming_shoots: List[UpcomingShootOrder] = []
        for o in upcoming_orders:
            customer = UserService.get_by_id(db, o.customer_id)
            photographer = UserService.get_by_id(db, o.photographer_id) if o.photographer_id else None
            upcoming_shoots.append(
                UpcomingShootOrder(
                    order_id=o.id,
                    order_no=o.order_no,
                    customer_name=customer.full_name if customer else None,
                    photographer_id=o.photographer_id,
                    photographer_name=photographer.full_name if photographer else None,
                    shoot_date=o.shoot_date,
                    shoot_time_start=o.shoot_time_start,
                    shoot_time_end=o.shoot_time_end,
                    city=o.city,
                    service_package=o.service_package,
                    status=o.status.value,
                )
            )

        photographer_schedule_stats: List[PhotographerScheduleStat] = []
        if user.role in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            photographers_query = db.query(User).filter(
                User.role == UserRole.PHOTOGRAPHER,
                User.is_active == True,
            )
            if user.role == UserRole.PHOTOGRAPHER:
                photographers_query = photographers_query.filter(User.id == user.id)
            photographers = photographers_query.all()

            for p in photographers:
                p_orders = (
                    db.query(Order)
                    .filter(
                        Order.photographer_id == p.id,
                        Order.status != OrderStatus.CANCELLED,
                    )
                    .all()
                )
                upcoming_p_orders = [
                    o for o in p_orders
                    if o.shoot_date and today_start.date() <= o.shoot_date <= seven_days_later.date()
                ]
                occupied_days_set = set()
                for o in p_orders:
                    if o.shoot_date:
                        occupied_days_set.add(o.shoot_date)

                p_upcoming_list: List[UpcomingShootOrder] = []
                for o in sorted(upcoming_p_orders, key=lambda x: (x.shoot_date, x.shoot_time_start or datetime.min)):
                    customer = UserService.get_by_id(db, o.customer_id)
                    p_upcoming_list.append(
                        UpcomingShootOrder(
                            order_id=o.id,
                            order_no=o.order_no,
                            customer_name=customer.full_name if customer else None,
                            photographer_id=p.id,
                            photographer_name=p.full_name,
                            shoot_date=o.shoot_date,
                            shoot_time_start=o.shoot_time_start,
                            shoot_time_end=o.shoot_time_end,
                            city=o.city,
                            service_package=o.service_package,
                            status=o.status.value,
                        )
                    )

                photographer_schedule_stats.append(
                    PhotographerScheduleStat(
                        photographer_id=p.id,
                        photographer_name=p.full_name,
                        total_orders=len(p_orders),
                        occupied_days=len(occupied_days_set),
                        upcoming_orders=p_upcoming_list,
                    )
                )

        stats = DashboardStats(
            total_orders=total_orders,
            total_sheets=total_sheets,
            locked_sheets=locked_sheets,
            unlocked_sheets=unlocked_sheets,
            follow_up_sheets=follow_up_sheets,
            total_deliveries=total_deliveries,
            retouchers_workload=retouchers_workload,
            selection_progress=selection_progress,
            overdue_sheets=overdue_sheets,
            upcoming_shoots=upcoming_shoots,
            photographer_schedule_stats=photographer_schedule_stats,
        )

        return DashboardResponse(
            stats=stats,
            generated_at=now,
        )

    @get("/retouchers-workload")
    async def get_retouchers_workload(self, request: Request, db: Session) -> List[RetoucherWorkload]:
        get_current_user(request, db)
        retouchers = UserService.list_retouchers(db)
        result: List[RetoucherWorkload] = []
        for ret in retouchers:
            assigned = db.query(PhotoSheet).filter(PhotoSheet.retoucher_id == ret.id).count()
            in_progress = db.query(PhotoSheet).filter(
                PhotoSheet.retoucher_id == ret.id,
                PhotoSheet.retouch_status == RetouchStatus.IN_PROGRESS,
            ).count()
            completed = db.query(PhotoSheet).filter(
                PhotoSheet.retoucher_id == ret.id,
                PhotoSheet.retouch_status == RetouchStatus.COMPLETED,
            ).count()
            total_photos = (
                db.query(func.sum(PhotoSheet.total_photos))
                .filter(PhotoSheet.retoucher_id == ret.id)
                .scalar()
                or 0
            )
            result.append(
                RetoucherWorkload(
                    retoucher_id=ret.id,
                    retoucher_name=ret.full_name,
                    assigned_sheets=assigned,
                    in_progress_sheets=in_progress,
                    completed_sheets=completed,
                    total_photos=total_photos,
                )
            )
        return result

    @get("/selection-progress")
    async def get_selection_progress(self, request: Request, db: Session) -> List[OrderSelectionProgress]:
        get_current_user(request, db)
        orders = db.query(Order).all()
        result: List[OrderSelectionProgress] = []
        for ord in orders:
            sheets = db.query(PhotoSheet).filter(PhotoSheet.order_id == ord.id).all()
            total = len(sheets)
            locked = sum(1 for s in sheets if s.lock_status == LockStatus.LOCKED)
            unlocked = sum(1 for s in sheets if s.lock_status == LockStatus.UNLOCKED)
            follow_up = sum(1 for s in sheets if s.lock_status == LockStatus.FOLLOW_UP)
            progress = (locked / total * 100) if total > 0 else 0.0
            customer = UserService.get_by_id(db, ord.customer_id)
            result.append(
                OrderSelectionProgress(
                    order_id=ord.id,
                    order_no=ord.order_no,
                    customer_name=customer.full_name if customer else None,
                    total_sheets=total,
                    locked_sheets=locked,
                    unlocked_sheets=unlocked,
                    follow_up_sheets=follow_up,
                    progress=round(progress, 2),
                )
            )
        return result

    @get("/overdue-sheets")
    async def get_overdue_sheets(self, request: Request, db: Session) -> List[OverdueSheet]:
        get_current_user(request, db)
        now = datetime.utcnow()
        overdue_sheets = (
            db.query(PhotoSheet)
            .filter(
                PhotoSheet.selection_deadline.isnot(None),
                PhotoSheet.selection_deadline < now,
                PhotoSheet.lock_status != LockStatus.LOCKED,
            )
            .all()
        )
        result: List[OverdueSheet] = []
        for s in overdue_sheets:
            order = OrderService.get_by_id(db, s.order_id)
            customer = UserService.get_by_id(db, order.customer_id) if order else None
            overdue_days = (now - s.selection_deadline).days if s.selection_deadline else 0
            result.append(
                OverdueSheet(
                    sheet_id=s.id,
                    sheet_no=s.sheet_no,
                    order_id=s.order_id,
                    order_no=order.order_no if order else None,
                    customer_name=customer.full_name if customer else None,
                    selection_deadline=s.selection_deadline,
                    overdue_days=overdue_days,
                    lock_status=s.lock_status.value,
                )
            )
        return result

    @get("/upcoming-shoots")
    async def get_upcoming_shoots(self, request: Request, db: Session) -> List[UpcomingShootOrder]:
        user = get_current_user(request, db)
        today_start = datetime.combine(date.today(), datetime.min.time())
        seven_days_later = today_start + timedelta(days=7)

        query = db.query(Order).filter(
            Order.shoot_date.isnot(None),
            Order.shoot_date >= today_start.date(),
            Order.shoot_date <= seven_days_later.date(),
            Order.status != OrderStatus.CANCELLED,
        )
        if user.role == UserRole.PHOTOGRAPHER:
            query = query.filter(Order.photographer_id == user.id)
        elif user.role == UserRole.CUSTOMER:
            query = query.filter(Order.customer_id == user.id)
        orders = query.order_by(Order.shoot_date.asc(), Order.shoot_time_start.asc()).all()

        result: List[UpcomingShootOrder] = []
        for o in orders:
            customer = UserService.get_by_id(db, o.customer_id)
            photographer = UserService.get_by_id(db, o.photographer_id) if o.photographer_id else None
            result.append(
                UpcomingShootOrder(
                    order_id=o.id,
                    order_no=o.order_no,
                    customer_name=customer.full_name if customer else None,
                    photographer_id=o.photographer_id,
                    photographer_name=photographer.full_name if photographer else None,
                    shoot_date=o.shoot_date,
                    shoot_time_start=o.shoot_time_start,
                    shoot_time_end=o.shoot_time_end,
                    city=o.city,
                    service_package=o.service_package,
                    status=o.status.value,
                )
            )
        return result

    @get("/photographer-schedule-stats")
    async def get_photographer_schedule_stats(
        self, request: Request, db: Session
    ) -> List[PhotographerScheduleStat]:
        user = get_current_user(request, db)
        if user.role not in [UserRole.ADMIN, UserRole.PHOTOGRAPHER]:
            return []

        today_start = datetime.combine(date.today(), datetime.min.time())
        seven_days_later = today_start + timedelta(days=7)

        photographers_query = db.query(User).filter(
            User.role == UserRole.PHOTOGRAPHER,
            User.is_active == True,
        )
        if user.role == UserRole.PHOTOGRAPHER:
            photographers_query = photographers_query.filter(User.id == user.id)
        photographers = photographers_query.all()

        result: List[PhotographerScheduleStat] = []
        for p in photographers:
            p_orders = (
                db.query(Order)
                .filter(
                    Order.photographer_id == p.id,
                    Order.status != OrderStatus.CANCELLED,
                )
                .all()
            )
            upcoming_p_orders = [
                o for o in p_orders
                if o.shoot_date and today_start.date() <= o.shoot_date <= seven_days_later.date()
            ]
            occupied_days_set = set()
            for o in p_orders:
                if o.shoot_date:
                    occupied_days_set.add(o.shoot_date)

            upcoming_list: List[UpcomingShootOrder] = []
            for o in sorted(upcoming_p_orders, key=lambda x: (x.shoot_date, x.shoot_time_start or datetime.min)):
                customer = UserService.get_by_id(db, o.customer_id)
                upcoming_list.append(
                    UpcomingShootOrder(
                        order_id=o.id,
                        order_no=o.order_no,
                        customer_name=customer.full_name if customer else None,
                        photographer_id=p.id,
                        photographer_name=p.full_name,
                        shoot_date=o.shoot_date,
                        shoot_time_start=o.shoot_time_start,
                        shoot_time_end=o.shoot_time_end,
                        city=o.city,
                        service_package=o.service_package,
                        status=o.status.value,
                    )
                )

            result.append(
                PhotographerScheduleStat(
                    photographer_id=p.id,
                    photographer_name=p.full_name,
                    total_orders=len(p_orders),
                    occupied_days=len(occupied_days_set),
                    upcoming_orders=upcoming_list,
                )
            )
        return result


dashboard_router = Router(route_handlers=[DashboardController], path="/api")
