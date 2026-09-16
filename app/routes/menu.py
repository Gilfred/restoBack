from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_session
from app.dependencies import get_user_restaurant_id, require_admin
from app.schemas.menu import (
    MenuDisplayResponse,
    MenuFamilleCreate, MenuFamilleUpdate, MenuFamilleResponse,
    MenuFamilleImageCreate, MenuFamilleImageUpdate, MenuFamilleImageResponse,
    MenuCategorieCreate, MenuCategorieUpdate, MenuCategorieResponse,
    MenuRepasCreate, MenuRepasUpdate, MenuRepasResponse,
    MenuBoissonCreate, MenuBoissonUpdate, MenuBoissonResponse,
    UploadCenterPresignRequest, UploadCenterPresignResponse,
    UploadCenterCompleteRequest, UploadCenterCompleteResponse
)
from app.services import menu_service, upload_center_service

router = APIRouter()

# ==========================================
# PUBLIC ENDPOINTS (No Authentication Required)
# ==========================================

@router.get("/display/{restaurant_id}", response_model=MenuDisplayResponse)
def get_public_menu_display(restaurant_id: UUID, db: Session = Depends(get_session)):
    """
    Endpoint public permettant de récupérer l'affichage complet du menu d'un restaurant
    (Restaurant, Familles, Images, Catégories, Repas, Boissons).
    """
    return menu_service.get_full_restaurant_menu(db, restaurant_id)


# ==========================================
# UPLOADCENTER INTEGRATION ENDPOINTS
# ==========================================

@router.post("/upload-center/presign", response_model=UploadCenterPresignResponse)
def presign_upload_center_image(
    req: UploadCenterPresignRequest,
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    """
    Génère une URL d'upload présignée via UploadCenter (avec visibility='public').
    Le frontend envoie le fichier directement à `upload_url` via HTTP PUT.
    """
    return upload_center_service.presign_upload(
        filename=req.filename,
        size_bytes=req.sizeBytes,
        mime_type=req.mimeType
    )

@router.post("/upload-center/complete", response_model=UploadCenterCompleteResponse)
def complete_upload_center_image(
    req: UploadCenterCompleteRequest,
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    """
    Confirme l'upload auprès d'UploadCenter et retourne l'objet FileOut contenant l'URL publique de l'image.
    """
    return upload_center_service.complete_upload(file_id=req.file_id)


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


# --- Menu Famille Images (UploadCenter References) ---

@router.post("/famille-images", response_model=MenuFamilleImageResponse, status_code=status.HTTP_201_CREATED)
def create_famille_image(
    image_data: MenuFamilleImageCreate,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    return menu_service.create_menu_famille_image(db, image_data, restaurant_id)

@router.patch("/famille-images/{image_id}", response_model=MenuFamilleImageResponse)
def update_famille_image(
    image_id: UUID,
    image_data: MenuFamilleImageUpdate,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    image = menu_service.update_menu_famille_image(db, image_id, image_data, restaurant_id)
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


# --- Menu Categoriés ---

@router.post("/categories", response_model=MenuCategorieResponse, status_code=status.HTTP_201_CREATED)
def create_categorie(
    cat_data: MenuCategorieCreate,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    return menu_service.create_menu_categorie(db, cat_data, restaurant_id)

@router.patch("/categories/{categorie_id}", response_model=MenuCategorieResponse)
def update_categorie(
    categorie_id: UUID,
    cat_data: MenuCategorieUpdate,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    cat = menu_service.update_menu_categorie(db, categorie_id, cat_data, restaurant_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return cat

@router.delete("/categories/{categorie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_categorie(
    categorie_id: UUID,
    db: Session = Depends(get_session),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
    admin_user = Depends(require_admin)
):
    if not menu_service.delete_menu_categorie(db, categorie_id, restaurant_id):
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
