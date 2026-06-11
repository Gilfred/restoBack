from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_session
from app.schemas.restaurant import RestaurantCreate, RestaurantResponse
from app.schemas.auth import StaffResponse, UserRolesUpdate
from app.schemas.restaurant_activation_history import RestaurantActivationHistoryResponse
from app.services import restaurant_service, association_service
from app.dependencies import get_current_user, require_superadmin

router = APIRouter()

@router.post("/", response_model=RestaurantResponse)
def create_new_restaurant(
    restaurant_data: RestaurantCreate,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return restaurant_service.create_restaurant(db, restaurant_data, current_user.id)

@router.get("/", response_model=List[RestaurantResponse])
def list_restaurants(
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return restaurant_service.get_all_restaurants(db)

@router.get("/inactive", response_model=List[RestaurantResponse])
def list_inactive_restaurants(
    db: Session = Depends(get_session),
    current_user = Depends(require_superadmin)
):
    return restaurant_service.get_inactive_restaurants(db)

@router.post("/{restaurant_id}/activate", response_model=RestaurantResponse)
def activate_restaurant(
    restaurant_id: UUID,
    db: Session = Depends(get_session),
    current_user = Depends(require_superadmin)
):
    restaurant = restaurant_service.activate_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant

@router.get("/activation-history", response_model=List[RestaurantActivationHistoryResponse])
def get_activation_history(
    db: Session = Depends(get_session),
    current_user = Depends(require_superadmin)
):
    return restaurant_service.get_activation_history(db)

@router.get("/staff", response_model=List[StaffResponse])
def get_restaurant_staff(
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    # Determine which restaurant's staff to show
    # If it's a restaurant owner or an employee, they should see their own restaurant's staff
    if not current_user.restaurantId:
        # Check if they own any restaurants (the first one)
        owned_restaurant = db.query(restaurant_service.Restaurant).filter(restaurant_service.Restaurant.ownerId == current_user.id).first()
        if owned_restaurant:
            restaurant_id = owned_restaurant.id
        else:
             raise HTTPException(status_code=403, detail="L'utilisateur n'est associé à aucun restaurant")
    else:
        restaurant_id = current_user.restaurantId

    return restaurant_service.get_restaurant_staff(db, restaurant_id)

@router.put("/staff/{employee_id}/roles", response_model=StaffResponse)
def update_employee_roles(
    employee_id: UUID,
    role_data: UserRolesUpdate,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    # This endpoint is restricted to the restaurant owner
    employee = db.query(restaurant_service.User).filter(restaurant_service.User.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employé non trouvé")
    
    if not employee.restaurantId:
        raise HTTPException(status_code=400, detail="L'employé n'est associé à aucun restaurant")

    # Check if current_user is the owner of the restaurant
    restaurant = restaurant_service.get_restaurant(db, employee.restaurantId)
    if not restaurant or restaurant.ownerId != current_user.id:
        raise HTTPException(status_code=403, detail="Seul le propriétaire du restaurant peut modifier les rôles des employés")

    updated_employee = association_service.update_user_roles(db, employee_id, role_data.roleIds)
    return updated_employee
