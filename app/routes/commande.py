from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_session
from app.schemas.commande import CommandeCreate, CommandeUpdate, CommandeResponse, UserBasicInfo
from app.services import commande_service
from app.dependencies import get_current_user, check_permissions, require_manager_cashier, get_user_restaurant_id

router = APIRouter()

@router.post("/", response_model=CommandeResponse)
def create_commande(
    commande_data: CommandeCreate,
    db: Session = Depends(get_session),
    current_user = Depends(require_manager_cashier),
    restaurant_id: UUID = Depends(get_user_restaurant_id)
):
    """Create an order for a waiter. Restricted to MANAGER_CASHIER, ADMIN, SUPERADMIN, or restaurant owner."""
    return commande_service.create_commande(db, commande_data, restaurant_id)


@router.get("/waiters", response_model=List[UserBasicInfo])
@router.get("/serveuses", response_model=List[UserBasicInfo])
def list_restaurant_waiters(
    db: Session = Depends(get_session),
    current_user = Depends(require_manager_cashier),
    restaurant_id: UUID = Depends(get_user_restaurant_id)
):
    """Get waiters belonging only to the manager's restaurant."""
    return commande_service.get_restaurant_waiters(db, restaurant_id)

@router.get("/my-commandes", response_model=List[CommandeResponse])
@router.get("/me", response_model=List[CommandeResponse])
def list_my_commandes(
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    """Get orders made for/by the currently logged-in user (e.g. serveuse)."""
    return commande_service.get_my_commandes(db, current_user.id)

@router.get("/", response_model=List[CommandeResponse])
def list_current_restaurant_commandes(
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user),
    restaurant_id: UUID = Depends(get_user_restaurant_id)
):
    """Get all orders for the current user's restaurant."""
    return commande_service.get_commandes(db, restaurant_id)

@router.get("/restaurant/{restaurant_id}", response_model=List[CommandeResponse])
def list_commandes(
    restaurant_id: UUID,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return commande_service.get_commandes(db, restaurant_id)

@router.get("/{commande_id}", response_model=CommandeResponse)
def get_commande(
    commande_id: UUID,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    db_commande = commande_service.get_commande(db, commande_id)
    if not db_commande:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    return db_commande

@router.patch("/{commande_id}", response_model=CommandeResponse)
def update_commande(
    commande_id: UUID,
    commande_data: CommandeUpdate,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    db_commande = commande_service.update_commande(db, commande_id, commande_data)
    if not db_commande:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    return db_commande

@router.delete("/{commande_id}")
def delete_commande(
    commande_id: UUID,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if not commande_service.delete_commande(db, commande_id):
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    return {"message": "Commande supprimée"}
