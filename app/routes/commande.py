from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_session
from app.schemas.commande import (
    CommandeCreate,
    CommandeUpdate,
    CommandeResponse,
    UserBasicInfo,
)
from app.services import commande_service
from app.dependencies import (
    get_current_user,
    require_manager_cashier,
    require_manager_or_admin,
    get_user_restaurant_id,
)

router = APIRouter()

@router.post("/", response_model=CommandeResponse)
def create_commande(
    commande_data: CommandeCreate,
    db: Session = Depends(get_session),
    current_user=Depends(require_manager_cashier),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
):
    """
    Crée une commande pour une serveuse du restaurant
    de l'utilisateur connecté.
    """
    return commande_service.create_commande(
        db,
        commande_data,
        restaurant_id,
    )


@router.get("/serveuses", response_model=List[UserBasicInfo])
def list_restaurant_waiters(
    db: Session = Depends(get_session),
    current_user=Depends(require_manager_or_admin),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
):
    """
    Liste les serveuses appartenant au restaurant
    de l'utilisateur connecté.
    """
    return commande_service.get_restaurant_waiters(
        db,
        restaurant_id,
    )


# GET - MES COMMANDES
# Serveuse : uniquement ses propres commandes

@router.get("/me", response_model=List[CommandeResponse])
def list_my_commandes(
    db: Session = Depends(get_session),
    current_user=Depends(get_current_user),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
):
    """
    Liste uniquement les commandes créées par l'utilisateur
    connecté et appartenant à son restaurant.
    """
    return commande_service.get_my_commandes(
        db,
        current_user.id,
        restaurant_id,
    )


# GET - TOUTES LES COMMANDES DU RESTAURANT
# MANAGER_CASHIER / ADMIN uniquement

@router.get("/", response_model=List[CommandeResponse])
def list_current_restaurant_commandes(
    db: Session = Depends(get_session),
    current_user=Depends(require_manager_or_admin),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
):
    """
    Liste toutes les commandes du restaurant
    de l'utilisateur connecté.
    """
    return commande_service.get_commandes(
        db,
        restaurant_id,
    )


@router.get("/{commande_id}", response_model=CommandeResponse)
def get_commande(
    commande_id: UUID,
    db: Session = Depends(get_session),
    current_user=Depends(get_current_user),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
):
    """
    Récupère une commande en respectant les règles d'accès
    du restaurant et du rôle de l'utilisateur.
    """

    # Vérifier si l'utilisateur est MANAGER_CASHIER ou ADMIN
    is_manager_or_admin = any(
        role.name
        and role.name.upper() in ["MANAGER_CASHIER", "ADMIN"]
        for role in current_user.roles
    )

    if is_manager_or_admin:
        # Manager/Admin :
        # accès à toute commande de son restaurant
        db_commande = commande_service.get_commande(
            db,
            commande_id,
            restaurant_id,
        )
    else:
        # Utilisateur standard / serveuse :
        # accès uniquement à sa propre commande
        db_commande = commande_service.get_my_commande(
            db,
            commande_id,
            current_user.id,
            restaurant_id,
        )

    if not db_commande:
        raise HTTPException(
            status_code=404,
            detail="Commande non trouvée",
        )

    return db_commande


@router.patch("/{commande_id}", response_model=CommandeResponse)
def update_commande(
    commande_id: UUID,
    commande_data: CommandeUpdate,
    db: Session = Depends(get_session),
    current_user=Depends(require_manager_or_admin),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
):
    """
    Modifie une commande appartenant au restaurant
    de l'utilisateur connecté.
    """
    db_commande = commande_service.update_commande(
        db,
        commande_id,
        commande_data,
        restaurant_id,
    )

    if not db_commande:
        raise HTTPException(
            status_code=404,
            detail="Commande non trouvée",
        )

    return db_commande


@router.delete("/{commande_id}")
def delete_commande(
    commande_id: UUID,
    db: Session = Depends(get_session),
    current_user=Depends(require_manager_or_admin),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
):
    """
    Supprime logiquement une commande appartenant au restaurant
    de l'utilisateur connecté.
    """
    if not commande_service.delete_commande(
        db,
        commande_id,
        restaurant_id,
    ):
        raise HTTPException(
            status_code=404,
            detail="Commande non trouvée",
        )

    return {"message": "Commande supprimée"}
