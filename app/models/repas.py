from datetime import datetime
import uuid
from sqlalchemy import String, DateTime, ForeignKey, Float, func, Column
from sqlalchemy import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant

class Repas(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurantId = Column(UUID(as_uuid=True), ForeignKey("restaurant.id"))
    nomRepas = Column(String(255))
    prix = Column(Float)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    restaurant = relationship("Restaurant", back_populates="repas")
