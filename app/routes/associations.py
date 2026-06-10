from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_session
from app.schemas.associations import UserRoleResponse, RolePermissionResponse
from app.services import association_service
from app.dependencies import get_current_user

router = APIRouter()

@router.get("/user-roles", response_model=List[UserRoleResponse])
def read_user_roles(
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return association_service.get_user_roles(db)

@router.get("/role-permissions", response_model=List[RolePermissionResponse])
def read_role_permissions(
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return association_service.get_role_permissions(db)
