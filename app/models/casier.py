import uuid
from sqlalchemy import column, String
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from app.enums import CasierType

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant
    from app.models.appro_boisson import ApproBoisson

class Casier(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    typeCasier: Mapped[CasierType] = mapped_column(Enum(CasierType))
    restaurantId: Mapped[int] = mapped_column(ForeignKey("restaurant.id"))
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="casiers")
    approBoissons: Mapped[List["ApproBoisson"]] = relationship("ApproBoisson", back_populates="casier")
