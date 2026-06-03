from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_session
from app.schemas.restaurant import RestaurantCreate, RestaurantResponse
from app.services import restaurant_service, auth_service

router = APIRouter()

def get_current_user(request: Request, db: Session = Depends(get_session)):
    token = request.cookies.get("session_token")
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = auth_service.get_session_by_token(db, token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")

    return session.user

@router.post("/", response_model=RestaurantResponse)
def create_new_restaurant(
    restaurant_data: RestaurantCreate,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return restaurant_service.create_restaurant(db, restaurant_data, current_user.id)
