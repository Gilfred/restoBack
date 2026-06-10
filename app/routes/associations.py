from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_session
from app.schemas.associations import UserRoleResponse, RolePermissionResponse, UserRoleCreate, RolePermissionCreate
from app.services import association_service
from app.dependencies import get_current_user, require_admin, restrict_staff_modification, require_superadmin
from app.models.user import User

router = APIRouter()

@router.get("/user-roles", response_model=List[UserRoleResponse])
def read_user_roles(
    db: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    # Multi-tenancy: ADMIN only sees roles of users in their restaurant
    if any(role.name.upper() == "SUPERADMIN" for role in current_user.roles):
        return association_service.get_user_roles(db)

    from app.models.associations import UserRole
    return db.query(UserRole).join(User).filter(User.restaurantId == current_user.restaurantId).all()

@router.get("/role-permissions", response_model=List[RolePermissionResponse])
def read_role_permissions(
    db: Session = Depends(get_session),
    current_user = Depends(require_admin)
):
    return association_service.get_role_permissions(db)

@router.post("/user-roles", response_model=UserRoleResponse)
def create_user_role(
    data: UserRoleCreate,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    restrict_staff_modification(data.userId, current_user, db)

    # Prevents ADMIN from assigning ADMIN or SUPERADMIN roles
    from app.models.role import Role
    target_role = db.query(Role).filter(Role.id == data.roleId).first()
    if not target_role:
        raise HTTPException(status_code=404, detail="Rôle non trouvé")

    is_superadmin = any(r.name.upper() == "SUPERADMIN" for r in current_user.roles)
    if not is_superadmin and target_role.name.upper() in ["ADMIN", "SUPERADMIN"]:
        raise HTTPException(status_code=403, detail="Un ADMIN ne peut pas attribuer les rôles ADMIN ou SUPERADMIN")

    return association_service.add_user_role(db, data.userId, data.roleId)

@router.delete("/user-roles")
def delete_user_role(
    data: UserRoleCreate,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    restrict_staff_modification(data.userId, current_user, db)
    if not association_service.remove_user_role(db, data.userId, data.roleId):
        raise HTTPException(status_code=404, detail="UserRole association not found")
    return {"message": "User role removed"}

@router.post("/role-permissions", response_model=RolePermissionResponse)
def create_role_permission(
    data: RolePermissionCreate,
    db: Session = Depends(get_session),
    current_user = Depends(require_superadmin)
):
    # Only SUPERADMIN should modify global role-permission mappings
    return association_service.add_role_permission(db, data.roleId, data.permissionId)

@router.delete("/role-permissions")
def delete_role_permission(
    data: RolePermissionCreate,
    db: Session = Depends(get_session),
    current_user = Depends(require_superadmin)
):
    # Only SUPERADMIN should modify global role-permission mappings
    if not association_service.remove_role_permission(db, data.roleId, data.permissionId):
        raise HTTPException(status_code=404, detail="RolePermission association not found")
    return {"message": "Role permission removed"}
