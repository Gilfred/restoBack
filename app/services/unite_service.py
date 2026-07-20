from sqlalchemy.orm import Session
from app.models.unite import Unite
from app.schemas.unite import UniteCreate
from uuid import UUID

def get_unites(db: Session, restaurant_id: UUID):
    return db.query(Unite).filter(Unite.restaurantId == restaurant_id, Unite.isActive == True).all()

def create_unite(db: Session, unite_data: UniteCreate, restaurant_id: UUID):
    db_unite = Unite(
        **unite_data.model_dump(exclude={"restaurantId"}),
        restaurantId=restaurant_id
    )
    db.add(db_unite)
    db.commit()
    db.refresh(db_unite)
    return db_unite
