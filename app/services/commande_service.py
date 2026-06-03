from sqlalchemy.orm import Session
from app.models.commande import Commande
from app.models.commande_article import CommandeArticle
from app.schemas.commande import CommandeCreate, CommandeUpdate
from uuid import UUID

def create_commande(db: Session, commande_data: CommandeCreate):
    data = commande_data.model_dump()
    articles_data = data.pop("articles")

    db_commande = Commande(**data)
    db.add(db_commande)
    db.flush() # To get the ID

    for art_data in articles_data:
        sous_total = art_data["qte"] * art_data["prixUnitaire"]
        db_article = CommandeArticle(
            **art_data,
            commandeId=db_commande.id,
            sousTotal=sous_total
        )
        db.add(db_article)

    db.commit()
    db.refresh(db_commande)
    return db_commande

def get_commandes(db: Session, restaurant_id: UUID):
    return db.query(Commande).filter(Commande.restaurantId == restaurant_id).all()

def get_commande(db: Session, commande_id: UUID):
    return db.query(Commande).filter(Commande.id == commande_id).first()

def update_commande(db: Session, commande_id: UUID, commande_data: CommandeUpdate):
    db_commande = get_commande(db, commande_id)
    if db_commande:
        for key, value in commande_data.model_dump(exclude_unset=True).items():
            setattr(db_commande, key, value)
        db.commit()
        db.refresh(db_commande)
    return db_commande

def delete_commande(db: Session, commande_id: UUID):
    db_commande = get_commande(db, commande_id)
    if db_commande:
        # Cascade delete is usually handled by DB or relationship, but let's be explicit if needed
        # In this project, let's assume standard behavior.
        db.delete(db_commande)
        db.commit()
    return db_commande
