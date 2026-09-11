from datetime import datetime
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer, Enum, func, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.enums import MenuCategorieNom

if TYPE_CHECKING:
    from app.models.menu_famille import MenuFamille
    from app.models.menu_repas import MenuRepas

class MenuCategorie(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    menuFamilleId = Column(UUID(as_uuid=True), ForeignKey("menufamille.id"), nullable=True)
    nom = Column(Enum(MenuCategorieNom), nullable=False)
    ordre = Column(Integer, default=0)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    menuFamille = relationship("MenuFamille", back_populates="categories")
    repasList = relationship("MenuRepas", back_populates="menuCategorie", cascade="all, delete-orphan")
