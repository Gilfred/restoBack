from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base

class UserRole(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    userId: Mapped[int] = mapped_column(ForeignKey("user.id"))
    roleId: Mapped[int] = mapped_column(ForeignKey("role.id"))
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class RolePermission(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    roleId: Mapped[int] = mapped_column(ForeignKey("role.id"))
    permissionId: Mapped[int] = mapped_column(ForeignKey("permission.id"))
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
