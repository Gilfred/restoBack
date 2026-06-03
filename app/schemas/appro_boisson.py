from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class ApproBoissonBase(BaseModel):
    boissonId: UUID
    casierId: UUID
    prixAchat: float
    nbreCasier: int

class ApproBoissonCreate(ApproBoissonBase):
    pass

class ApproBoissonUpdate(BaseModel):
    prixAchat: Optional[float] = None
    nbreCasier: Optional[int] = None
    casierId: Optional[UUID] = None

class ApproBoissonResponse(ApproBoissonBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    createdAt: datetime
    updatedAt: datetime
