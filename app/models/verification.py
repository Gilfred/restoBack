from datetime import datetime
import uuid
from sqlalchemy import String, DateTime, func, Column
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class Verification(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identifier = Column(String(255))
    value = Column(String(255))
    expiresAt = Column(DateTime)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())
