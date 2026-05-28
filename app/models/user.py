from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.restaurant import Restaurant
    from app.models.session import Session
    from app.models.account import Account
    from app.models.commande import Commande

class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), index=True, unique=True)
    emailVerified: Mapped[datetime | None] = mapped_column(DateTime)
    image: Mapped[str | None] = mapped_column(String(255))
    password: Mapped[str] = mapped_column(String(255))
    restaurantId: Mapped[int | None] = mapped_column(ForeignKey("restaurant.id"))
    isActive: Mapped[bool] = mapped_column(Boolean, default=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    roles: Mapped[List["Role"]] = relationship(
        "Role", secondary="userrole", back_populates="users"
    )
    restaurant: Mapped[Optional["Restaurant"]] = relationship(
        "Restaurant",
        back_populates="staff",
        foreign_keys=[restaurantId]
    )
    owned_restaurants: Mapped[List["Restaurant"]] = relationship(
        "Restaurant",
        back_populates="owner",
        foreign_keys="[Restaurant.ownerId]"
    )
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="user")
    accounts: Mapped[List["Account"]] = relationship("Account", back_populates="user")
    commandes: Mapped[List["Commande"]] = relationship("Commande", back_populates="user")
