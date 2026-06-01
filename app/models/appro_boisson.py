from datetime import datetime
import uuid
from sqlalchemy import DateTime, ForeignKey, Float, Integer, func, Column
from sqlalchemy import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.boisson import Boisson
    from app.models.casier import Casier

class ApproBoisson(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    boissonId = Column(UUID(as_uuid=True), ForeignKey("boisson.id"))
    casierId = Column(UUID(as_uuid=True), ForeignKey("casier.id"))
    prixAchat = Column(Float)
    nbreCasier = Column(Integer)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    boisson = relationship("Boisson", back_populates="approBoissons")
    casier = relationship("Casier", back_populates="approBoissons")
