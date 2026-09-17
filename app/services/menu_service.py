from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.restaurant import Restaurant
from app.models.menu_famille import MenuFamille
from app.models.menu_famille_image import MenuFamilleImage
from app.models.menu_categorie import MenuCategorie
from app.models.menu_repas import MenuRepas
from app.models.menu_boisson import MenuBoisson
from app.models.repas import Repas
from app.models.boisson import Boisson
from app.schemas.menu import (
    MenuFamilleCreate, MenuFamilleUpdate,
    MenuFamilleImageUpdate,
    MenuRepasCreate, MenuRepasUpdate,
    MenuBoissonCreate, MenuBoissonUpdate
)
from app.services import cloudinary_service


# --- Full Menu Display Service ---
def get_full_restaurant_menu(db: Session):
    restaurants = db.query(Restaurant).filter(Restaurant.isActive == True).all()

    restaurant_menus = []
    for restaurant in restaurants:
        target_restaurant_id = restaurant.id

        familles = (
            db.query(MenuFamille)
            .filter(MenuFamille.restaurantId == target_restaurant_id)
            .options(
                joinedload(MenuFamille.images),
                joinedload(MenuFamille.categories)
                .joinedload(MenuCategorie.repasList)
                .joinedload(MenuRepas.repas)
            )
            .order_by(MenuFamille.ordre.asc())
            .all()
        )

        for famille in familles:
            famille.images.sort(key=lambda x: x.ordre or 0)
            famille.categories.sort(key=lambda x: x.ordre or 0)
            for cat in famille.categories:
                cat.repasList.sort(key=lambda x: x.ordre or 0)

        boissons = (
            db.query(MenuBoisson)
            .join(Boisson, MenuBoisson.boissonId == Boisson.id)
            .filter(Boisson.restaurantId == target_restaurant_id)
            .options(joinedload(MenuBoisson.boisson))
            .order_by(MenuBoisson.ordre.asc())
            .all()
        )

        restaurant_menus.append({
            "restaurant": restaurant,
            "familles": familles,
            "boissons": boissons
        })

    return {
        "restaurants": restaurant_menus
    }


# --- MenuFamille Services ---
def create_menu_famille(db: Session, famille_data: MenuFamilleCreate, restaurant_id: UUID) -> MenuFamille:
    famille = MenuFamille(
        restaurantId=restaurant_id,
        nom=famille_data.nom,
        ordre=famille_data.ordre or 0
    )
    db.add(famille)
    db.commit()
    db.refresh(famille)
    return famille

def get_menu_familles(db: Session, restaurant_id: UUID) -> List[MenuFamille]:
    return (
        db.query(MenuFamille)
        .filter(MenuFamille.restaurantId == restaurant_id)
        .order_by(MenuFamille.ordre.asc())
        .all()
    )

def get_menu_famille(db: Session, famille_id: UUID, restaurant_id: UUID) -> Optional[MenuFamille]:
    return (
        db.query(MenuFamille)
        .filter(MenuFamille.id == famille_id, MenuFamille.restaurantId == restaurant_id)
        .first()
    )

def update_menu_famille(db: Session, famille_id: UUID, famille_data: MenuFamilleUpdate, restaurant_id: UUID) -> Optional[MenuFamille]:
    famille = get_menu_famille(db, famille_id, restaurant_id)
    if not famille:
        return None
    if famille_data.nom is not None:
        famille.nom = famille_data.nom
    if famille_data.ordre is not None:
        famille.ordre = famille_data.ordre
    db.commit()
    db.refresh(famille)
    return famille

def delete_menu_famille(db: Session, famille_id: UUID, restaurant_id: UUID) -> bool:
    famille = get_menu_famille(db, famille_id, restaurant_id)
    if not famille:
        return False
    db.delete(famille)
    db.commit()
    return True


# --- MenuFamilleImage Services ---
def upload_and_create_famille_image(
    db: Session,
    famille_id: UUID,
    file_bytes: bytes,
    filename: str,
    ordre: int,
    restaurant_id: UUID
) -> dict:
    # 1. Verify famille exists and belongs to user's restaurant BEFORE uploading
    famille = get_menu_famille(db, famille_id, restaurant_id)
    if not famille:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Famille de menu non trouvée pour ce restaurant"
        )

    # 2. Upload image to Cloudinary
    res = cloudinary_service.upload_image(file_bytes=file_bytes, filename=filename)
    image_url = res.get("url")
    public_id = res.get("public_id")

    # 3. Create MenuFamilleImage record in DB
    image = MenuFamilleImage(
        familleId=famille_id,
        imageUrl=image_url,
        ordre=ordre or 0
    )

    try:
        db.add(image)
        db.commit()
        db.refresh(image)
        return {
            "id": image.id,
            "familleId": image.familleId,
            "imageUrl": image.imageUrl,
            "ordre": image.ordre,
            "public_id": public_id
        }
    except Exception as e:
        db.rollback()
        if public_id:
            cloudinary_service.delete_image(public_id)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Échec de l'enregistrement de l'image en base de données: {str(e)}"
        )


def update_menu_famille_image_file(
    db: Session,
    image_id: UUID,
    file_bytes: bytes,
    filename: str,
    ordre: Optional[int],
    restaurant_id: UUID
) -> Optional[MenuFamilleImage]:
    image = (
        db.query(MenuFamilleImage)
        .join(MenuFamille, MenuFamilleImage.familleId == MenuFamille.id)
        .filter(MenuFamilleImage.id == image_id, MenuFamille.restaurantId == restaurant_id)
        .first()
    )
    if not image:
        return None

    old_image_url = image.imageUrl

    res = cloudinary_service.upload_image(file_bytes=file_bytes, filename=filename)
    new_url = res.get("url")
    new_public_id = res.get("public_id")

    image.imageUrl = new_url
    if ordre is not None:
        image.ordre = ordre

    try:
        db.commit()
        db.refresh(image)

        old_public_id = cloudinary_service.extract_public_id_from_url(old_image_url)
        if old_public_id:
            cloudinary_service.delete_image(old_public_id)

        return image
    except Exception as e:
        db.rollback()
        if new_public_id:
            cloudinary_service.delete_image(new_public_id)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Échec de la mise à jour de l'image en base de données: {str(e)}"
        )

def delete_menu_famille_image(db: Session, image_id: UUID, restaurant_id: UUID) -> bool:
    image = (
        db.query(MenuFamilleImage)
        .join(MenuFamille, MenuFamilleImage.familleId == MenuFamille.id)
        .filter(MenuFamilleImage.id == image_id, MenuFamille.restaurantId == restaurant_id)
        .first()
    )
    if not image:
        return False
    db.delete(image)
    db.commit()
    return True


# --- MenuCategorie Services ---
def get_menu_categorie(db: Session, categorie_id: UUID, restaurant_id: UUID) -> Optional[MenuCategorie]:
    return (
        db.query(MenuCategorie)
        .join(MenuFamille, MenuCategorie.menuFamilleId == MenuFamille.id)
        .filter(MenuCategorie.id == categorie_id, MenuFamille.restaurantId == restaurant_id)
        .first()
    )


# --- MenuRepas Services ---
def create_menu_repas(db: Session, mr_data: MenuRepasCreate, restaurant_id: UUID) -> MenuRepas:
    categorie = get_menu_categorie(db, mr_data.menuCategorieId, restaurant_id)
    if not categorie:
        raise HTTPException(status_code=404, detail="Catégorie de menu non trouvée pour ce restaurant")
    
    repas = db.query(Repas).filter(Repas.id == mr_data.repasId, Repas.restaurantId == restaurant_id).first()
    if not repas:
        raise HTTPException(status_code=404, detail="Repas non trouvé pour ce restaurant")
    
    menu_repas = MenuRepas(
        menuCategorieId=mr_data.menuCategorieId,
        repasId=mr_data.repasId,
        ordre=mr_data.ordre or 0
    )
    db.add(menu_repas)
    db.commit()
    db.refresh(menu_repas)
    return menu_repas

def get_menu_repas(db: Session, menu_repas_id: UUID, restaurant_id: UUID) -> Optional[MenuRepas]:
    return (
        db.query(MenuRepas)
        .join(MenuCategorie, MenuRepas.menuCategorieId == MenuCategorie.id)
        .join(MenuFamille, MenuCategorie.menuFamilleId == MenuFamille.id)
        .filter(MenuRepas.id == menu_repas_id, MenuFamille.restaurantId == restaurant_id)
        .first()
    )

def update_menu_repas(db: Session, menu_repas_id: UUID, mr_data: MenuRepasUpdate, restaurant_id: UUID) -> Optional[MenuRepas]:
    menu_repas = get_menu_repas(db, menu_repas_id, restaurant_id)
    if not menu_repas:
        return None
    if mr_data.menuCategorieId is not None:
        categorie = get_menu_categorie(db, mr_data.menuCategorieId, restaurant_id)
        if not categorie:
            raise HTTPException(status_code=404, detail="Catégorie de menu non trouvée pour ce restaurant")
        menu_repas.menuCategorieId = mr_data.menuCategorieId
    if mr_data.repasId is not None:
        repas = db.query(Repas).filter(Repas.id == mr_data.repasId, Repas.restaurantId == restaurant_id).first()
        if not repas:
            raise HTTPException(status_code=404, detail="Repas non trouvé pour ce restaurant")
        menu_repas.repasId = mr_data.repasId
    if mr_data.ordre is not None:
        menu_repas.ordre = mr_data.ordre
    db.commit()
    db.refresh(menu_repas)
    return menu_repas

def delete_menu_repas(db: Session, menu_repas_id: UUID, restaurant_id: UUID) -> bool:
    menu_repas = get_menu_repas(db, menu_repas_id, restaurant_id)
    if not menu_repas:
        return False
    db.delete(menu_repas)
    db.commit()
    return True


# --- MenuBoisson Services ---
def create_menu_boisson(db: Session, mb_data: MenuBoissonCreate, restaurant_id: UUID) -> MenuBoisson:
    boisson = db.query(Boisson).filter(Boisson.id == mb_data.boissonId, Boisson.restaurantId == restaurant_id).first()
    if not boisson:
        raise HTTPException(status_code=404, detail="Boisson non trouvée pour ce restaurant")
    
    menu_boisson = MenuBoisson(
        boissonId=mb_data.boissonId,
        ordre=mb_data.ordre or 0,
        imageUrl=mb_data.imageUrl
    )
    db.add(menu_boisson)
    db.commit()
    db.refresh(menu_boisson)
    return menu_boisson

def get_menu_boisson(db: Session, menu_boisson_id: UUID, restaurant_id: UUID) -> Optional[MenuBoisson]:
    return (
        db.query(MenuBoisson)
        .join(Boisson, MenuBoisson.boissonId == Boisson.id)
        .filter(MenuBoisson.id == menu_boisson_id, Boisson.restaurantId == restaurant_id)
        .first()
    )

def update_menu_boisson(db: Session, menu_boisson_id: UUID, mb_data: MenuBoissonUpdate, restaurant_id: UUID) -> Optional[MenuBoisson]:
    menu_boisson = get_menu_boisson(db, menu_boisson_id, restaurant_id)
    if not menu_boisson:
        return None
    if mb_data.boissonId is not None:
        boisson = db.query(Boisson).filter(Boisson.id == mb_data.boissonId, Boisson.restaurantId == restaurant_id).first()
        if not boisson:
            raise HTTPException(status_code=404, detail="Boisson non trouvée pour ce restaurant")
        menu_boisson.boissonId = mb_data.boissonId
    if mb_data.ordre is not None:
        menu_boisson.ordre = mb_data.ordre
    if mb_data.imageUrl is not None:
        menu_boisson.imageUrl = mb_data.imageUrl
    db.commit()
    db.refresh(menu_boisson)
    return menu_boisson

def delete_menu_boisson(db: Session, menu_boisson_id: UUID, restaurant_id: UUID) -> bool:
    menu_boisson = get_menu_boisson(db, menu_boisson_id, restaurant_id)
    if not menu_boisson:
        return False
    db.delete(menu_boisson)
    db.commit()
    return True
