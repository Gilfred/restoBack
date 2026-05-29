import uuid
from sqlalchemy import column, String
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant

class Repas(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    restaurantId: Mapped[int] = mapped_column(ForeignKey("restaurant.id"))
    nomRepas: Mapped[str] = mapped_column(String(255))
    prix: Mapped[float] = mapped_column(Float)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="repas")
