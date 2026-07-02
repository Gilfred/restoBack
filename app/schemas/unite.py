from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from app.enums import UniteType

class UniteBase(BaseModel):
    unite: UniteType

class UniteCreate(UniteBase):
    pass

class UniteResponse(UniteBase):
    restaurantId: UUID
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    isActive: bool
    createdAt: datetime
    updatedAt: datetime
