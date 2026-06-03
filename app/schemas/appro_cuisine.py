from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class ApproCuisineBase(BaseModel):
    condimentId: UUID
    uniteId: UUID
    prix: float
    qte: float

class ApproCuisineCreate(ApproCuisineBase):
    pass

class ApproCuisineUpdate(BaseModel):
    prix: Optional[float] = None
    qte: Optional[float] = None
    uniteId: Optional[UUID] = None

class ApproCuisineResponse(ApproCuisineBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    createdAt: datetime
    updatedAt: datetime
