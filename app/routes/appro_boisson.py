from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_session
from app.schemas.appro_boisson import ApproBoissonCreate, ApproBoissonUpdate, ApproBoissonResponse
from app.services import appro_boisson_service
from app.dependencies import get_current_user

router = APIRouter()

@router.post("/", response_model=ApproBoissonResponse)
def create_appro(
    appro_data: ApproBoissonCreate,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return appro_boisson_service.create_appro_boisson(db, appro_data)

@router.get("/", response_model=List[ApproBoissonResponse])
def list_appros(
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return appro_boisson_service.get_appro_boissons(db)

@router.get("/{appro_id}", response_model=ApproBoissonResponse)
def get_appro(
    appro_id: UUID,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    db_appro = appro_boisson_service.get_appro_boisson(db, appro_id)
    if not db_appro:
        raise HTTPException(status_code=404, detail="ApproBoisson not found")
    return db_appro

@router.put("/{appro_id}", response_model=ApproBoissonResponse)
def update_appro(
    appro_id: UUID,
    appro_data: ApproBoissonUpdate,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    db_appro = appro_boisson_service.update_appro_boisson(db, appro_id, appro_data)
    if not db_appro:
        raise HTTPException(status_code=404, detail="ApproBoisson not found")
    return db_appro

@router.delete("/{appro_id}")
def delete_appro(
    appro_id: UUID,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if not appro_boisson_service.delete_appro_boisson(db, appro_id):
        raise HTTPException(status_code=404, detail="ApproBoisson not found")
    return {"message": "ApproBoisson deleted"}
