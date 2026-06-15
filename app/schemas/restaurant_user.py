from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from app.enums import UserRestaurantStatus
from app.schemas.auth import UserResponse
from app.schemas.role import RoleResponse, RoleWithPermissionsResponse
from app.schemas.restaurant import RestaurantResponse

class RestaurantUserBase(BaseModel):
    restaurantId: UUID

class RestaurantUserCreate(RestaurantUserBase):
    pass

class RestaurantUserApprove(BaseModel):
    roleId: UUID

class RestaurantUserRoleUpdate(BaseModel):
    roleId: UUID

class RestaurantUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    userId: UUID
    restaurantId: UUID
    roleId: Optional[UUID] = None
    status: UserRestaurantStatus
    createdAt: datetime
    updatedAt: datetime

class RestaurantUserWithDetailsResponse(RestaurantUserResponse):
    user: UserResponse
    role: Optional[RoleResponse] = None

class MeRestaurantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    restaurant: RestaurantResponse
    role: Optional[RoleWithPermissionsResponse] = None
    status: UserRestaurantStatus
