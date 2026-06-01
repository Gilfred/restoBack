from datetime import datetime
import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime, func, Enum, Column
from sqlalchemy import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.enums import MethodePaiementEnum

if TYPE_CHECKING:
    from app.models.reglement_facture import ReglementFacture

class MethodePayment(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nomMethode = Column(Enum(MethodePaiementEnum))
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    reglementFactures = relationship("ReglementFacture", back_populates="methode")
