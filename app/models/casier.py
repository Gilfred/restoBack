from datetime import datetime
import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, func, Enum, Column
from sqlalchemy import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.enums import CasierType

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant
    from app.models.appro_boisson import ApproBoisson

class Casier(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    typeCasier = Column(Enum(CasierType))
    restaurantId = Column(UUID(as_uuid=True), ForeignKey("restaurant.id"))
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    restaurant = relationship("Restaurant", back_populates="casiers")
    approBoissons = relationship("ApproBoisson", back_populates="casier")
