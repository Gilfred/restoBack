from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.permission import Permission

class Role(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True, unique=True)
    description: Mapped[str | None] = mapped_column(String(255))
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    users: Mapped[List["User"]] = relationship(
        "User", secondary="userrole", back_populates="roles"
    )
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission", secondary="rolepermission", back_populates="roles"
    )
