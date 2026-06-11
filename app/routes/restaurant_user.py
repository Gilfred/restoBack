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

@router.get("/{restaurantId}/join-requests", response_model=List[RestaurantUserWithDetailsResponse])
def get_join_requests(
    restaurantId: UUID,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    # Check if current_user is the owner of the restaurant
    restaurant = restaurant_service.get_restaurant(db, restaurantId)
    if not restaurant or restaurant.ownerId != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul le propriétaire du restaurant peut voir les demandes"
        )
    return restaurant_user_service.get_join_requests(db, restaurantId)

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
            detail="Aucun restaurant associé"
        )
    return res

@router.post("/me/restaurant/leave")
def leave_restaurant(
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    restaurant_user_service.leave_restaurant(db, current_user.id)
    return {"message": "Vous avez quitté le restaurant"}

@router.get("/{restaurantId}/employees", response_model=List[StaffResponse])
def get_employees(
    restaurantId: UUID,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    restaurant = restaurant_service.get_restaurant(db, restaurantId)
    if not restaurant or restaurant.ownerId != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul le propriétaire du restaurant peut voir les employés"
        )
    # Reusing restaurant_service.get_restaurant_staff which returns the flattened format
    return restaurant_service.get_restaurant_staff(db, restaurantId)

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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul le propriétaire du restaurant peut modifier les rôles"
        )
    return restaurant_user_service.update_employee_role(db, restaurantId, userId, role_data.roleId)
