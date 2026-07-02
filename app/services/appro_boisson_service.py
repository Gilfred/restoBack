from sqlalchemy.orm import Session
from app.models.appro_boisson import ApproBoisson
from app.models.boisson import Boisson
from app.schemas.appro_boisson import ApproBoissonCreate, ApproBoissonUpdate
from uuid import UUID
from fastapi import HTTPException

def create_appro_boisson(db: Session, appro_data: ApproBoissonCreate, restaurant_id: UUID):
    # Verify boisson belongs to restaurant
    boisson = db.query(Boisson).filter(Boisson.id == appro_data.boissonId, Boisson.restaurantId == restaurant_id).first()
    if not boisson:
        raise HTTPException(status_code=400, detail="Boisson not found or does not belong to your restaurant")

    db_appro = ApproBoisson(**appro_data.model_dump())
    db.add(db_appro)
    db.commit()
    db.refresh(db_appro)
    return db_appro

def get_appro_boissons(db: Session, restaurant_id: UUID):
    return db.query(ApproBoisson).join(Boisson).filter(
        Boisson.restaurantId == restaurant_id,
        ApproBoisson.isActive == True
    ).all()

def get_appro_boisson(db: Session, appro_id: UUID, restaurant_id: UUID):
    return db.query(ApproBoisson).join(Boisson).filter(
        ApproBoisson.id == appro_id,
        Boisson.restaurantId == restaurant_id,
        ApproBoisson.isActive == True
    ).first()

def update_appro_boisson(db: Session, appro_id: UUID, appro_data: ApproBoissonUpdate, restaurant_id: UUID):
    db_appro = get_appro_boisson(db, appro_id, restaurant_id)
    if db_appro:
        for key, value in appro_data.model_dump(exclude_unset=True).items():
            setattr(db_appro, key, value)
        db.commit()
        db.refresh(db_appro)
    return db_appro

def delete_appro_boisson(db: Session, appro_id: UUID, restaurant_id: UUID):
    db_appro = get_appro_boisson(db, appro_id, restaurant_id)
    if db_appro:
        db_appro.isActive = False
        db.commit()
    return db_appro
