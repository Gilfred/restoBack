import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Integer, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.menu_famille import MenuFamille

class MenuFamilleImage(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    familleId = Column(
        UUID(as_uuid=True),
        ForeignKey("menufamille.id"),
        nullable=False
    )
    imageUrl = Column(String(500), nullable=False)
    ordre = Column(Integer, default=0)

    menuFamille = relationship("MenuFamille", back_populates="images")
