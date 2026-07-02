from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_session
from app.schemas.unite import UniteResponse, UniteCreate
from app.services import unite_service
from app.dependencies import get_user_restaurant_id, require_superadmin, get_current_user

router = APIRouter()

@router.get("/", response_model=List[UniteResponse])
def read_unites(
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    current_user = Depends(get_current_user) # Accessible to all restaurant employees
):
    return unite_service.get_unites(db, restaurant_id)

@router.post("/", response_model=UniteResponse)
def create_unite(
    unite_data: UniteCreate,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    current_user = Depends(require_superadmin) # Only SUPERADMIN can create units
):
    return unite_service.create_unite(db, unite_data, restaurant_id)
