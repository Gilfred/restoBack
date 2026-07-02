from sqlalchemy.orm import Session
from app.models.appro_cuisine import ApproCuisine
from app.models.condiment import Condiment
from app.schemas.appro_cuisine import ApproCuisineCreate, ApproCuisineUpdate
from uuid import UUID
from fastapi import HTTPException

def create_appro_cuisine(db: Session, appro_data: ApproCuisineCreate, restaurant_id: UUID):
    # Verify condiment belongs to restaurant
    condiment = db.query(Condiment).filter(Condiment.id == appro_data.condimentId, Condiment.restaurantId == restaurant_id).first()
    if not condiment:
        raise HTTPException(status_code=400, detail="Condiment not found or does not belong to your restaurant")

    db_appro = ApproCuisine(**appro_data.model_dump())
    db.add(db_appro)
    db.commit()
    db.refresh(db_appro)
    return db_appro

def get_appro_cuisines(db: Session, restaurant_id: UUID):
    return db.query(ApproCuisine).join(Condiment).filter(
        Condiment.restaurantId == restaurant_id,
        ApproCuisine.isActive == True
    ).all()

def get_appro_cuisine(db: Session, appro_id: UUID, restaurant_id: UUID):
    return db.query(ApproCuisine).join(Condiment).filter(
        ApproCuisine.id == appro_id,
        Condiment.restaurantId == restaurant_id,
        ApproCuisine.isActive == True
    ).first()

def update_appro_cuisine(db: Session, appro_id: UUID, appro_data: ApproCuisineUpdate, restaurant_id: UUID):
    db_appro = get_appro_cuisine(db, appro_id, restaurant_id)
    if db_appro:
        for key, value in appro_data.model_dump(exclude_unset=True).items():
            setattr(db_appro, key, value)
        db.commit()
        db.refresh(db_appro)
    return db_appro

def delete_appro_cuisine(db: Session, appro_id: UUID, restaurant_id: UUID):
    db_appro = get_appro_cuisine(db, appro_id, restaurant_id)
    if db_appro:
        db_appro.isActive = False
        db.commit()
    return db_appro
