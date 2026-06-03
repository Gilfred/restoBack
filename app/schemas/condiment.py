from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class CondimentBase(BaseModel):
    nomcondiment: str
    restaurantId: UUID

class CondimentCreate(CondimentBase):
    pass

class CondimentUpdate(BaseModel):
    nomcondiment: Optional[str] = None

class CondimentResponse(CondimentBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    createdAt: datetime
    updatedAt: datetime
