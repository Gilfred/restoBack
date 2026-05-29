from datetime import datetime
import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Boolean, func, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.restaurant import Restaurant
    from app.models.session import Session
    from app.models.account import Account
    from app.models.commande import Commande

class User(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255))
    email = Column(String(255), index=True, unique=True)
    emailVerified = Column(DateTime)
    image = Column(String(255))
    password = Column(String(255))
    restaurantId = Column(UUID(as_uuid=True), ForeignKey("restaurant.id"))
    isActive = Column(Boolean, default=True)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    roles = relationship(
        "Role", secondary="userrole", back_populates="users"
    )
    restaurant = relationship(
        "Restaurant",
        back_populates="staff",
        foreign_keys=[restaurantId]
    )
    owned_restaurants = relationship(
        "Restaurant",
        back_populates="owner",
        foreign_keys="[Restaurant.ownerId]"
    )
    sessions = relationship("Session", back_populates="user")
    accounts = relationship("Account", back_populates="user")
    commandes = relationship("Commande", back_populates="user")
