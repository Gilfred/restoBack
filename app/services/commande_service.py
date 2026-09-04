import uuid as uuid_mod

from uuid import UUID

from fastapi import HTTPException, status

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.commande import Commande
from app.models.commande_article import CommandeArticle
from app.models.user import User
from app.models.restaurant_user import RestaurantUser
from app.models.role import Role
from app.models.associations import UserRole
from app.models.boisson import Boisson
from app.models.repas import Repas

from app.enums import UserRestaurantStatus

from app.schemas.commande import CommandeCreate, CommandeUpdate


# SERVEUSES
def get_restaurant_waiters(db: Session, restaurant_id: UUID):
    """Retrieve all active waiters belonging to a restaurant."""

    ru_waiters = db.query(User).join(
        RestaurantUser,
        RestaurantUser.userId == User.id
    ).join(
        Role,
        RestaurantUser.roleId == Role.id
    ).filter(
        RestaurantUser.restaurantId == restaurant_id,
        RestaurantUser.status == UserRestaurantStatus.ACTIVE,
        func.upper(Role.name) == "WAITER"
    ).all()

    ur_waiters = db.query(User).join(
        UserRole,
        UserRole.userId == User.id
    ).join(
        Role,
        UserRole.roleId == Role.id
    ).filter(
        User.restaurantId == restaurant_id,
        User.isActive == True,
        func.upper(Role.name) == "WAITER"
    ).all()

    waiters_map = {u.id: u for u in ru_waiters + ur_waiters}

    return list(waiters_map.values())


# CREATION COMMANDE
def create_commande(
    db: Session,
    commande_data: CommandeCreate,
    restaurant_id: UUID
):
    # 1. Vérifier la serveuse
    waiter_user = db.query(User).filter(
        User.id == commande_data.userId
    ).first()

    if not waiter_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La serveuse sélectionnée n'existe pas"
        )

    # 2. Vérifier que la serveuse appartient au restaurant
    is_in_restaurant = False

    if waiter_user.restaurantId == restaurant_id:
        is_in_restaurant = True

    else:
        ru = db.query(RestaurantUser).filter(
            RestaurantUser.userId == waiter_user.id,
            RestaurantUser.restaurantId == restaurant_id,
            RestaurantUser.status == UserRestaurantStatus.ACTIVE
        ).first()

        if ru:
            is_in_restaurant = True

    if not is_in_restaurant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La serveuse sélectionnée n'appartient pas à votre restaurant"
        )

    # 3. Vérifier qu'il y a des articles
    if not commande_data.articles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La commande doit contenir au moins un article"
        )

    try:
        # 4. Créer la commande
        db_commande = Commande(
            restaurantId=restaurant_id,
            userId=commande_data.userId,
            numeroCommande=f"CMD-{uuid_mod.uuid4().hex[:8].upper()}",
            total=0.0
        )

        db.add(db_commande)
        db.flush()

        calculated_total = 0.0

        # 5. Traiter chaque article
        for article in commande_data.articles:

            boisson_id = article.boissonId
            repas_id = article.repasId
            qte = article.qte

            # Un article doit être soit une boisson soit un repas

            if boisson_id and repas_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Un article ne peut pas être à la fois une boisson et un repas"
                )

            if not boisson_id and not repas_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Chaque article doit avoir un boissonId ou un repasId"
                )

            # BOISSON

            if boisson_id:

                boisson = db.query(Boisson).filter(
                    Boisson.id == boisson_id,
                    Boisson.restaurantId == restaurant_id
                ).first()

                if not boisson:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="La boisson sélectionnée n'existe pas ou n'appartient pas à votre restaurant"
                    )

                prix_unitaire = boisson.prixVente

            # REPAS

            else:

                repas = db.query(Repas).filter(
                    Repas.id == repas_id,
                    Repas.restaurantId == restaurant_id
                ).first()

                if not repas:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Le repas sélectionné n'existe pas ou n'appartient pas à votre restaurant"
                    )

                prix_unitaire = repas.prix

            # Calcul du sous-total

            sous_total = qte * prix_unitaire

            calculated_total += sous_total

            # Création de l'article

            db_article = CommandeArticle(
                commandeId=db_commande.id,
                boissonId=boisson_id,
                repasId=repas_id,
                qte=qte,
                prixUnitaire=prix_unitaire,
                sousTotal=sous_total
            )

            db.add(db_article)

        # 6. Enregistrer le total calculé

        db_commande.total = calculated_total

        # 7. Valider la transaction

        db.commit()

        return get_commande(db, db_commande.id)

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur est survenue lors de la création de la commande"
        )


# LISTE DES COMMANDES D'UNE SERVEUSE
def get_my_commandes(db: Session, user_id: UUID):

    return db.query(Commande).options(
        joinedload(Commande.articles),
        joinedload(Commande.user)
    ).filter(
        Commande.userId == user_id,
        Commande.isActive == True
    ).order_by(
        Commande.createdAt.desc()
    ).all()


# LISTE DES COMMANDES DU RESTAURANT
def get_commandes(db: Session, restaurant_id: UUID):

    return db.query(Commande).options(
        joinedload(Commande.articles),
        joinedload(Commande.user)
    ).filter(
        Commande.restaurantId == restaurant_id,
        Commande.isActive == True
    ).order_by(
        Commande.createdAt.desc()
    ).all()


# UNE COMMANDE
def get_commande(db: Session, commande_id: UUID):

    return db.query(Commande).options(
        joinedload(Commande.articles),
        joinedload(Commande.user)
    ).filter(
        Commande.id == commande_id,
        Commande.isActive == True
    ).first()


# MODIFICATION COMMANDE
def update_commande(
    db: Session,
    commande_id: UUID,
    commande_data: CommandeUpdate
):

    db_commande = get_commande(db, commande_id)

    if db_commande:

        update_data = commande_data.model_dump(
            exclude_unset=True
        )

        for key, value in update_data.items():
            setattr(db_commande, key, value)

        db.commit()
        db.refresh(db_commande)

    return db_commande


# SUPPRESSION LOGIQUE
def delete_commande(
    db: Session,
    commande_id: UUID
):

    db_commande = get_commande(db, commande_id)

    if db_commande:

        db_commande.isActive = False

        db.commit()

    return db_commande