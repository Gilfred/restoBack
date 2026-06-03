from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_session
from app.schemas.permission import PermissionResponse
from app.services import permission_service

router = APIRouter()

@router.get("/", response_model=List[PermissionResponse])
def read_permissions(db: Session = Depends(get_session)):
    return permission_service.get_permissions(db)
