from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_session
from app.schemas.unite import UniteResponse, UniteCreate
from app.services import unite_service

router = APIRouter()

@router.get("/{restaurant_id}", response_model=List[UniteResponse])
def read_unites(restaurant_id: UUID, db: Session = Depends(get_session)):
    return unite_service.get_unites(db, restaurant_id)

@router.post("/", response_model=UniteResponse)
def create_unite(unite_data: UniteCreate, db: Session = Depends(get_session)):
    return unite_service.create_unite(db, unite_data)
