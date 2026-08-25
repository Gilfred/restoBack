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

class UserBasicInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    email: str

class CommandeBase(BaseModel):
    restaurantId: Optional[UUID] = None
    numeroCommande: Optional[str] = None
    userId: Optional[UUID] = None
    total: Optional[float] = None
    statut: CommandeStatut = CommandeStatut.PENDING

class CommandeCreate(CommandeBase):
    articles: List[CommandeArticleCreate]

class CommandeUpdate(BaseModel):
    statut: Optional[CommandeStatut] = None
    total: Optional[float] = None

class CommandeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    restaurantId: UUID
    numeroCommande: str
    userId: UUID
    total: float
    statut: CommandeStatut
    createdAt: datetime
    updatedAt: datetime
    user: Optional[UserBasicInfo] = None
    articles: List[CommandeArticleResponse]
