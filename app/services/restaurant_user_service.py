from sqlalchemy.orm import Session, joinedload
from app.models.restaurant_user import RestaurantUser
from app.models.user import User
from app.models.restaurant import Restaurant
from app.models.role import Role
from app.enums import UserRestaurantStatus
from uuid import UUID
from fastapi import HTTPException, status

def join_restaurant(db: Session, user_id: UUID, restaurant_id: UUID):
    # Check if user already belongs to a restaurant
    existing = db.query(RestaurantUser).filter(RestaurantUser.userId == user_id).first()
    if existing:
        if existing.status == UserRestaurantStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="L'utilisateur est déjà lié à un restaurant"
            )
        elif existing.status == UserRestaurantStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Votre demande antérieure n'a pas encore été confirmée ou rejetée"
            )
        else:
            # If REJECTED, delete the old record to allow a new application
            db.delete(existing)
            db.commit()

    # Check if restaurant exists
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant non trouvé"
        )

    db_restaurant_user = RestaurantUser(
        userId=user_id,
        restaurantId=restaurant_id,
        status=UserRestaurantStatus.PENDING
    )
    db.add(db_restaurant_user)
    db.commit()
    db.refresh(db_restaurant_user)
    return db_restaurant_user

def get_join_requests(db: Session, restaurant_id: UUID):
    return db.query(RestaurantUser).options(
        joinedload(RestaurantUser.user),
        joinedload(RestaurantUser.role)
    ).filter(
        RestaurantUser.restaurantId == restaurant_id,
        RestaurantUser.status == UserRestaurantStatus.PENDING
    ).all()

def approve_request(db: Session, restaurant_id: UUID, user_id: UUID, role_id: UUID):
    db_restaurant_user = db.query(RestaurantUser).filter(
        RestaurantUser.restaurantId == restaurant_id,
        RestaurantUser.userId == user_id
    ).first()

    if not db_restaurant_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demande non trouvée"
        )

    if db_restaurant_user.status != UserRestaurantStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La demande n'est plus en attente"
        )

    # Check if role exists
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rôle non trouvé"
        )

    db_restaurant_user.status = UserRestaurantStatus.ACTIVE
    db_restaurant_user.roleId = role_id

    # Sync User.restaurantId
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.restaurantId = restaurant_id

    db.commit()
    db.refresh(db_restaurant_user)
    return db_restaurant_user

def reject_request(db: Session, restaurant_id: UUID, user_id: UUID):
    db_restaurant_user = db.query(RestaurantUser).filter(
        RestaurantUser.restaurantId == restaurant_id,
        RestaurantUser.userId == user_id
    ).first()

    if not db_restaurant_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demande non trouvée"
        )

    if db_restaurant_user.status != UserRestaurantStatus.PENDING:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La demande n'est plus en attente"
        )

    db_restaurant_user.status = UserRestaurantStatus.REJECTED
    db.commit()
    db.refresh(db_restaurant_user)
    return db_restaurant_user

def get_my_restaurant(db: Session, user_id: UUID):
    return db.query(RestaurantUser).options(
        joinedload(RestaurantUser.restaurant),
        joinedload(RestaurantUser.role)
    ).filter(
        RestaurantUser.userId == user_id
    ).first()

def leave_restaurant(db: Session, user_id: UUID):
    db_restaurant_user = db.query(RestaurantUser).filter(
        RestaurantUser.userId == user_id
    ).first()

    if not db_restaurant_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="L'utilisateur n'est lié à aucun restaurant"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.restaurantId = None

    db.delete(db_restaurant_user)
    db.commit()
    return True

def get_employees(db: Session, restaurant_id: UUID):
    return db.query(RestaurantUser).options(
        joinedload(RestaurantUser.user),
        joinedload(RestaurantUser.role)
    ).filter(
        RestaurantUser.restaurantId == restaurant_id,
        RestaurantUser.status == UserRestaurantStatus.ACTIVE
    ).all()

def update_employee_role(db: Session, restaurant_id: UUID, user_id: UUID, role_id: UUID):
    db_restaurant_user = db.query(RestaurantUser).filter(
        RestaurantUser.restaurantId == restaurant_id,
        RestaurantUser.userId == user_id,
        RestaurantUser.status == UserRestaurantStatus.ACTIVE
    ).first()

    if not db_restaurant_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employé non trouvé"
        )

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rôle non trouvé"
        )

    db_restaurant_user.roleId = role_id
    db.commit()
    db.refresh(db_restaurant_user)
    return db_restaurant_user
