from sqlalchemy.orm import Session
from app.models.appro_cuisine import ApproCuisine
from app.schemas.appro_cuisine import ApproCuisineCreate, ApproCuisineUpdate
from uuid import UUID

def create_appro_cuisine(db: Session, appro_data: ApproCuisineCreate):
    db_appro = ApproCuisine(**appro_data.model_dump())
    db.add(db_appro)
    db.commit()
    db.refresh(db_appro)
    return db_appro

def get_appro_cuisines(db: Session):
    return db.query(ApproCuisine).filter(ApproCuisine.isActive == True).all()

def get_appro_cuisine(db: Session, appro_id: UUID):
    return db.query(ApproCuisine).filter(ApproCuisine.id == appro_id, ApproCuisine.isActive == True).first()

def update_appro_cuisine(db: Session, appro_id: UUID, appro_data: ApproCuisineUpdate):
    db_appro = get_appro_cuisine(db, appro_id)
    if db_appro:
        for key, value in appro_data.model_dump(exclude_unset=True).items():
            setattr(db_appro, key, value)
        db.commit()
        db.refresh(db_appro)
    return db_appro

def delete_appro_cuisine(db: Session, appro_id: UUID):
    db_appro = get_appro_cuisine(db, appro_id)
    if db_appro:
        db_appro.isActive = False
        db.commit()
    return db_appro
