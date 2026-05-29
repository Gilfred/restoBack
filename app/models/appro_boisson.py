import uuid
from sqlalchemy import column, String
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Float, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.boisson import Boisson
    from app.models.casier import Casier

class ApproBoisson(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    boissonId: Mapped[int] = mapped_column(ForeignKey("boisson.id"))
    casierId: Mapped[int] = mapped_column(ForeignKey("casier.id"))
    prixAchat: Mapped[float] = mapped_column(Float)
    nbreCasier: Mapped[int] = mapped_column(Integer)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    boisson: Mapped["Boisson"] = relationship("Boisson", back_populates="approBoissons")
    casier: Mapped["Casier"] = relationship("Casier", back_populates="approBoissons")
