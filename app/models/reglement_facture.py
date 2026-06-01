from datetime import datetime
import uuid
from sqlalchemy import DateTime, ForeignKey, Float, func, Column
from app.db.guid import GUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant
    from app.models.commande import Commande
    from app.models.methode_payment import MethodePayment

class ReglementFacture(Base):
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    restaurantId = Column(GUID(), ForeignKey("restaurant.id"))
    commandeId = Column(GUID(), ForeignKey("commande.id"))
    montant = Column(Float)
    methodeId = Column(GUID(), ForeignKey("methodepayment.id"))
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    restaurant = relationship("Restaurant", back_populates="reglementFactures")
    commande = relationship("Commande", back_populates="reglementFactures")
    methode = relationship("MethodePayment", back_populates="reglementFactures")
