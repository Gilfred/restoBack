from sqlalchemy.orm import Session
from app.models.appro_boisson import ApproBoisson
from app.schemas.appro_boisson import ApproBoissonCreate, ApproBoissonUpdate
from uuid import UUID

def create_appro_boisson(db: Session, appro_data: ApproBoissonCreate):
    db_appro = ApproBoisson(**appro_data.model_dump())
    db.add(db_appro)
    db.commit()
    db.refresh(db_appro)
    return db_appro

def get_appro_boissons(db: Session):
    return db.query(ApproBoisson).filter(ApproBoisson.isActive == True).all()

def get_appro_boisson(db: Session, appro_id: UUID):
    return db.query(ApproBoisson).filter(ApproBoisson.id == appro_id, ApproBoisson.isActive == True).first()

def update_appro_boisson(db: Session, appro_id: UUID, appro_data: ApproBoissonUpdate):
    db_appro = get_appro_boisson(db, appro_id)
    if db_appro:
        for key, value in appro_data.model_dump(exclude_unset=True).items():
            setattr(db_appro, key, value)
        db.commit()
        db.refresh(db_appro)
    return db_appro

def delete_appro_boisson(db: Session, appro_id: UUID):
    db_appro = get_appro_boisson(db, appro_id)
    if db_appro:
        db_appro.isActive = False
        db.commit()
    return db_appro
