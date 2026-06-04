from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class RestaurantActivationHistoryBase(BaseModel):
    restaurantId: UUID

class RestaurantActivationHistoryCreate(RestaurantActivationHistoryBase):
    pass

class RestaurantActivationHistoryResponse(RestaurantActivationHistoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    requestedAt: datetime
