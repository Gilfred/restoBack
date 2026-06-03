from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_session
from app.schemas.casier import CasierResponse, CasierCreate
from app.services import casier_service
from app.dependencies import get_current_user

router = APIRouter()

@router.get("/{restaurant_id}", response_model=List[CasierResponse])
def read_casiers(
    restaurant_id: UUID,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return casier_service.get_casiers(db, restaurant_id)

@router.post("/", response_model=CasierResponse)
def create_casier(
    casier_data: CasierCreate,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return casier_service.create_casier(db, casier_data)
