from datetime import datetime
import uuid
from sqlalchemy import Column, DateTime, ForeignKey, func, UUID, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.enums import ActivationStatus

class RestaurantActivationHistory(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurantId = Column(UUID(as_uuid=True), ForeignKey("restaurant.id"), nullable=False)
    status = Column(Enum(ActivationStatus), default=ActivationStatus.PENDING, nullable=False)
    requestedAt = Column(DateTime, default=func.now(), nullable=False)
    processedAt = Column(DateTime)

    restaurant = relationship("Restaurant")
