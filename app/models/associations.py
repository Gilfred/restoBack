from datetime import datetime
import uuid
from sqlalchemy import ForeignKey, DateTime, func, Column
from app.db.base_class import Base
from app.db.guid import GUID

class UserRole(Base):
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    userId = Column(GUID(), ForeignKey("user.id"))
    roleId = Column(GUID(), ForeignKey("role.id"))
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

class RolePermission(Base):
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    roleId = Column(GUID(), ForeignKey("role.id"))
    permissionId = Column(GUID(), ForeignKey("permission.id"))
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())
