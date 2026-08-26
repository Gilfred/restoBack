from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class ApproBoissonBase(BaseModel):
    boissonId: UUID
    casierId: UUID
    prixAchat: float = Field(..., gt=0)
    nbreCasier: int = Field(..., gt=0)

class ApproBoissonCreate(ApproBoissonBase):
    pass

class ApproBoissonUpdate(BaseModel):
    prixAchat: Optional[float] = Field(None, gt=0)
    nbreCasier: Optional[int] = Field(None, gt=0)
    casierId: Optional[UUID] = None

class ApproBoissonResponse(ApproBoissonBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    createdAt: datetime
    updatedAt: datetime
