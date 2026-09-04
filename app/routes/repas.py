from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_session
from app.schemas.repas import RepasCreate, RepasUpdate, RepasResponse
from app.services import repas_service
from app.dependencies import get_user_restaurant_id, require_admin, require_manager_cashier

router = APIRouter()

@router.post("/", response_model=RepasResponse, status_code=status.HTTP_201_CREATED)
def create_repas(
    repas_data: RepasCreate,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    return repas_service.create_repas(db, repas_data, restaurant_id)

@router.get("/", response_model=List[RepasResponse])
def list_repas(
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    current_user = Depends(require_manager_cashier)
):
    return repas_service.get_repas_list(db, restaurant_id)

@router.get("/{repas_id}", response_model=RepasResponse)
def get_repas(
    repas_id: UUID,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    db_repas = repas_service.get_repas(db, repas_id, restaurant_id)
    if not db_repas:
        raise HTTPException(status_code=404, detail="Repas non trouvé")
    return db_repas

@router.patch("/{repas_id}", response_model=RepasResponse)
def update_repas(
    repas_id: UUID,
    repas_data: RepasUpdate,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    db_repas = repas_service.update_repas(db, repas_id, repas_data, restaurant_id)
    if not db_repas:
        raise HTTPException(status_code=404, detail="Repas non trouvé")
    return db_repas

@router.delete("/{repas_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repas(
    repas_id: UUID,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    if not repas_service.delete_repas(db, repas_id, restaurant_id):
        raise HTTPException(status_code=404, detail="Repas non trouvé")
    return None
