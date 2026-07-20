from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.database import get_session
from app.schemas.unite import UniteResponse, UniteCreate
from app.services import unite_service
from app.dependencies import get_user_restaurant_id, require_superadmin, get_current_user

router = APIRouter()

@router.get("/", response_model=List[UniteResponse])
def read_unites(
    restaurant_id: Optional[UUID] = None,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user) # Accessible to all restaurant employees
):
    # Check if the user is a superadmin
    is_superadmin = any(role.name.upper() == "SUPERADMIN" for role in current_user.roles if role.name)
    if not is_superadmin:
        # Fallback: check database directly to be absolutely sure
        from app.models.associations import UserRole
        from app.models.role import Role
        is_superadmin = db.query(Role).join(UserRole).filter(
            UserRole.userId == current_user.id,
            Role.name == "SUPERADMIN"
        ).first() is not None

    if is_superadmin:
        # Superadmin can view units for a specific restaurant, or all active units if restaurant_id is None
        from app.models.unite import Unite
        if restaurant_id:
            return db.query(Unite).filter(Unite.restaurantId == restaurant_id, Unite.isActive == True).all()
        else:
            return db.query(Unite).filter(Unite.isActive == True).all()
    else:
        # Non-superadmin users must belong to a restaurant
        # We call get_user_restaurant_id logic manually or pass current_user
        from app.dependencies import get_user_restaurant_id
        # Let's get the restaurant_id for the current user
        user_restaurant_id = get_user_restaurant_id(current_user, db)
        return unite_service.get_unites(db, user_restaurant_id)

@router.post("/", response_model=UniteResponse)
def create_unite(
    unite_data: UniteCreate,
    restaurant_id: Optional[UUID] = None,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user) # Accessible to restaurant employees and superadmins
):
    # Check if the user is a superadmin
    is_superadmin = any(role.name.upper() == "SUPERADMIN" for role in current_user.roles if role.name)
    if not is_superadmin:
        # Fallback: check database directly to be absolutely sure
        from app.models.associations import UserRole
        from app.models.role import Role
        is_superadmin = db.query(Role).join(UserRole).filter(
            UserRole.userId == current_user.id,
            Role.name == "SUPERADMIN"
        ).first() is not None

    if is_superadmin:
        # Superadmin can specify target restaurant ID via body or query parameter
        target_restaurant_id = unite_data.restaurantId or restaurant_id
        if not target_restaurant_id:
            # Fallback to superadmin's associated restaurant if any
            try:
                from app.dependencies import get_user_restaurant_id
                target_restaurant_id = get_user_restaurant_id(current_user, db)
            except Exception:
                pass

        if not target_restaurant_id:
            raise HTTPException(
                status_code=400,
                detail="Le paramètre restaurantId ou restaurant_id est requis pour le superadmin"
            )

        # Verify that the specified restaurant exists
        from app.models.restaurant import Restaurant
        restaurant_exists = db.query(Restaurant).filter(Restaurant.id == target_restaurant_id).first() is not None
        if not restaurant_exists:
            raise HTTPException(
                status_code=404,
                detail="Le restaurant spécifié n'existe pas"
            )
    else:
        # Non-superadmin users: check if they are authorized (owner, ADMIN, or has manage_staff permission)
        from app.models.restaurant import Restaurant
        is_owner = db.query(Restaurant).filter(Restaurant.ownerId == current_user.id).first() is not None
        
        is_authorized = is_owner
        if not is_authorized:
            for role in current_user.roles:
                if role.name.upper() == "ADMIN":
                    is_authorized = True
                    break
                for perm in role.permissions:
                    if perm.name == "manage_staff":
                        is_authorized = True
                        break

        # Fallback direct database check for role or permission if not eagerly loaded
        if not is_authorized:
            from app.models.associations import RolePermission, UserRole
            from app.models.permission import Permission
            from app.models.role import Role

            has_admin_role = db.query(Role).join(UserRole).filter(
                UserRole.userId == current_user.id,
                Role.name == "ADMIN"
            ).first() is not None

            has_manage_staff_perm = db.query(Permission).join(RolePermission).join(Role).join(UserRole).filter(
                UserRole.userId == current_user.id,
                Permission.name == "manage_staff"
            ).first() is not None

            if has_admin_role or has_manage_staff_perm:
                is_authorized = True

        if not is_authorized:
            raise HTTPException(
                status_code=403,
                detail="Vous n'avez pas la permission de créer des unités"
            )

        # Force-use their associated restaurant ID to prevent BOLA (ignore passed parameters)
        from app.dependencies import get_user_restaurant_id
        target_restaurant_id = get_user_restaurant_id(current_user, db)

    return unite_service.create_unite(db, unite_data, target_restaurant_id)
