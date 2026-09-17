from datetime import datetime
import re
import unicodedata
from sqlalchemy.orm import Session, joinedload
from app.models.restaurant import Restaurant
from app.models.user import User
from app.models.restaurant_user import RestaurantUser
from app.models.restaurant_activation_history import RestaurantActivationHistory
from app.schemas.restaurant import RestaurantCreate
from app.enums import ActivationStatus, UserRestaurantStatus
from uuid import UUID

def generate_unique_slug(db: Session, name: str, provided_slug: str = None) -> str:
    if provided_slug:
        base_slug = provided_slug.lower().strip()
    else:
        # Normalize accent characters and convert to lower
        text = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')
        text = text.lower().strip()
        text = re.sub(r'[\s\-_]+', '-', text)
        base_slug = re.sub(r'[^a-z0-9\-]', '', text).strip('-')

    if not base_slug:
        base_slug = "restaurant"

    slug = base_slug
    counter = 1
    while db.query(Restaurant).filter(Restaurant.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug

def create_restaurant(db: Session, restaurant_data: RestaurantCreate, owner_id: UUID):
    data_dict = restaurant_data.model_dump()
    provided_slug = data_dict.pop("slug", None)
    slug = generate_unique_slug(db, restaurant_data.name, provided_slug)

    db_restaurant = Restaurant(
        **data_dict,
        slug=slug,
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

def get_restaurant_staff(db: Session, restaurant_id: UUID):
    from app.models.role import Role
    results = db.query(RestaurantUser).options(
        joinedload(RestaurantUser.user),
        joinedload(RestaurantUser.role).joinedload(Role.permissions)
    ).filter(
        RestaurantUser.restaurantId == restaurant_id,
        RestaurantUser.status == UserRestaurantStatus.ACTIVE
    ).all()

    # Flatten the result to match StaffResponse
    staff = []
    for ru in results:
        u = ru.user
        u.role = ru.role
        u.status = ru.status
        staff.append(u)
    return staff
