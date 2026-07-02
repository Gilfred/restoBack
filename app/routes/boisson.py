from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_session
from app.schemas.boisson import BoissonCreate, BoissonUpdate, BoissonResponse
from app.services import boisson_service
from app.dependencies import get_user_restaurant_id, require_admin

router = APIRouter()

@router.post("/", response_model=BoissonResponse, status_code=status.HTTP_201_CREATED)
def create_boisson(
    boisson_data: BoissonCreate,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    return boisson_service.create_boisson(db, boisson_data, restaurant_id)

@router.get("/", response_model=List[BoissonResponse])
def list_boissons(
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    return boisson_service.get_boissons(db, restaurant_id)

@router.get("/{boisson_id}", response_model=BoissonResponse)
def get_boisson(
    boisson_id: UUID,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    db_boisson = boisson_service.get_boisson(db, boisson_id, restaurant_id)
    if not db_boisson:
        raise HTTPException(status_code=404, detail="Boisson non trouvée")
    return db_boisson

@router.put("/{boisson_id}", response_model=BoissonResponse)
def update_boisson(
    boisson_id: UUID,
    boisson_data: BoissonUpdate,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    db_boisson = boisson_service.update_boisson(db, boisson_id, boisson_data, restaurant_id)
    if not db_boisson:
        raise HTTPException(status_code=404, detail="Boisson non trouvée")
    return db_boisson

@router.delete("/{boisson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_boisson(
    boisson_id: UUID,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    if not boisson_service.delete_boisson(db, boisson_id, restaurant_id):
        raise HTTPException(status_code=404, detail="Boisson non trouvée")
    return None
