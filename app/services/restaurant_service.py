from sqlalchemy.orm import Session
from app.models.restaurant import Restaurant
from app.schemas.restaurant import RestaurantCreate
from uuid import UUID

def create_restaurant(db: Session, restaurant_data: RestaurantCreate, owner_id: UUID):
    db_restaurant = Restaurant(
        **restaurant_data.model_dump(),
        ownerId=owner_id,
        isActive=False
    )
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant

def get_restaurant(db: Session, restaurant_id: UUID):
    return db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
