from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class RestaurantBase(BaseModel):
    name: str
    address: str
    phone: str

class RestaurantCreate(RestaurantBase):
    pass

class RestaurantResponse(RestaurantBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    ownerId: UUID
    isActive: bool
    createdAt: datetime
    updatedAt: datetime
