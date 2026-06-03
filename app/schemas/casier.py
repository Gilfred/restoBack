from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from app.enums import CasierType

class CasierBase(BaseModel):
    typeCasier: CasierType
    restaurantId: UUID

class CasierCreate(CasierBase):
    pass

class CasierResponse(CasierBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    isActive: bool
    createdAt: datetime
    updatedAt: datetime
