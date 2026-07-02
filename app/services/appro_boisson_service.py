from sqlalchemy.orm import Session
from app.models.appro_boisson import ApproBoisson
from app.models.boisson import Boisson
from app.models.casier import Casier
from app.schemas.appro_boisson import ApproBoissonCreate, ApproBoissonUpdate
from uuid import UUID
from fastapi import HTTPException

def create_appro_boisson(db: Session, appro_data: ApproBoissonCreate, restaurant_id: UUID):
    # Verify boisson belongs to restaurant
    boisson = db.query(Boisson).filter(Boisson.id == appro_data.boissonId, Boisson.restaurantId == restaurant_id).first()
    if not boisson:
        raise HTTPException(status_code=400, detail="Boisson not found or does not belong to your restaurant")

    # Verify casier belongs to restaurant
    casier = db.query(Casier).filter(Casier.id == appro_data.casierId, Casier.restaurantId == restaurant_id).first()
    if not casier:
        raise HTTPException(status_code=400, detail="Casier not found or does not belong to your restaurant")

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
        update_dict = appro_data.model_dump(exclude_unset=True)

        # If casierId is being updated, verify it belongs to the restaurant
        if "casierId" in update_dict:
            casier = db.query(Casier).filter(Casier.id == update_dict["casierId"], Casier.restaurantId == restaurant_id).first()
            if not casier:
                raise HTTPException(status_code=400, detail="Casier not found or does not belong to your restaurant")

        for key, value in update_dict.items():
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
