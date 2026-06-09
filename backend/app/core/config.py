from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "摄影工作室修片管理系统"
    DEBUG: bool = True

    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/photo_studio?charset=utf8mb4"

    SECRET_KEY: str = "your-secret-key-change-in-production-please-change-this-very-long-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
