import uuid
from sqlalchemy import column, String
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.condiment import Condiment
    from app.models.unite import Unite

class ApproCuisine(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    condimentId: Mapped[int] = mapped_column(ForeignKey("condiment.id"))
    uniteId: Mapped[int] = mapped_column(ForeignKey("unite.id"))
    prix: Mapped[float] = mapped_column(Float)
    qte: Mapped[float] = mapped_column(Float)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    condiment: Mapped["Condiment"] = relationship("Condiment", back_populates="approCuisines")
    unite: Mapped["Unite"] = relationship("Unite", back_populates="approCuisines")
