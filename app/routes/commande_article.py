from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_session
from app.schemas.commande import CommandeArticleResponse, CommandeArticleCreate, CommandeArticleUpdate
from app.services import commande_article_service
from app.dependencies import get_current_user, check_permissions

router = APIRouter()

@router.get("/commande/{commande_id}", response_model=List[CommandeArticleResponse])
def read_commande_articles(
    commande_id: UUID,
    db: Session = Depends(get_session),
    current_user = Depends(check_permissions("view_orders"))
):
    return commande_article_service.get_commande_articles(db, commande_id)

@router.get("/{article_id}", response_model=CommandeArticleResponse)
def read_commande_article(
    article_id: UUID,
    db: Session = Depends(get_session),
    current_user = Depends(check_permissions("view_orders"))
):
    db_article = commande_article_service.get_commande_article(db, article_id)
    if db_article is None:
        raise HTTPException(status_code=404, detail="Article de commande non trouvé")
    return db_article

@router.post("/{commande_id}", response_model=CommandeArticleResponse)
def create_commande_article(
    commande_id: UUID,
    article_data: CommandeArticleCreate,
    db: Session = Depends(get_session),
    current_user = Depends(check_permissions("create_orders"))
):
    return commande_article_service.create_commande_article(db, article_data, commande_id)

@router.put("/{article_id}", response_model=CommandeArticleResponse)
def update_commande_article(
    article_id: UUID,
    article_data: CommandeArticleUpdate,
    db: Session = Depends(get_session),
    current_user = Depends(check_permissions("update_orders"))
):
    db_article = commande_article_service.update_commande_article(db, article_id, article_data)
    if db_article is None:
        raise HTTPException(status_code=404, detail="Article de commande non trouvé")
    return db_article

@router.delete("/{article_id}")
def delete_commande_article(
    article_id: UUID,
    db: Session = Depends(get_session),
    current_user = Depends(check_permissions("update_orders"))
):
    db_article = commande_article_service.delete_commande_article(db, article_id)
    if db_article is None:
        raise HTTPException(status_code=404, detail="Article de commande non trouvé")
    return {"message": "Article supprimé avec succès (soft delete)"}
