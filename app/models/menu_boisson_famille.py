import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class MenuBoissonFamille(Base):
    __tablename__ = "menuboissonfamille"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurantId = Column(UUID(as_uuid=True), ForeignKey("restaurant.id"), nullable=False)
    nom = Column(String(255), nullable=False)
    createdAt = Column(DateTime, default=func.now(), nullable=False)
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    restaurant = relationship("Restaurant", back_populates="menuBoissonFamilles")
    images = relationship("MenuBoissonImage", back_populates="menuBoissonFamille", cascade="all, delete-orphan")
    boissons = relationship("MenuBoisson", back_populates="menuBoissonFamille", cascade="all, delete-orphan")
