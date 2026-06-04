from datetime import datetime
import uuid
from sqlalchemy import Column, DateTime, ForeignKey, func, UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class RestaurantActivationHistory(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurantId = Column(UUID(as_uuid=True), ForeignKey("restaurant.id"), nullable=False)
    requestedAt = Column(DateTime, default=func.now(), nullable=False)

    restaurant = relationship("Restaurant")
