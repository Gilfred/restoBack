from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_session
from app.schemas.restaurant_user import (
    RestaurantUserResponse,
    RestaurantUserWithDetailsResponse,
    RestaurantUserApprove,
    RestaurantUserRoleUpdate,
    MeRestaurantResponse
)
from app.schemas.auth import StaffResponse
from app.services import restaurant_user_service, restaurant_service
from app.dependencies import get_current_user

router = APIRouter()

@router.post("/{restaurantId}/join", response_model=RestaurantUserResponse)
def join_restaurant(
    restaurantId: UUID,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return restaurant_user_service.join_restaurant(db, current_user.id, restaurantId)

@router.get("/join-requests", response_model=List[RestaurantUserWithDetailsResponse])
def get_join_requests(
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    # Get the restaurant owned by the current user
    restaurant = db.query(restaurant_service.Restaurant).filter(
        restaurant_service.Restaurant.ownerId == current_user.id
    ).first()

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul le propriétaire d'un restaurant peut voir les demandes d'adhésion"
        )

    return restaurant_user_service.get_join_requests(db, restaurant.id)

@router.post("/{restaurantId}/join-requests/{userId}/approve", response_model=RestaurantUserResponse)
def approve_request(
    restaurantId: UUID,
    userId: UUID,
    approve_data: RestaurantUserApprove,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    restaurant = restaurant_service.get_restaurant(db, restaurantId)
    if not restaurant or restaurant.ownerId != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul le propriétaire du restaurant peut approuver les demandes"
        )
    return restaurant_user_service.approve_request(db, restaurantId, userId, approve_data.roleId)

@router.post("/{restaurantId}/join-requests/{userId}/reject", response_model=RestaurantUserResponse)
def reject_request(
    restaurantId: UUID,
    userId: UUID,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    restaurant = restaurant_service.get_restaurant(db, restaurantId)
    if not restaurant or restaurant.ownerId != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul le propriétaire du restaurant peut rejeter les demandes"
        )
    return restaurant_user_service.reject_request(db, restaurantId, userId)

@router.get("/me/restaurant", response_model=MeRestaurantResponse)
def get_me_restaurant(
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    res = restaurant_user_service.get_my_restaurant(db, current_user.id)
    if not res:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vous n'êtes associé à aucun restaurant"
        )
    return res

@router.post("/me/restaurant/leave")
def leave_restaurant(
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    restaurant_user_service.leave_restaurant(db, current_user.id)
    return {"message": "Vous avez quitté le restaurant"}

@router.get("/employees", response_model=List[StaffResponse])
def get_employees(
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    # Check if the user is an owner
    restaurant = db.query(restaurant_service.Restaurant).filter(
        restaurant_service.Restaurant.ownerId == current_user.id
    ).first()

    # If not an owner, check if they are an active staff member
    if not restaurant:
        res_user = db.query(restaurant_user_service.RestaurantUser).filter(
            restaurant_user_service.RestaurantUser.userId == current_user.id,
            restaurant_user_service.RestaurantUser.status == restaurant_user_service.UserRestaurantStatus.ACTIVE
        ).first()

        if res_user:
            restaurant = restaurant_service.get_restaurant(db, res_user.restaurantId)

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé : vous devez appartenir à un restaurant pour voir les membres"
        )

    # Reusing restaurant_service.get_restaurant_staff which returns the flattened format
    return restaurant_service.get_restaurant_staff(db, restaurant.id)

@router.patch("/{restaurantId}/employees/{userId}/role", response_model=RestaurantUserResponse)
def update_employee_role(
    restaurantId: UUID,
    userId: UUID,
    role_data: RestaurantUserRoleUpdate,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    restaurant = restaurant_service.get_restaurant(db, restaurantId)
    if not restaurant or restaurant.ownerId != current_user.id:
        # SUPERADMIN can also modify roles
        is_superadmin = any(role.name.upper() == "SUPERADMIN" for role in current_user.roles if role.name)
        if not is_superadmin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seul le propriétaire du restaurant peut modifier les rôles"
            )
    return restaurant_user_service.update_employee_role(db, restaurantId, userId, role_data.roleId)
