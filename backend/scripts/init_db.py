import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models import User, UserRole, Order, OrderStatus
from datetime import date


def init_db():
    print("创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成")

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("创建默认管理员账号...")
            admin = User(
                username="admin",
                email="admin@example.com",
                full_name="系统管理员",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                phone="13800000000",
                is_active=True,
            )
            db.add(admin)
            print("管理员账号创建成功: admin / admin123")

        photographer = db.query(User).filter(User.username == "photographer").first()
        if not photographer:
            print("创建示例摄影师账号...")
            photographer = User(
                username="photographer",
                email="photographer@example.com",
                full_name="张摄影师",
                hashed_password=get_password_hash("123456"),
                role=UserRole.PHOTOGRAPHER,
                phone="13800000001",
                is_active=True,
            )
            db.add(photographer)
            print("摄影师账号创建成功: photographer / 123456")

        retoucher = db.query(User).filter(User.username == "retoucher").first()
        if not retoucher:
            print("创建示例修图师账号...")
            retoucher = User(
                username="retoucher",
                email="retoucher@example.com",
                full_name="李修图师",
                hashed_password=get_password_hash("123456"),
                role=UserRole.RETOUCHER,
                phone="13800000002",
                is_active=True,
            )
            db.add(retoucher)
            print("修图师账号创建成功: retoucher / 123456")

        customer = db.query(User).filter(User.username == "customer").first()
        if not customer:
            print("创建示例客户账号...")
            customer = User(
                username="customer",
                email="customer@example.com",
                full_name="王先生",
                hashed_password=get_password_hash("123456"),
                role=UserRole.CUSTOMER,
                phone="13900000001",
                is_active=True,
            )
            db.add(customer)
            print("客户账号创建成功: customer / 123456")

        db.commit()
        print("\n初始化完成！")
    except Exception as e:
        db.rollback()
        print(f"初始化失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
