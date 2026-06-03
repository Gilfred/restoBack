from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionResponse(PermissionBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    createdAt: datetime
    updatedAt: datetime
