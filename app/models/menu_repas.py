from datetime import datetime
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer, func, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.menu_categorie import MenuCategorie
    from app.models.repas import Repas

class MenuRepas(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    menuCategorieId = Column(UUID(as_uuid=True), ForeignKey("menucategorie.id"), nullable=True)
    repasId = Column(UUID(as_uuid=True), ForeignKey("repas.id"), nullable=True)
    ordre = Column(Integer, default=0)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    menuCategorie = relationship("MenuCategorie", back_populates="repasList")
    repas = relationship("Repas")
