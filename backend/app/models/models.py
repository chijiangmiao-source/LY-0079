from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Date, Enum, Float
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PHOTOGRAPHER = "photographer"
    RETOUCHER = "retoucher"
    CUSTOMER = "customer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders_as_customer = relationship("Order", back_populates="customer", foreign_keys="Order.customer_id")
    orders_as_photographer = relationship("Order", back_populates="photographer", foreign_keys="Order.photographer_id")
    assigned_sheets = relationship("PhotoSheet", back_populates="retoucher", foreign_keys="PhotoSheet.retoucher_id")
    retouch_requests = relationship("RetouchRequest", back_populates="retoucher", foreign_keys="RetouchRequest.retoucher_id")


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    SHOOTING = "shooting"
    SHOT = "shot"
    RETOUCHING = "retouching"
    SELECTING = "selecting"
    LOCKED = "locked"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    photographer_id = Column(Integer, ForeignKey("users.id"))
    shoot_type = Column(String(100))
    shoot_date = Column(Date)
    location = Column(String(255))
    total_photos = Column(Integer, default=0)
    included_retouches = Column(Integer, default=0)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("User", back_populates="orders_as_customer", foreign_keys=[customer_id])
    photographer = relationship("User", back_populates="orders_as_photographer", foreign_keys=[photographer_id])
    photo_sheets = relationship("PhotoSheet", back_populates="order", cascade="all, delete-orphan")
    photo_batches = relationship("PhotoBatch", back_populates="order", cascade="all, delete-orphan")
    delivery_versions = relationship("DeliveryVersion", back_populates="order", cascade="all, delete-orphan")


class RetouchStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class LockStatus(str, enum.Enum):
    UNLOCKED = "unlocked"
    LOCKED = "locked"
    FOLLOW_UP = "follow_up"


class PhotoSheet(Base):
    __tablename__ = "photo_sheets"

    id = Column(Integer, primary_key=True, index=True)
    sheet_no = Column(String(50), unique=True, index=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    total_photos = Column(Integer, default=0, nullable=False)
    selectable_count = Column(Integer, default=0, nullable=False)
    retouch_status = Column(Enum(RetouchStatus), default=RetouchStatus.NOT_STARTED, nullable=False)
    retoucher_id = Column(Integer, ForeignKey("users.id"))
    selection_deadline = Column(DateTime)
    lock_status = Column(Enum(LockStatus), default=LockStatus.UNLOCKED, nullable=False)
    locked_at = Column(DateTime)
    locked_by = Column(Integer, ForeignKey("users.id"))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order = relationship("Order", back_populates="photo_sheets")
    retoucher = relationship("User", back_populates="assigned_sheets", foreign_keys=[retoucher_id])
    photo_batches = relationship("PhotoBatch", back_populates="photo_sheet")
    selection_records = relationship("SelectionRecord", back_populates="photo_sheet", cascade="all, delete-orphan")
    retouch_requests = relationship("RetouchRequest", back_populates="photo_sheet", cascade="all, delete-orphan")


class PhotoBatch(Base):
    __tablename__ = "photo_batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_no = Column(String(50), unique=True, index=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    sheet_id = Column(Integer, ForeignKey("photo_sheets.id"))
    photo_count = Column(Integer, default=0, nullable=False)
    storage_path = Column(String(500))
    batch_type = Column(String(50), default="original")
    description = Column(Text)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="photo_batches")
    photo_sheet = relationship("PhotoSheet", back_populates="photo_batches")


class SelectionRecord(Base):
    __tablename__ = "selection_records"

    id = Column(Integer, primary_key=True, index=True)
    sheet_id = Column(Integer, ForeignKey("photo_sheets.id"), nullable=False)
    customer_name = Column(String(100), nullable=False)
    selection_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    selected_count = Column(Integer, default=0, nullable=False)
    selected_photo_ids = Column(Text)
    retouch_notes = Column(Text)
    final_confirm_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    photo_sheet = relationship("PhotoSheet", back_populates="selection_records")
    retouch_requests = relationship("RetouchRequest", back_populates="selection_record", cascade="all, delete-orphan")


class RetouchRequestStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class RetouchRequest(Base):
    __tablename__ = "retouch_requests"

    id = Column(Integer, primary_key=True, index=True)
    sheet_id = Column(Integer, ForeignKey("photo_sheets.id"), nullable=False)
    selection_id = Column(Integer, ForeignKey("selection_records.id"), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    description = Column(Text)
    retoucher_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(RetouchRequestStatus), default=RetouchRequestStatus.PENDING, nullable=False)
    storage_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    photo_sheet = relationship("PhotoSheet", back_populates="retouch_requests")
    selection_record = relationship("SelectionRecord", back_populates="retouch_requests")
    retoucher = relationship("User", back_populates="retouch_requests", foreign_keys=[retoucher_id])


class DeliveryVersion(Base):
    __tablename__ = "delivery_versions"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    delivery_date = Column(DateTime, default=datetime.utcnow)
    storage_path = Column(String(500))
    description = Column(Text)
    photo_count = Column(Integer, default=0)
    delivered_by = Column(Integer, ForeignKey("users.id"))
    is_protected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="delivery_versions")
