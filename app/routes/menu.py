from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_session
from app.dependencies import (
    get_user_restaurant_id,
    get_optional_user_restaurant_id,
    require_admin,
    require_superadmin
)
from app.enums import MenuCategorieNom
from app.schemas.menu import (
    MenuDisplayResponse,
    MenuFamilleCreate, MenuFamilleUpdate, MenuFamilleResponse,
    MenuFamilleImageResponse,
    MenuCategorieCreate, MenuCategorieUpdate, MenuCategorieResponse,
    MenuRepasCreate, MenuRepasUpdate, MenuRepasResponse,
    MenuBoissonCreate, MenuBoissonUpdate, MenuBoissonResponse,
    MenuFamilleImageUploadResponse
)
from app.services import menu_service, cloudinary_service

router = APIRouter()

# PUBLIC ENDPOINTS (No Authentication Required)

@router.get("/display", response_model=MenuDisplayResponse)
def get_public_menu_display(
    db: Session = Depends(get_session)
):
    """
    Endpoint public permettant de récupérer l'affichage complet du menu d'un restaurant
    (Restaurant, Familles, Images, Catégories, Repas, Boissons).
    """
    return menu_service.get_full_restaurant_menu(db)

# IMAGE UPLOAD ENDPOINT (Cloudinary)

@router.post("/upload", response_model=MenuFamilleImageUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_menu_image(
    file: UploadFile = File(...),
    famille_id: UUID = Form(...),
    ordre: int = Form(0),
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    """
    Téléverse une image vers Cloudinary et enregistre la ligne MenuFamilleImage en BDD en une seule opération.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seuls les fichiers de type image (JPEG, PNG, WEBP, etc.) sont autorisés"
        )

    contents = file.file.read()
    filename = file.filename or "image.png"

    return menu_service.upload_and_create_famille_image(
        db=db,
        famille_id=famille_id,
        file_bytes=contents,
        filename=filename,
        ordre=ordre,
        restaurant_id=restaurant_id
    )


# ==========================================
# AUTHENTICATED & SCOPED MANAGEMENT ENDPOINTS
# ==========================================

# --- Menu Familles ---

@router.post("/familles", response_model=MenuFamilleResponse, status_code=status.HTTP_201_CREATED)
def create_famille(
    famille_data: MenuFamilleCreate,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    return menu_service.create_menu_famille(db, famille_data, restaurant_id)

@router.get("/familles", response_model=List[MenuFamilleResponse])
def list_familles(
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id)
):
    return menu_service.get_menu_familles(db, restaurant_id)

@router.get("/familles/{famille_id}", response_model=MenuFamilleResponse)
def get_famille(
    famille_id: UUID,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id)
):
    famille = menu_service.get_menu_famille(db, famille_id, restaurant_id)
    if not famille:
        raise HTTPException(status_code=404, detail="Famille non trouvée")
    return famille

@router.patch("/familles/{famille_id}", response_model=MenuFamilleResponse)
def update_famille(
    famille_id: UUID,
    famille_data: MenuFamilleUpdate,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    famille = menu_service.update_menu_famille(db, famille_id, famille_data, restaurant_id)
    if not famille:
        raise HTTPException(status_code=404, detail="Famille non trouvée")
    return famille

@router.delete("/familles/{famille_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_famille(
    famille_id: UUID,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    if not menu_service.delete_menu_famille(db, famille_id, restaurant_id):
        raise HTTPException(status_code=404, detail="Famille non trouvée")
    return None


# --- Menu Famille Images ---

@router.patch("/famille-images/{image_id}", response_model=MenuFamilleImageResponse)
def update_famille_image(
    image_id: UUID,
    file: UploadFile = File(...),
    ordre: Optional[int] = Form(None),
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seuls les fichiers de type image (JPEG, PNG, WEBP, etc.) sont autorisés"
        )

    contents = file.file.read()
    filename = file.filename or "image.png"

    image = menu_service.update_menu_famille_image_file(
        db=db,
        image_id=image_id,
        file_bytes=contents,
        filename=filename,
        ordre=ordre,
        restaurant_id=restaurant_id
    )
    if not image:
        raise HTTPException(status_code=404, detail="Image non trouvée")
    return image

@router.delete("/famille-images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_famille_image(
    image_id: UUID,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    if not menu_service.delete_menu_famille_image(db, image_id, restaurant_id):
        raise HTTPException(status_code=404, detail="Image non trouvée")
    return None


# --- Menu Catégories ---

@router.post("/categories", response_model=MenuCategorieResponse, status_code=status.HTTP_201_CREATED)
def create_categorie(
    cat_data: MenuCategorieCreate,
    db: Session = Depends(get_session),
    superadmin_user = Depends(require_superadmin)
):
    """
    Création d'une catégorie (réservé au SUPERADMIN).
    """
    return menu_service.create_menu_categorie(db, cat_data)

@router.get("/categories", response_model=List[MenuCategorieResponse])
def list_categories(
    db: Session = Depends(get_session),
    restaurant_id: Optional[UUID] = Depends(get_optional_user_restaurant_id)
):
    """
    Liste des catégories visible pour tous les restaurants.
    """
    return menu_service.get_menu_categories(db, restaurant_id)

@router.get("/categories/{categorie_id}", response_model=MenuCategorieResponse)
def get_categorie(
    categorie_id: UUID,
    db: Session = Depends(get_session),
    restaurant_id: Optional[UUID] = Depends(get_optional_user_restaurant_id)
):
    """
    Détail d'une catégorie.
    """
    cat = menu_service.get_menu_categorie_by_id(db, categorie_id, restaurant_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return cat

@router.patch("/categories/{categorie_id}", response_model=MenuCategorieResponse)
def update_categorie(
    categorie_id: UUID,
    cat_data: MenuCategorieUpdate,
    db: Session = Depends(get_session),
    superadmin_user = Depends(require_superadmin)
):
    """
    Mise à jour d'une catégorie (réservé au SUPERADMIN).
    """
    cat = menu_service.update_menu_categorie(db, categorie_id, cat_data)
    if not cat:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return cat

@router.delete("/categories/{categorie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_categorie(
    categorie_id: UUID,
    db: Session = Depends(get_session),
    superadmin_user = Depends(require_superadmin)
):
    """
    Suppression d'une catégorie (réservé au SUPERADMIN).
    """
    if not menu_service.delete_menu_categorie(db, categorie_id):
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return None


# --- Menu Repas (Association Repas <-> Categorie) ---

@router.post("/repas", response_model=MenuRepasResponse, status_code=status.HTTP_201_CREATED)
def create_menu_repas(
    mr_data: MenuRepasCreate,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    return menu_service.create_menu_repas(db, mr_data, restaurant_id)

@router.patch("/repas/{menu_repas_id}", response_model=MenuRepasResponse)
def update_menu_repas(
    menu_repas_id: UUID,
    mr_data: MenuRepasUpdate,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    mr = menu_service.update_menu_repas(db, menu_repas_id, mr_data, restaurant_id)
    if not mr:
        raise HTTPException(status_code=404, detail="Association Repas non trouvée")
    return mr

@router.delete("/repas/{menu_repas_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_repas(
    menu_repas_id: UUID,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    if not menu_service.delete_menu_repas(db, menu_repas_id, restaurant_id):
        raise HTTPException(status_code=404, detail="Association Repas non trouvée")
    return None


# --- Menu Boisson ---

@router.post("/boissons", response_model=MenuBoissonResponse, status_code=status.HTTP_201_CREATED)
def create_menu_boisson(
    mb_data: MenuBoissonCreate,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    return menu_service.create_menu_boisson(db, mb_data, restaurant_id)

@router.patch("/boissons/{menu_boisson_id}", response_model=MenuBoissonResponse)
def update_menu_boisson(
    menu_boisson_id: UUID,
    mb_data: MenuBoissonUpdate,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    mb = menu_service.update_menu_boisson(db, menu_boisson_id, mb_data, restaurant_id)
    if not mb:
        raise HTTPException(status_code=404, detail="Élément boisson de menu non trouvé")
    return mb

@router.delete("/boissons/{menu_boisson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_boisson(
    menu_boisson_id: UUID,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    if not menu_service.delete_menu_boisson(db, menu_boisson_id, restaurant_id):
        raise HTTPException(status_code=404, detail="Élément boisson de menu non trouvé")
    return None
