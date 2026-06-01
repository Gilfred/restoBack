from datetime import datetime
import uuid
from sqlalchemy import String, DateTime, ForeignKey, func, Column
from app.db.guid import GUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

class Account(Base):
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    provider = Column(String(255))
    userId = Column(GUID(), ForeignKey("user.id"))
    providerAccountId = Column(String(255))
    password = Column(String(255))
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="accounts")
