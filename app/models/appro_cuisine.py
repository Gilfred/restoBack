from datetime import datetime
import uuid
from sqlalchemy import DateTime, ForeignKey, Float, func, Column
from app.db.guid import GUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.condiment import Condiment
    from app.models.unite import Unite

class ApproCuisine(Base):
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    condimentId = Column(GUID(), ForeignKey("condiment.id"))
    uniteId = Column(GUID(), ForeignKey("unite.id"))
    prix = Column(Float)
    qte = Column(Float)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    condiment = relationship("Condiment", back_populates="approCuisines")
    unite = relationship("Unite", back_populates="approCuisines")
