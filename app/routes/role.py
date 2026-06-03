from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_session
from app.schemas.role import RoleResponse
from app.services import role_service
from app.dependencies import get_current_user

router = APIRouter()

@router.get("/", response_model=List[RoleResponse])
def read_roles(
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return role_service.get_roles(db)
