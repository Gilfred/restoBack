from sqlalchemy.orm import Session
from app.models.boisson import Boisson
from app.schemas.boisson import BoissonCreate, BoissonUpdate
from uuid import UUID

def create_boisson(db: Session, boisson_data: BoissonCreate, restaurant_id: UUID):
    db_boisson = Boisson(
        **boisson_data.model_dump(),
        restaurantId=restaurant_id
    )
    db.add(db_boisson)
    db.commit()
    db.refresh(db_boisson)
    return db_boisson

def get_boissons(db: Session, restaurant_id: UUID):
    return db.query(Boisson).filter(Boisson.restaurantId == restaurant_id).all()

def get_boisson(db: Session, boisson_id: UUID, restaurant_id: UUID):
    return db.query(Boisson).filter(
        Boisson.id == boisson_id,
        Boisson.restaurantId == restaurant_id
    ).first()

def update_boisson(db: Session, boisson_id: UUID, boisson_data: BoissonUpdate, restaurant_id: UUID):
    db_boisson = get_boisson(db, boisson_id, restaurant_id)
    if db_boisson:
        for key, value in boisson_data.model_dump(exclude_unset=True).items():
            setattr(db_boisson, key, value)
        db.commit()
        db.refresh(db_boisson)
    return db_boisson

def delete_boisson(db: Session, boisson_id: UUID, restaurant_id: UUID):
    db_boisson = get_boisson(db, boisson_id, restaurant_id)
    if db_boisson:
        db.delete(db_boisson)
        db.commit()
    return db_boisson
