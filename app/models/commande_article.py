from datetime import datetime
import uuid
from sqlalchemy import DateTime, ForeignKey, Float, Integer, func, Column, Boolean
from sqlalchemy import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.commande import Commande

class CommandeArticle(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    commandeId = Column(UUID(as_uuid=True), ForeignKey("commande.id"))
    boissonId = Column(UUID(as_uuid=True), ForeignKey("boisson.id"))
    repasId = Column(UUID(as_uuid=True), ForeignKey("repas.id"))
    qte = Column(Integer)
    prixUnitaire = Column(Float)
    sousTotal = Column(Float)
    isActive = Column(Boolean, default=True, nullable=False)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    commande = relationship("Commande", back_populates="articles")
