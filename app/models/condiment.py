import uuid
from sqlalchemy import column, String
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant
    from app.models.appro_cuisine import ApproCuisine

class Condiment(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    restaurantId: Mapped[int] = mapped_column(ForeignKey("restaurant.id"))
    nomcondiment: Mapped[str] = mapped_column(String(255))
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="condiments")
    approCuisines: Mapped[List["ApproCuisine"]] = relationship("ApproCuisine", back_populates="condiment")
