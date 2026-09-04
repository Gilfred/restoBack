from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from app.enums import CommandeStatut

class CommandeArticleCreate(BaseModel):
    boissonId: Optional[UUID] = None
    repasId: Optional[UUID] = None
    qte: int = Field(..., gt=0)

class CommandeArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    boissonId: Optional[UUID] = None
    repasId: Optional[UUID] = None
    qte: int
    prixUnitaire: float
    sousTotal: float
    isActive: bool

class CommandeArticleUpdate(BaseModel):
    boissonId: Optional[UUID] = None
    repasId: Optional[UUID] = None
    qte: Optional[int] = Field(None, gt=0)
    prixUnitaire: Optional[float] = None

# UTILISATEUR
class UserBasicInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    email: str

# COMMANDE
class CommandeCreate(BaseModel):
    userId: UUID
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
