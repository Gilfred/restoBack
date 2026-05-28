from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from app.enums import MethodePaiementEnum

if TYPE_CHECKING:
    from app.models.reglement_facture import ReglementFacture

class MethodePayment(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    nomMethode: Mapped[MethodePaiementEnum] = mapped_column(Enum(MethodePaiementEnum))
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    reglementFactures: Mapped[List["ReglementFacture"]] = relationship("ReglementFacture", back_populates="methode")
