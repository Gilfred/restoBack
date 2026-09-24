from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from app.enums import BoissonContenance

class BoissonBase(BaseModel):
    nomBoisson: str
    contenance: BoissonContenance
    prixVente: float
    stock: Optional[int] = 0

class BoissonCreate(BoissonBase):
    pass

class BoissonUpdate(BaseModel):
    nomBoisson: Optional[str] = None
    contenance: Optional[BoissonContenance] = None
    prixVente: Optional[float] = None
    stock: Optional[int] = None

class BoissonResponse(BoissonBase):
    id: UUID
    restaurantId: UUID
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)


from app.schemas.menu import MenuBoissonFamilleResponse, MenuBoissonImageResponse

class BoissonWithFamilyAndImagesResponse(BaseModel):
    boisson: BoissonResponse
    famille: Optional[MenuBoissonFamilleResponse] = None
    images: List[MenuBoissonImageResponse] = []

    model_config = ConfigDict(from_attributes=True)
