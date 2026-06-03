from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from app.enums import CommandeStatut

class CommandeArticleBase(BaseModel):
    boissonId: Optional[UUID] = None
    repasId: Optional[UUID] = None
    qte: int
    prixUnitaire: float

class CommandeArticleCreate(CommandeArticleBase):
    pass

class CommandeArticleResponse(CommandeArticleBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    sousTotal: float
    isActive: bool

class CommandeArticleUpdate(BaseModel):
    boissonId: Optional[UUID] = None
    repasId: Optional[UUID] = None
    qte: Optional[int] = None
    prixUnitaire: Optional[float] = None

class CommandeBase(BaseModel):
    restaurantId: UUID
    numeroCommande: str
    userId: UUID
    total: float
    statut: CommandeStatut = CommandeStatut.PENDING

class CommandeCreate(CommandeBase):
    articles: List[CommandeArticleCreate]

class CommandeUpdate(BaseModel):
    statut: Optional[CommandeStatut] = None
    total: Optional[float] = None

class CommandeResponse(CommandeBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    createdAt: datetime
    updatedAt: datetime
    articles: List[CommandeArticleResponse]
