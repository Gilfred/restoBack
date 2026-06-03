from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from app.enums import UniteType

class UniteBase(BaseModel):
    unite: UniteType
    restaurantId: UUID

class UniteCreate(UniteBase):
    pass

class UniteResponse(UniteBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    isActive: bool
    createdAt: datetime
    updatedAt: datetime
