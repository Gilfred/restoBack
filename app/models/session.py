from datetime import datetime
import uuid
from sqlalchemy import String, DateTime, ForeignKey, func, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

class Session(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expiresAt = Column(DateTime)
    token = Column(String(255), unique=True)
    userId = Column(UUID(as_uuid=True), ForeignKey("user.id"))
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="sessions")
