from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.enums import ActivationStatus

class RestaurantActivationHistoryBase(BaseModel):
    restaurantId: UUID
    status: ActivationStatus

class RestaurantActivationHistoryCreate(RestaurantActivationHistoryBase):
    pass

class RestaurantActivationHistoryResponse(RestaurantActivationHistoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    requestedAt: datetime
    processedAt: Optional[datetime] = None
