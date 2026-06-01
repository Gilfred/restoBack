from datetime import datetime
import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Float, Integer, func, Enum, Column
from sqlalchemy import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.enums import BoissonContenance

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant
    from app.models.appro_boisson import ApproBoisson

class Boisson(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurantId = Column(UUID(as_uuid=True), ForeignKey("restaurant.id"))
    nomBoisson = Column(String(255))
    contenance = Column(Enum(BoissonContenance))
    prixVente = Column(Float)
    stock = Column(Integer, default=0)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    restaurant = relationship("Restaurant", back_populates="boissons")
    approBoissons = relationship("ApproBoisson", back_populates="boisson")
