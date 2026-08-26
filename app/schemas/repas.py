from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class RepasBase(BaseModel):
    nomRepas: str
    prix: float

class RepasCreate(RepasBase):
    pass

class RepasUpdate(BaseModel):
    nomRepas: Optional[str] = None
    prix: Optional[float] = None

class RepasResponse(RepasBase):
    id: UUID
    restaurantId: UUID
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)
