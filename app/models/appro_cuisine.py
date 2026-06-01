from datetime import datetime
import uuid
from sqlalchemy import DateTime, ForeignKey, Float, func, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.condiment import Condiment
    from app.models.unite import Unite

class ApproCuisine(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    condimentId = Column(UUID(as_uuid=True), ForeignKey("condiment.id"))
    uniteId = Column(UUID(as_uuid=True), ForeignKey("unite.id"))
    prix = Column(Float)
    qte = Column(Float)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    condiment = relationship("Condiment", back_populates="approCuisines")
    unite = relationship("Unite", back_populates="approCuisines")
