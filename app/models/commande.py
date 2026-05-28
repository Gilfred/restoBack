from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Float, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from app.enums import CommandeStatut

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant
    from app.models.user import User
    from app.models.commande_article import CommandeArticle
    from app.models.reglement_facture import ReglementFacture

class Commande(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    restaurantId: Mapped[int] = mapped_column(ForeignKey("restaurant.id"))
    numeroCommande: Mapped[str] = mapped_column(String(255), index=True)
    userId: Mapped[int] = mapped_column(ForeignKey("user.id"))
    total: Mapped[float] = mapped_column(Float, default=0.0)
    statut: Mapped[CommandeStatut] = mapped_column(Enum(CommandeStatut), default=CommandeStatut.PENDING)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="commandes")
    user: Mapped["User"] = relationship("User", back_populates="commandes")
    articles: Mapped[List["CommandeArticle"]] = relationship("CommandeArticle", back_populates="commande")
    reglementFactures: Mapped[List["ReglementFacture"]] = relationship("ReglementFacture", back_populates="commande")
