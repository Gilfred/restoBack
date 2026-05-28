from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

class Account(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(255))
    userId: Mapped[int] = mapped_column(ForeignKey("user.id"))
    providerAccountId: Mapped[str] = mapped_column(String(255))
    password: Mapped[str | None] = mapped_column(String(255))
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="accounts")
