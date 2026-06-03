from sqlalchemy.orm import Session
from app.models.commande_article import CommandeArticle
from app.schemas.commande import CommandeArticleCreate, CommandeArticleUpdate
from uuid import UUID

def get_commande_article(db: Session, article_id: UUID):
    return db.query(CommandeArticle).filter(CommandeArticle.id == article_id, CommandeArticle.isActive == True).first()

def get_commande_articles(db: Session, commande_id: UUID):
    return db.query(CommandeArticle).filter(CommandeArticle.commandeId == commande_id, CommandeArticle.isActive == True).all()

def create_commande_article(db: Session, article_data: CommandeArticleCreate, commande_id: UUID):
    db_article = CommandeArticle(
        **article_data.model_dump(),
        commandeId=commande_id,
        sousTotal=article_data.qte * article_data.prixUnitaire
    )
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

def update_commande_article(db: Session, article_id: UUID, article_data: CommandeArticleUpdate):
    db_article = get_commande_article(db, article_id)
    if db_article:
        for key, value in article_data.model_dump(exclude_unset=True).items():
            setattr(db_article, key, value)

        # Recalculate sousTotal if qte or prixUnitaire changed
        db_article.sousTotal = (db_article.qte or 0) * (db_article.prixUnitaire or 0.0)
        db.commit()
        db.refresh(db_article)
    return db_article

def delete_commande_article(db: Session, article_id: UUID):
    db_article = get_commande_article(db, article_id)
    if db_article:
        db_article.isActive = False
        db.commit()
    return db_article
