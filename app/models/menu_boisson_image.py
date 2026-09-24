import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class MenuBoissonImage(Base):
    __tablename__ = "menuboissonimage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    menuBoissonFamilleId = Column(UUID(as_uuid=True), ForeignKey("menuboissonfamille.id"), nullable=False)
    url = Column(String(500), nullable=False)
    createdAt = Column(DateTime, default=func.now(), nullable=False)
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    menuBoissonFamille = relationship("MenuBoissonFamille", back_populates="images")
