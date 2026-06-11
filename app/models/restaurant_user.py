import uuid
from sqlalchemy import Column, ForeignKey, DateTime, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.enums import UserRestaurantStatus

class RestaurantUser(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    userId = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, unique=True)
    restaurantId = Column(UUID(as_uuid=True), ForeignKey("restaurant.id"), nullable=False)
    roleId = Column(UUID(as_uuid=True), ForeignKey("role.id"), nullable=True)
    status = Column(SQLEnum(UserRestaurantStatus), default=UserRestaurantStatus.PENDING, nullable=False)
    createdAt = Column(DateTime, default=func.now(), nullable=False)
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", foreign_keys=[userId], back_populates="restaurant_user")
    restaurant = relationship("Restaurant", foreign_keys=[restaurantId])
    role = relationship("Role", foreign_keys=[roleId])
