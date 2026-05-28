from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Float, Integer, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from app.enums import BoissonContenance

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant
    from app.models.appro_boisson import ApproBoisson

class Boisson(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    restaurantId: Mapped[int] = mapped_column(ForeignKey("restaurant.id"))
    nomBoisson: Mapped[str] = mapped_column(String(255))
    contenance: Mapped[BoissonContenance] = mapped_column(Enum(BoissonContenance))
    prixVente: Mapped[float] = mapped_column(Float)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="boissons")
    approBoissons: Mapped[List["ApproBoisson"]] = relationship("ApproBoisson", back_populates="boisson")
