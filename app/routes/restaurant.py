from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_session
from app.schemas.restaurant import RestaurantCreate, RestaurantResponse
from app.schemas.restaurant_activation_history import RestaurantActivationHistoryResponse
from app.schemas.auth import UserResponse
from app.services import restaurant_service
from app.dependencies import get_current_user, require_superadmin, check_permissions
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=RestaurantResponse)
def create_new_restaurant(
    restaurant_data: RestaurantCreate,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return restaurant_service.create_restaurant(db, restaurant_data, current_user.id)

@router.get("/", response_model=List[RestaurantResponse])
def list_restaurants(
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return restaurant_service.get_all_restaurants(db)

@router.get("/inactive", response_model=List[RestaurantResponse])
def list_inactive_restaurants(
    db: Session = Depends(get_session),
    current_user = Depends(require_superadmin)
):
    return restaurant_service.get_inactive_restaurants(db)

@router.post("/{restaurant_id}/activate", response_model=RestaurantResponse)
def activate_restaurant(
    restaurant_id: UUID,
    db: Session = Depends(get_session),
    current_user = Depends(require_superadmin)
):
    restaurant = restaurant_service.activate_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant

@router.get("/activation-history", response_model=List[RestaurantActivationHistoryResponse])
def get_activation_history(
    db: Session = Depends(get_session),
    current_user = Depends(require_superadmin)
):
    return restaurant_service.get_activation_history(db)

@router.get("/{restaurant_id}/staff", response_model=List[UserResponse])
def get_restaurant_staff(
    restaurant_id: UUID,
    db: Session = Depends(get_session),
    current_user = Depends(check_permissions("manage_staff"))
):
    # If not SUPERADMIN, ensure ADMIN is only looking at their own restaurant
    is_superadmin = any(role.name.upper() == "SUPERADMIN" for role in current_user.roles)
    if not is_superadmin and current_user.restaurantId != restaurant_id:
        raise HTTPException(status_code=403, detail="Vous ne pouvez consulter que le personnel de votre propre restaurant")

    return db.query(User).filter(User.restaurantId == restaurant_id).all()
