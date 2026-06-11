from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.schemas.role import RoleWithPermissionsResponse
from app.enums import UserRestaurantStatus

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    image: Optional[str] = None
    isActive: bool
    createdAt: datetime

class StaffResponse(UserResponse):
    model_config = ConfigDict(from_attributes=True)
    role: Optional[RoleWithPermissionsResponse] = None
    status: UserRestaurantStatus

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class Token(BaseModel):
    access_token: str
    token_type: str
