from typing import Optional, List
from sqlalchemy.orm import Session

from app.models import User, UserRole


class UserService:
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_name_by_id(db: Session, user_id: Optional[int]) -> Optional[str]:
        if not user_id:
            return None
        user = UserService.get_by_id(db, user_id)
        return user.full_name if user else None

    @staticmethod
    def list_by_role(db: Session, role: UserRole, only_active: bool = True) -> List[User]:
        query = db.query(User).filter(User.role == role)
        if only_active:
            query = query.filter(User.is_active == True)
        return query.all()

    @staticmethod
    def list_photographers(db: Session, only_active: bool = True) -> List[User]:
        return UserService.list_by_role(db, UserRole.PHOTOGRAPHER, only_active)

    @staticmethod
    def list_retouchers(db: Session, only_active: bool = True) -> List[User]:
        return UserService.list_by_role(db, UserRole.RETOUCHER, only_active)

    @staticmethod
    def list_customers(db: Session, only_active: bool = True) -> List[User]:
        return UserService.list_by_role(db, UserRole.CUSTOMER, only_active)
