from datetime import datetime
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Integer, func, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant
    from app.models.menu_famille_image import MenuFamilleImage
    from app.models.menu_categorie import MenuCategorie

class MenuFamille(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurantId = Column(UUID(as_uuid=True), ForeignKey("restaurant.id"), nullable=True)
    nom = Column(String(255), nullable=False)
    ordre = Column(Integer, default=0)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    restaurant = relationship("Restaurant", back_populates="menuFamilles")
    images = relationship("MenuFamilleImage", back_populates="menuFamille", cascade="all, delete-orphan")
    categories = relationship("MenuCategorie", back_populates="menuFamille", cascade="all, delete-orphan")
