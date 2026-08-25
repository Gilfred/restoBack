import uuid as uuid_mod
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.models.commande import Commande
from app.models.commande_article import CommandeArticle
from app.models.user import User
from app.models.restaurant_user import RestaurantUser
from app.models.role import Role
from app.models.associations import UserRole
from app.enums import UserRestaurantStatus
from app.schemas.commande import CommandeCreate, CommandeUpdate

def get_restaurant_waiters(db: Session, restaurant_id: UUID):
    """Retrieve all active waiters (serveuses) belonging to a specific restaurant."""
    ru_waiters = db.query(User).join(
        RestaurantUser, RestaurantUser.userId == User.id
    ).join(
        Role, RestaurantUser.roleId == Role.id
    ).filter(
        RestaurantUser.restaurantId == restaurant_id,
        RestaurantUser.status == UserRestaurantStatus.ACTIVE,
        func.upper(Role.name) == "WAITER"
    ).all()

    ur_waiters = db.query(User).join(
        UserRole, UserRole.userId == User.id
    ).join(
        Role, UserRole.roleId == Role.id
    ).filter(
        User.restaurantId == restaurant_id,
        User.isActive == True,
        func.upper(Role.name) == "WAITER"
    ).all()

    waiters_map = {u.id: u for u in ru_waiters + ur_waiters}
    return list(waiters_map.values())

def create_commande(db: Session, commande_data: CommandeCreate, restaurant_id: UUID, current_user_id: UUID = None):
    """Create an order for a waiter within the manager's restaurant."""
    data = commande_data.model_dump()
    waiter_id = data.get("userId") or current_user_id

    if not waiter_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Une serveuse doit être sélectionnée"
        )

    # Verify selected waiter exists
    waiter_user = db.query(User).filter(User.id == waiter_id).first()
    if not waiter_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La serveuse sélectionnée n'existe pas"
        )

    # Verify waiter belongs to this restaurant
    is_in_restaurant = False
    if waiter_user.restaurantId == restaurant_id:
        is_in_restaurant = True
    else:
        ru = db.query(RestaurantUser).filter(
            RestaurantUser.userId == waiter_user.id,
            RestaurantUser.restaurantId == restaurant_id,
            RestaurantUser.status == UserRestaurantStatus.ACTIVE
        ).first()
        if ru:
            is_in_restaurant = True

    if not is_in_restaurant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La serveuse sélectionnée n'appartient pas à votre restaurant"
        )

    data["userId"] = waiter_id
    articles_data = data.pop("articles")

    data["restaurantId"] = restaurant_id

    if not data.get("numeroCommande"):
        data["numeroCommande"] = f"CMD-{uuid_mod.uuid4().hex[:8].upper()}"

    calculated_total = sum(art["qte"] * art["prixUnitaire"] for art in articles_data)
    if not data.get("total") or data.get("total") == 0:
        data["total"] = calculated_total

    db_commande = Commande(**data)
    db.add(db_commande)
    db.flush()

    for art_data in articles_data:
        sous_total = art_data["qte"] * art_data["prixUnitaire"]
        db_article = CommandeArticle(
            **art_data,
            commandeId=db_commande.id,
            sousTotal=sous_total
        )
        db.add(db_article)

    db.commit()
    return get_commande(db, db_commande.id)

def get_my_commandes(db: Session, user_id: UUID):
    """Retrieve orders made for/by the currently logged-in serveuse/user."""
    return db.query(Commande).options(
        joinedload(Commande.articles),
        joinedload(Commande.user)
    ).filter(
        Commande.userId == user_id,
        Commande.isActive == True
    ).order_by(Commande.createdAt.desc()).all()

def get_commandes(db: Session, restaurant_id: UUID):
    return db.query(Commande).options(
        joinedload(Commande.articles),
        joinedload(Commande.user)
    ).filter(
        Commande.restaurantId == restaurant_id,
        Commande.isActive == True
    ).order_by(Commande.createdAt.desc()).all()

def get_commande(db: Session, commande_id: UUID):
    return db.query(Commande).options(
        joinedload(Commande.articles),
        joinedload(Commande.user)
    ).filter(
        Commande.id == commande_id,
        Commande.isActive == True
    ).first()

def update_commande(db: Session, commande_id: UUID, commande_data: CommandeUpdate):
    db_commande = get_commande(db, commande_id)
    if db_commande:
        for key, value in commande_data.model_dump(exclude_unset=True).items():
            setattr(db_commande, key, value)
        db.commit()
        db.refresh(db_commande)
    return db_commande

def delete_commande(db: Session, commande_id: UUID):
    db_commande = get_commande(db, commande_id)
    if db_commande:
        db_commande.isActive = False
        db.commit()
    return db_commande
