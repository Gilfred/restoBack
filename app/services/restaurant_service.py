from sqlalchemy.orm import Session
from app.models.restaurant import Restaurant
from app.models.restaurant_activation_history import RestaurantActivationHistory
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

def get_all_restaurants(db: Session):
    return db.query(Restaurant).all()

def get_inactive_restaurants(db: Session):
    return db.query(Restaurant).filter(Restaurant.isActive == False).all()

def activate_restaurant(db: Session, restaurant_id: UUID):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        return None

    restaurant.isActive = True

    # Create history record
    history = RestaurantActivationHistory(restaurantId=restaurant_id)
    db.add(history)

    db.commit()
    db.refresh(restaurant)
    return restaurant
