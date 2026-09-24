import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Column, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.boisson import Boisson
    from app.models.menu_boisson_famille import MenuBoissonFamille

class MenuBoisson(Base):
    __tablename__ = "menuboisson"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    menuBoissonFamilleId = Column(UUID(as_uuid=True), ForeignKey("menuboissonfamille.id"), nullable=False)
    boissonId = Column(UUID(as_uuid=True), ForeignKey("boisson.id"), nullable=False)
    createdAt = Column(DateTime, default=func.now(), nullable=False)
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    menuBoissonFamille = relationship("MenuBoissonFamille", back_populates="boissons")
    boisson = relationship("Boisson")
