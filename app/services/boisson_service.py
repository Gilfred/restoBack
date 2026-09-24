from sqlalchemy.orm import Session, joinedload
from app.models.boisson import Boisson
from app.models.menu_boisson import MenuBoisson
from app.models.menu_boisson_famille import MenuBoissonFamille
from app.schemas.boisson import BoissonCreate, BoissonUpdate
from uuid import UUID
from typing import Optional

def create_boisson(db: Session, boisson_data: BoissonCreate, restaurant_id: UUID):
    db_boisson = Boisson(
        **boisson_data.model_dump(),
        restaurantId=restaurant_id
    )
    db.add(db_boisson)
    db.commit()
    db.refresh(db_boisson)
    return db_boisson

def get_boissons(db: Session, restaurant_id: Optional[UUID] = None):
    if restaurant_id:
        return db.query(Boisson).filter(Boisson.restaurantId == restaurant_id).all()
    return db.query(Boisson).all()

def get_boisson(db: Session, boisson_id: UUID, restaurant_id: Optional[UUID] = None):
    query = db.query(Boisson).filter(Boisson.id == boisson_id)
    if restaurant_id:
        query = query.filter(Boisson.restaurantId == restaurant_id)
    return query.first()

def get_boissons_with_family_and_images(db: Session, restaurant_id: UUID):
    boissons = db.query(Boisson).filter(Boisson.restaurantId == restaurant_id).all()

    menu_boissons = (
        db.query(MenuBoisson)
        .join(MenuBoissonFamille, MenuBoisson.menuBoissonFamilleId == MenuBoissonFamille.id)
        .filter(MenuBoissonFamille.restaurantId == restaurant_id)
        .options(
            joinedload(MenuBoisson.menuBoissonFamille).joinedload(MenuBoissonFamille.images)
        )
        .all()
    )

    boisson_famille_map = {mb.boissonId: mb.menuBoissonFamille for mb in menu_boissons}

    results = []
    for boisson in boissons:
        famille = boisson_famille_map.get(boisson.id)
        images = famille.images if famille and famille.images else []
        results.append({
            "boisson": boisson,
            "famille": famille,
            "images": images
        })
    return results

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
