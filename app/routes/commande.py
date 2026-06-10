from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_session
from app.schemas.commande import CommandeCreate, CommandeUpdate, CommandeResponse
from app.services import commande_service
from app.dependencies import get_current_user, check_permissions

router = APIRouter()

@router.post("/", response_model=CommandeResponse)
def create_commande(
    commande_data: CommandeCreate,
    db: Session = Depends(get_session),
    current_user = Depends(check_permissions("create_orders"))
):
    return commande_service.create_commande(db, commande_data)

@router.get("/restaurant/{restaurant_id}", response_model=List[CommandeResponse])
def list_commandes(
    restaurant_id: UUID,
    db: Session = Depends(get_session),
    current_user = Depends(check_permissions("view_orders"))
):
    return commande_service.get_commandes(db, restaurant_id)

@router.get("/{commande_id}", response_model=CommandeResponse)
def get_commande(
    commande_id: UUID,
    db: Session = Depends(get_session),
    current_user = Depends(check_permissions("view_orders"))
):
    db_commande = commande_service.get_commande(db, commande_id)
    if not db_commande:
        raise HTTPException(status_code=404, detail="Commande not found")
    return db_commande

@router.put("/{commande_id}", response_model=CommandeResponse)
def update_commande(
    commande_id: UUID,
    commande_data: CommandeUpdate,
    db: Session = Depends(get_session),
    current_user = Depends(check_permissions("update_orders"))
):
    db_commande = commande_service.update_commande(db, commande_id, commande_data)
    if not db_commande:
        raise HTTPException(status_code=404, detail="Commande not found")
    return db_commande

@router.delete("/{commande_id}")
def delete_commande(
    commande_id: UUID,
    db: Session = Depends(get_session),
    current_user = Depends(check_permissions("update_orders"))
):
    if not commande_service.delete_commande(db, commande_id):
        raise HTTPException(status_code=404, detail="Commande not found")
    return {"message": "Commande deleted"}
