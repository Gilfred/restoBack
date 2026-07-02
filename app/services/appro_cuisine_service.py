from sqlalchemy.orm import Session
from app.models.appro_cuisine import ApproCuisine
from app.models.condiment import Condiment
from app.models.unite import Unite
from app.schemas.appro_cuisine import ApproCuisineCreate, ApproCuisineUpdate
from uuid import UUID
from fastapi import HTTPException

def create_appro_cuisine(db: Session, appro_data: ApproCuisineCreate, restaurant_id: UUID):
    # Verify condiment belongs to restaurant
    condiment = db.query(Condiment).filter(Condiment.id == appro_data.condimentId, Condiment.restaurantId == restaurant_id).first()
    if not condiment:
        raise HTTPException(status_code=400, detail="Condiment not found or does not belong to your restaurant")

    # Verify unite belongs to restaurant
    unite = db.query(Unite).filter(Unite.id == appro_data.uniteId, Unite.restaurantId == restaurant_id).first()
    if not unite:
        raise HTTPException(status_code=400, detail="Unite not found or does not belong to your restaurant")

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
        update_dict = appro_data.model_dump(exclude_unset=True)

        # If uniteId is being updated, verify it belongs to the restaurant
        if "uniteId" in update_dict:
            unite = db.query(Unite).filter(Unite.id == update_dict["uniteId"], Unite.restaurantId == restaurant_id).first()
            if not unite:
                raise HTTPException(status_code=400, detail="Unite not found or does not belong to your restaurant")

        for key, value in update_dict.items():
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
