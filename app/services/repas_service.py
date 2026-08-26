from sqlalchemy.orm import Session
from app.models.repas import Repas
from app.schemas.repas import RepasCreate, RepasUpdate
from uuid import UUID

def create_repas(db: Session, repas_data: RepasCreate, restaurant_id: UUID):
    db_repas = Repas(
        **repas_data.model_dump(),
        restaurantId=restaurant_id
    )
    db.add(db_repas)
    db.commit()
    db.refresh(db_repas)
    return db_repas

def get_repas_list(db: Session, restaurant_id: UUID):
    return db.query(Repas).filter(Repas.restaurantId == restaurant_id).all()

def get_repas(db: Session, repas_id: UUID, restaurant_id: UUID):
    return db.query(Repas).filter(
        Repas.id == repas_id,
        Repas.restaurantId == restaurant_id
    ).first()

def update_repas(db: Session, repas_id: UUID, repas_data: RepasUpdate, restaurant_id: UUID):
    db_repas = get_repas(db, repas_id, restaurant_id)
    if db_repas:
        for key, value in repas_data.model_dump(exclude_unset=True).items():
            setattr(db_repas, key, value)
        db.commit()
        db.refresh(db_repas)
    return db_repas

def delete_repas(db: Session, repas_id: UUID, restaurant_id: UUID):
    db_repas = get_repas(db, repas_id, restaurant_id)
    if db_repas:
        db.delete(db_repas)
        db.commit()
        return True
    return False
