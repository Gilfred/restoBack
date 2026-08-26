from sqlalchemy.orm import Session
from app.models.appro_boisson import ApproBoisson
from app.models.boisson import Boisson
from app.models.casier import Casier
from app.enums import CasierType
from app.schemas.appro_boisson import ApproBoissonCreate, ApproBoissonUpdate
from uuid import UUID
from fastapi import HTTPException

CASIER_CAPACITY = {
    CasierType.T12: 12,
    CasierType.T20: 20,
    CasierType.T24: 24,
}

def get_casier_capacity(casier_type: CasierType) -> int:
    if casier_type in CASIER_CAPACITY:
        return CASIER_CAPACITY[casier_type]
    val = str(casier_type.value if hasattr(casier_type, 'value') else casier_type).upper().replace("T", "")
    try:
        return int(val)
    except ValueError:
        return 0

def create_appro_boisson(db: Session, appro_data: ApproBoissonCreate, restaurant_id: UUID):
    # Verify boisson belongs to restaurant
    boisson = db.query(Boisson).filter(Boisson.id == appro_data.boissonId, Boisson.restaurantId == restaurant_id).first()
    if not boisson:
        raise HTTPException(status_code=400, detail="Boisson not found or does not belong to your restaurant")

    # Verify casier belongs to restaurant
    casier = db.query(Casier).filter(Casier.id == appro_data.casierId, Casier.restaurantId == restaurant_id).first()
    if not casier:
        raise HTTPException(status_code=400, detail="Casier not found or does not belong to your restaurant")

    capacity = get_casier_capacity(casier.typeCasier)
    added_bottles = appro_data.nbreCasier * capacity
    if boisson.stock is None:
        boisson.stock = 0
    boisson.stock += added_bottles

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

        old_casier = db_appro.casier
        old_nbre_casier = db_appro.nbreCasier
        old_capacity = get_casier_capacity(old_casier.typeCasier) if old_casier else 0
        old_bottles = old_nbre_casier * old_capacity

        new_nbre_casier = update_dict.get("nbreCasier", db_appro.nbreCasier)
        if "casierId" in update_dict:
            casier = db.query(Casier).filter(Casier.id == update_dict["casierId"], Casier.restaurantId == restaurant_id).first()
            if not casier:
                raise HTTPException(status_code=400, detail="Casier not found or does not belong to your restaurant")
            new_capacity = get_casier_capacity(casier.typeCasier)
        else:
            new_capacity = old_capacity

        new_bottles = new_nbre_casier * new_capacity

        boisson = db_appro.boisson
        if boisson:
            if boisson.stock is None:
                boisson.stock = 0
            boisson.stock += (new_bottles - old_bottles)

        for key, value in update_dict.items():
            setattr(db_appro, key, value)
        db.commit()
        db.refresh(db_appro)
    return db_appro

def delete_appro_boisson(db: Session, appro_id: UUID, restaurant_id: UUID):
    db_appro = get_appro_boisson(db, appro_id, restaurant_id)
    if db_appro:
        if db_appro.isActive:
            capacity = get_casier_capacity(db_appro.casier.typeCasier) if db_appro.casier else 0
            removed_bottles = db_appro.nbreCasier * capacity
            if db_appro.boisson:
                if db_appro.boisson.stock is None:
                    db_appro.boisson.stock = 0
                db_appro.boisson.stock -= removed_bottles
            db_appro.isActive = False
            db.commit()
    return db_appro
