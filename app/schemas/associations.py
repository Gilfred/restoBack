from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List

class UserRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    userId: UUID
    roleId: UUID
    createdAt: datetime
    updatedAt: datetime

class RolePermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    roleId: UUID
    permissionId: UUID
    createdAt: datetime
    updatedAt: datetime

class UserRoleCreate(BaseModel):
    userId: UUID
    roleId: UUID

class RolePermissionCreate(BaseModel):
    roleId: UUID
    permissionId: UUID

class UserRolesUpdate(BaseModel):
    roleIds: List[UUID]
