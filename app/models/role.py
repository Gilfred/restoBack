from datetime import datetime
import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime, func, Column
from app.db.guid import GUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.permission import Permission

class Role(Base):
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), index=True, unique=True)
    description = Column(String(255))
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    users = relationship(
        "User", secondary="userrole", back_populates="roles"
    )
    permissions = relationship(
        "Permission", secondary="rolepermission", back_populates="roles"
    )
