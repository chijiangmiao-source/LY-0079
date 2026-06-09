from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import re

from app.models import UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: str = Field(..., max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: UserRole = UserRole.CUSTOMER

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("姓名不能为空")
        if re.search(r"\s", v):
            raise ValueError("姓名不能包含空格")
        if re.search(r"[a-zA-Z0-9]", v):
            raise ValueError("姓名不能包含英文或数字")
        if not re.match(r"^[\u4e00-\u9fa5·]+$", v):
            raise ValueError("姓名只能包含中文字符")
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


class QuickCustomerCreate(BaseModel):
    full_name: str = Field(..., max_length=100)
    phone: Optional[str] = Field(None, max_length=20)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("姓名不能为空")
        if re.search(r"\s", v):
            raise ValueError("姓名不能包含空格")
        if re.search(r"[a-zA-Z0-9]", v):
            raise ValueError("姓名不能包含英文或数字")
        if not re.match(r"^[\u4e00-\u9fa5·]+$", v):
            raise ValueError("姓名只能包含中文字符")
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6, max_length=100)


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListItem(BaseModel):
    id: int
    username: str
    full_name: str
    email: Optional[str]
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True
