from datetime import datetime
import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Boolean, func, Column
from app.db.guid import GUID
from sqlalchemy.orm import relationship
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
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    phone = Column(String(255), nullable=False)
    ownerId = Column(GUID(), ForeignKey("user.id", use_alter=True, name="fk_restaurant_owner"), nullable=False)
    isActive = Column(Boolean, default=True, nullable=False)
    createdAt = Column(DateTime, default=func.now(), nullable=False)
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    owner = relationship(
        "User",
        back_populates="owned_restaurants",
        foreign_keys=[ownerId]
    )
    staff = relationship(
        "User",
        back_populates="restaurant",
        foreign_keys="[User.restaurantId]"
    )
    boissons = relationship("Boisson", back_populates="restaurant")
    repas = relationship("Repas", back_populates="restaurant")
    condiments = relationship("Condiment", back_populates="restaurant")
    commandes = relationship("Commande", back_populates="restaurant")
    reglementFactures = relationship("ReglementFacture", back_populates="restaurant")
    casiers = relationship("Casier", back_populates="restaurant")
    unites = relationship("Unite", back_populates="restaurant")
