import uuid
from sqlalchemy import column, String
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.boisson import Boisson
    from app.models.repas import Repas
    from app.models.condiment import Condiment
    from app.models.commande import Commande
    from app.models.reglement_facture import ReglementFacture
    from app.models.casier import Casier
    from app.models.unite import Unite

class Restaurant(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(255))
    ownerId: Mapped[int] = mapped_column(ForeignKey("user.id"))
    isActive: Mapped[bool] = mapped_column(Boolean, default=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    owner: Mapped["User"] = relationship(
        "User",
        back_populates="owned_restaurants",
        foreign_keys=[ownerId]
    )
    staff: Mapped[List["User"]] = relationship(
        "User",
        back_populates="restaurant",
        foreign_keys="[User.restaurantId]"
    )
    boissons: Mapped[List["Boisson"]] = relationship("Boisson", back_populates="restaurant")
    repas: Mapped[List["Repas"]] = relationship("Repas", back_populates="restaurant")
    condiments: Mapped[List["Condiment"]] = relationship("Condiment", back_populates="restaurant")
    commandes: Mapped[List["Commande"]] = relationship("Commande", back_populates="restaurant")
    reglementFactures: Mapped[List["ReglementFacture"]] = relationship("ReglementFacture", back_populates="restaurant")
    casiers: Mapped[List["Casier"]] = relationship("Casier", back_populates="restaurant")
    unites: Mapped[List["Unite"]] = relationship("Unite", back_populates="restaurant")
