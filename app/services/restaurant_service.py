from datetime import datetime
from sqlalchemy.orm import Session
from app.models.restaurant import Restaurant
from app.models.restaurant_activation_history import RestaurantActivationHistory
from app.schemas.restaurant import RestaurantCreate
from app.enums import ActivationStatus
from uuid import UUID

def create_restaurant(db: Session, restaurant_data: RestaurantCreate, owner_id: UUID):
    db_restaurant = Restaurant(
        **restaurant_data.model_dump(),
        ownerId=owner_id,
        isActive=False
    )
    db.add(db_restaurant)
    db.flush() # To get the id

    # Automatically create an activation request
    history = RestaurantActivationHistory(
        restaurantId=db_restaurant.id,
        status=ActivationStatus.PENDING
    )
    db.add(history)

    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant

def get_restaurant(db: Session, restaurant_id: UUID):
    return db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()

def get_all_restaurants(db: Session):
    return db.query(Restaurant).filter(Restaurant.isActive == True).all()

def get_inactive_restaurants(db: Session):
    return db.query(Restaurant).filter(Restaurant.isActive == False).all()

def activate_restaurant(db: Session, restaurant_id: UUID):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        return None

    restaurant.isActive = True

    # Find the pending request and mark it as activated
    history = db.query(RestaurantActivationHistory).filter(
        RestaurantActivationHistory.restaurantId == restaurant_id,
        RestaurantActivationHistory.status == ActivationStatus.PENDING
    ).first()

    if history:
        history.status = ActivationStatus.ACTIVATED
        history.processedAt = datetime.now()
    else:
        # If no pending request (should not happen with automatic creation), create one
        history = RestaurantActivationHistory(
            restaurantId=restaurant_id,
            status=ActivationStatus.ACTIVATED,
            processedAt=datetime.now()
        )
        db.add(history)

    db.commit()
    db.refresh(restaurant)
    return restaurant

def get_activation_history(db: Session):
    return db.query(RestaurantActivationHistory).all()
