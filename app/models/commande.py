from datetime import datetime
import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Float, func, Enum, Column, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.enums import CommandeStatut

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant
    from app.models.user import User
    from app.models.commande_article import CommandeArticle
    from app.models.reglement_facture import ReglementFacture

class Commande(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurantId = Column(UUID(as_uuid=True), ForeignKey("restaurant.id"))
    numeroCommande = Column(String(255), index=True)
    userId = Column(UUID(as_uuid=True), ForeignKey("user.id"))
    total = Column(Float, default=0.0)
    statut = Column(Enum(CommandeStatut), default=CommandeStatut.PENDING)
    isActive = Column(Boolean, default=True, nullable=False)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    restaurant = relationship("Restaurant", back_populates="commandes")
    user = relationship("User", back_populates="commandes")
    articles = relationship("CommandeArticle", back_populates="commande")
    reglementFactures = relationship("ReglementFacture", back_populates="commande")
