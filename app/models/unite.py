from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from app.enums import UniteType

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant
    from app.models.appro_cuisine import ApproCuisine

class Unite(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    unite: Mapped[UniteType] = mapped_column(Enum(UniteType))
    restaurantId: Mapped[int] = mapped_column(ForeignKey("restaurant.id"))
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="unites")
    approCuisines: Mapped[List["ApproCuisine"]] = relationship("ApproCuisine", back_populates="unite")
