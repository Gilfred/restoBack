from datetime import datetime
import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, func, Column
from app.db.guid import GUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant
    from app.models.appro_cuisine import ApproCuisine

class Condiment(Base):
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    restaurantId = Column(GUID(), ForeignKey("restaurant.id"))
    nomcondiment = Column(String(255))
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    restaurant = relationship("Restaurant", back_populates="condiments")
    approCuisines = relationship("ApproCuisine", back_populates="condiment")
