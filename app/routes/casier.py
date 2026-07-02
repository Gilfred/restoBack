from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_session
from app.schemas.casier import CasierResponse, CasierCreate
from app.services import casier_service
from app.dependencies import get_current_user, check_permissions, get_user_restaurant_id

router = APIRouter()

@router.get("/", response_model=List[CasierResponse])
def read_casiers(
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    current_user = Depends(check_permissions("view_menu"))
):
    return casier_service.get_casiers(db, restaurant_id)

@router.post("/", response_model=CasierResponse)
def create_casier(
    casier_data: CasierCreate,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    current_user = Depends(check_permissions("manage_staff"))
):
    return casier_service.create_casier(db, casier_data, restaurant_id)
