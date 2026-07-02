from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_session
from app.schemas.condiment import CondimentCreate, CondimentUpdate, CondimentResponse
from app.services import condiment_service
from app.dependencies import get_user_restaurant_id, check_permissions

router = APIRouter()

@router.post("/", response_model=CondimentResponse)
def create_condiment(
    condiment_data: CondimentCreate,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    current_user = Depends(check_permissions("manage_staff")) # Only staff managers can modify menu items
):
    return condiment_service.create_condiment(db, condiment_data, restaurant_id)

@router.get("/", response_model=List[CondimentResponse])
def list_condiments(
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    current_user = Depends(check_permissions("view_menu"))
):
    return condiment_service.get_condiments(db, restaurant_id)

@router.get("/{condiment_id}", response_model=CondimentResponse)
def get_condiment(
    condiment_id: UUID,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    current_user = Depends(check_permissions("view_menu"))
):
    db_condiment = condiment_service.get_condiment(db, condiment_id, restaurant_id)
    if not db_condiment:
        raise HTTPException(status_code=404, detail="Condiment not found")
    return db_condiment

@router.put("/{condiment_id}", response_model=CondimentResponse)
def update_condiment(
    condiment_id: UUID,
    condiment_data: CondimentUpdate,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    current_user = Depends(check_permissions("manage_staff"))
):
    db_condiment = condiment_service.update_condiment(db, condiment_id, condiment_data, restaurant_id)
    if not db_condiment:
        raise HTTPException(status_code=404, detail="Condiment not found")
    return db_condiment

@router.delete("/{condiment_id}")
def delete_condiment(
    condiment_id: UUID,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    current_user = Depends(check_permissions("manage_staff"))
):
    if not condiment_service.delete_condiment(db, condiment_id, restaurant_id):
        raise HTTPException(status_code=404, detail="Condiment not found")
    return {"message": "Condiment deleted"}
