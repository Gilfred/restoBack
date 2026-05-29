import uuid
from sqlalchemy import column, String
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Float, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.commande import Commande

class CommandeArticle(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    commandeId: Mapped[int] = mapped_column(ForeignKey("commande.id"))
    boissonId: Mapped[int | None] = mapped_column(ForeignKey("boisson.id"))
    repasId: Mapped[int | None] = mapped_column(ForeignKey("repas.id"))
    qte: Mapped[int] = mapped_column(Integer)
    prixUnitaire: Mapped[float] = mapped_column(Float)
    sousTotal: Mapped[float] = mapped_column(Float)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    commande: Mapped["Commande"] = relationship("Commande", back_populates="articles")
