from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from app.enums import MenuCategorieNom, BoissonContenance
from app.schemas.repas import RepasResponse
from app.schemas.boisson import BoissonResponse


# --- MenuFamilleImage Schemas ---
class MenuFamilleImageBase(BaseModel):
    imageUrl: str
    ordre: Optional[int] = 0

class MenuFamilleImageUpdate(BaseModel):
    imageUrl: Optional[str] = None
    ordre: Optional[int] = None

class MenuFamilleImageResponse(MenuFamilleImageBase):
    id: UUID
    familleId: UUID

    model_config = ConfigDict(from_attributes=True)


# --- MenuFamille Schemas ---
class MenuFamilleBase(BaseModel):
    nom: str
    ordre: Optional[int] = 0

class MenuFamilleCreate(MenuFamilleBase):
    pass

class MenuFamilleUpdate(BaseModel):
    nom: Optional[str] = None
    ordre: Optional[int] = None

class MenuFamilleResponse(MenuFamilleBase):
    id: UUID
    restaurantId: Optional[UUID] = None
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)


# --- MenuCategorie Schemas ---
class MenuCategorieBase(BaseModel):
    nom: MenuCategorieNom
    ordre: Optional[int] = 0

class MenuCategorieCreate(MenuCategorieBase):
    menuFamilleId: Optional[UUID] = None

class MenuCategorieUpdate(BaseModel):
    nom: Optional[MenuCategorieNom] = None
    ordre: Optional[int] = None
    menuFamilleId: Optional[UUID] = None

class MenuCategorieResponse(MenuCategorieBase):
    id: UUID
    menuFamilleId: Optional[UUID] = None
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)


# --- MenuRepas Schemas ---
class MenuRepasBase(BaseModel):
    ordre: Optional[int] = 0

class MenuRepasCreate(MenuRepasBase):
    menuCategorieId: UUID
    repasId: UUID

class MenuRepasUpdate(BaseModel):
    ordre: Optional[int] = None
    menuCategorieId: Optional[UUID] = None
    repasId: Optional[UUID] = None

class MenuRepasResponse(MenuRepasBase):
    id: UUID
    menuCategorieId: Optional[UUID] = None
    repasId: Optional[UUID] = None
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)


# --- MenuBoissonFamille & MenuBoissonImage Schemas ---
class MenuBoissonFamilleBase(BaseModel):
    nom: str

class MenuBoissonFamilleCreate(MenuBoissonFamilleBase):
    pass

class MenuBoissonFamilleUpdate(BaseModel):
    nom: Optional[str] = None

class MenuBoissonFamilleResponse(MenuBoissonFamilleBase):
    id: UUID
    restaurantId: UUID
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)

class MenuBoissonImageBase(BaseModel):
    url: str

class MenuBoissonImageResponse(MenuBoissonImageBase):
    id: UUID
    menuBoissonFamilleId: UUID
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)


# --- MenuBoisson Schemas ---
class MenuBoissonBase(BaseModel):
    menuBoissonFamilleId: UUID
    boissonId: UUID

class MenuBoissonCreate(MenuBoissonBase):
    pass

class MenuBoissonUpdate(BaseModel):
    menuBoissonFamilleId: Optional[UUID] = None
    boissonId: Optional[UUID] = None

class MenuBoissonResponse(MenuBoissonBase):
    id: UUID
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Full Display Nested Schemas ---
class MenuRepasDisplayResponse(BaseModel):
    id: UUID
    ordre: int
    repas: Optional[RepasResponse] = None

    model_config = ConfigDict(from_attributes=True)

class MenuCategorieDisplayResponse(BaseModel):
    id: UUID
    nom: MenuCategorieNom
    ordre: int
    repasList: List[MenuRepasDisplayResponse] = []

    model_config = ConfigDict(from_attributes=True)

class MenuFamilleDisplayResponse(BaseModel):
    id: UUID
    nom: str
    ordre: int
    images: List[MenuFamilleImageResponse] = []
    categories: List[MenuCategorieDisplayResponse] = []

    model_config = ConfigDict(from_attributes=True)

class MenuBoissonImageDisplayResponse(BaseModel):
    id: UUID
    url: str

    model_config = ConfigDict(from_attributes=True)

class BoissonDisplayResponse(BaseModel):
    id: UUID
    nomBoisson: str
    contenance: BoissonContenance
    prixVente: float

    model_config = ConfigDict(from_attributes=True)

class MenuBoissonFamilleDisplayResponse(BaseModel):
    id: UUID
    nom: str
    images: List[MenuBoissonImageDisplayResponse] = []
    boissons: List[BoissonDisplayResponse] = []

    model_config = ConfigDict(from_attributes=True)

class RestaurantSimpleResponse(BaseModel):
    id: UUID
    name: str
    address: str
    phone: str

    model_config = ConfigDict(from_attributes=True)

class RestaurantMenuDisplayResponse(BaseModel):
    restaurant: RestaurantSimpleResponse
    familles: List[MenuFamilleDisplayResponse] = []
    boissons: List[MenuBoissonFamilleDisplayResponse] = []

    model_config = ConfigDict(from_attributes=True)

class MenuDisplayResponse(BaseModel):
    restaurants: List[RestaurantMenuDisplayResponse] = []


# --- Image Upload Response Schema ---
class MenuFamilleImageUploadResponse(BaseModel):
    id: UUID
    familleId: UUID
    imageUrl: str
    ordre: int
    public_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class MenuBoissonImageUploadResponse(BaseModel):
    id: UUID
    menuBoissonFamilleId: UUID
    url: str
    public_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
