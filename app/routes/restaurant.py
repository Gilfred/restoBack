from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from app.database import get_session
from app.schemas.restaurant import RestaurantCreate, RestaurantResponse
from app.services import restaurant_service
from app.dependencies import get_current_user

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
