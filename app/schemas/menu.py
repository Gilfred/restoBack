from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from app.enums import MenuCategorieNom
from app.schemas.repas import RepasResponse
from app.schemas.boisson import BoissonResponse


# --- MenuFamilleImage Schemas ---
class MenuFamilleImageBase(BaseModel):
    imageUrl: str
    ordre: Optional[int] = 0

class MenuFamilleImageCreate(MenuFamilleImageBase):
    familleId: UUID

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
    menuFamilleId: UUID

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


# --- MenuBoisson Schemas ---
class MenuBoissonBase(BaseModel):
    ordre: Optional[int] = 0
    imageUrl: Optional[str] = None

class MenuBoissonCreate(MenuBoissonBase):
    boissonId: UUID

class MenuBoissonUpdate(BaseModel):
    ordre: Optional[int] = None
    imageUrl: Optional[str] = None
    boissonId: Optional[UUID] = None

class MenuBoissonResponse(MenuBoissonBase):
    id: UUID
    boissonId: Optional[UUID] = None
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

class MenuBoissonDisplayResponse(BaseModel):
    id: UUID
    ordre: int
    imageUrl: Optional[str] = None
    boisson: Optional[BoissonResponse] = None

    model_config = ConfigDict(from_attributes=True)

class RestaurantSimpleResponse(BaseModel):
    id: UUID
    name: str
    address: str
    phone: str

    model_config = ConfigDict(from_attributes=True)

class MenuDisplayResponse(BaseModel):
    restaurant: RestaurantSimpleResponse
    familles: List[MenuFamilleDisplayResponse] = []
    boissons: List[MenuBoissonDisplayResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- UploadCenter Schemas ---
class UploadCenterPresignRequest(BaseModel):
    filename: str
    sizeBytes: int
    mimeType: str

class UploadCenterPresignResponse(BaseModel):
    file_id: str
    upload_url: str
    expires_in: int

class UploadCenterCompleteRequest(BaseModel):
    file_id: str

class UploadCenterCompleteResponse(BaseModel):
    id: str
    url: Optional[str] = None
    status: str
    original_name: str
    mime_type: str
    size_bytes: int
    visibility: str
