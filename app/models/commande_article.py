from datetime import datetime
import uuid
from sqlalchemy import DateTime, ForeignKey, Float, Integer, func, Column
from app.db.guid import GUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.commande import Commande

class CommandeArticle(Base):
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    commandeId = Column(GUID(), ForeignKey("commande.id"))
    boissonId = Column(GUID(), ForeignKey("boisson.id"))
    repasId = Column(GUID(), ForeignKey("repas.id"))
    qte = Column(Integer)
    prixUnitaire = Column(Float)
    sousTotal = Column(Float)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    commande = relationship("Commande", back_populates="articles")
