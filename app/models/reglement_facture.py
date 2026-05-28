from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant
    from app.models.commande import Commande
    from app.models.methode_payment import MethodePayment

class ReglementFacture(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    restaurantId: Mapped[int] = mapped_column(ForeignKey("restaurant.id"))
    commandeId: Mapped[int] = mapped_column(ForeignKey("commande.id"))
    montant: Mapped[float] = mapped_column(Float)
    methodeId: Mapped[int] = mapped_column(ForeignKey("methodepayment.id"))
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="reglementFactures")
    commande: Mapped["Commande"] = relationship("Commande", back_populates="reglementFactures")
    methode: Mapped["MethodePayment"] = relationship("MethodePayment", back_populates="reglementFactures")
