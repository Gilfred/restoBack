from datetime import datetime
import uuid
from sqlalchemy import ForeignKey, DateTime, func, Column
from sqlalchemy import UUID
from app.db.base_class import Base

class UserRole(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    userId = Column(UUID(as_uuid=True), ForeignKey("user.id"))
    roleId = Column(UUID(as_uuid=True), ForeignKey("role.id"))
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

class RolePermission(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roleId = Column(UUID(as_uuid=True), ForeignKey("role.id"))
    permissionId = Column(UUID(as_uuid=True), ForeignKey("permission.id"))
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())
