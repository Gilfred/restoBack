from sqlalchemy.orm import Session
from app.models.casier import Casier
from app.schemas.casier import CasierCreate
from uuid import UUID

def get_casiers(db: Session, restaurant_id: UUID):
    return db.query(Casier).filter(Casier.restaurantId == restaurant_id, Casier.isActive == True).all()

def create_casier(db: Session, casier_data: CasierCreate, restaurant_id: UUID):
    # Check if a casier of the same type already exists for this restaurant
    existing_casier = db.query(Casier).filter(
        Casier.typeCasier == casier_data.typeCasier,
        Casier.restaurantId == restaurant_id,
        Casier.isActive == True
    ).first()

    if existing_casier:
        return existing_casier

    db_casier = Casier(
        **casier_data.model_dump(),
        restaurantId=restaurant_id
    )
    db.add(db_casier)
    db.commit()
    db.refresh(db_casier)
    return db_casier
