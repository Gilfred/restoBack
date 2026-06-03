from sqlalchemy.orm import Session
from app.models.condiment import Condiment
from app.schemas.condiment import CondimentCreate, CondimentUpdate
from uuid import UUID

def create_condiment(db: Session, condiment_data: CondimentCreate):
    db_condiment = Condiment(**condiment_data.model_dump())
    db.add(db_condiment)
    db.commit()
    db.refresh(db_condiment)
    return db_condiment

def get_condiments(db: Session, restaurant_id: UUID):
    return db.query(Condiment).filter(Condiment.restaurantId == restaurant_id, Condiment.isActive == True).all()

def get_condiment(db: Session, condiment_id: UUID):
    return db.query(Condiment).filter(Condiment.id == condiment_id, Condiment.isActive == True).first()

def update_condiment(db: Session, condiment_id: UUID, condiment_data: CondimentUpdate):
    db_condiment = get_condiment(db, condiment_id)
    if db_condiment:
        for key, value in condiment_data.model_dump(exclude_unset=True).items():
            setattr(db_condiment, key, value)
        db.commit()
        db.refresh(db_condiment)
    return db_condiment

def delete_condiment(db: Session, condiment_id: UUID):
    db_condiment = get_condiment(db, condiment_id)
    if db_condiment:
        db_condiment.isActive = False
        db.commit()
    return db_condiment
