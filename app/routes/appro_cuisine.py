from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_session
from app.schemas.appro_cuisine import ApproCuisineCreate, ApproCuisineUpdate, ApproCuisineResponse
from app.services import appro_cuisine_service
from app.dependencies import get_current_user

router = APIRouter()

@router.post("/", response_model=ApproCuisineResponse)
def create_appro(
    appro_data: ApproCuisineCreate,
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return appro_cuisine_service.create_appro_cuisine(db, appro_data)

@router.get("/", response_model=List[ApproCuisineResponse])
def list_appros(
    db: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return appro_cuisine_service.get_appro_cuisines(db)

@router.get("/{appro_id}", response_model=ApproCuisineResponse)
def get_appro(appro_id: UUID, db: Session = Depends(get_session)):
    db_appro = appro_cuisine_service.get_appro_cuisine(db, appro_id)
    if not db_appro:
        raise HTTPException(status_code=404, detail="ApproCuisine not found")
    return db_appro

@router.put("/{appro_id}", response_model=ApproCuisineResponse)
def update_appro(appro_id: UUID, appro_data: ApproCuisineUpdate, db: Session = Depends(get_session)):
    db_appro = appro_cuisine_service.update_appro_cuisine(db, appro_id, appro_data)
    if not db_appro:
        raise HTTPException(status_code=404, detail="ApproCuisine not found")
    return db_appro

@router.delete("/{appro_id}")
def delete_appro(appro_id: UUID, db: Session = Depends(get_session)):
    if not appro_cuisine_service.delete_appro_cuisine(db, appro_id):
        raise HTTPException(status_code=404, detail="ApproCuisine not found")
    return {"message": "ApproCuisine deleted"}
