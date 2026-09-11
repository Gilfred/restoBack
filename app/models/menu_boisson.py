from datetime import datetime
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Integer, func, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.boisson import Boisson

class MenuBoisson(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    boissonId = Column(UUID(as_uuid=True), ForeignKey("boisson.id"), nullable=True)
    ordre = Column(Integer, default=0)
    imageUrl = Column(String(500), nullable=True)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    boisson = relationship("Boisson")
