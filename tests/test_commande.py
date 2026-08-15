import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from fastapi import HTTPException
from app.schemas.commande import CommandeCreate, CommandeArticleCreate
from app.services.commande_service import create_commande, get_restaurant_waiters
from app.models.user import User

def test_create_commande_schema_optional_fields():
    # Verify CommandeCreate can be initialized without restaurantId, numeroCommande, or userId
    data = {
        "articles": [
            {"boissonId": str(uuid4()), "qte": 2, "prixUnitaire": 1500.0}
        ]
    }
    commande_in = CommandeCreate(**data)
    assert commande_in.restaurantId is None
    assert commande_in.numeroCommande is None
    assert commande_in.userId is None

def test_create_commande_waiter_not_found():
    db = MagicMock()
    db.query().filter().first.return_value = None
    restaurant_id = uuid4()
    waiter_id = uuid4()

    commande_in = CommandeCreate(
        userId=waiter_id,
        articles=[{"qte": 1, "prixUnitaire": 100.0}]
    )

    with pytest.raises(HTTPException) as exc_info:
        create_commande(db, commande_in, restaurant_id)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "La serveuse sélectionnée n'existe pas"

def test_create_commande_waiter_not_in_restaurant():
    db = MagicMock()
    mock_user = MagicMock(spec=User)
    mock_user.id = uuid4()
    mock_user.restaurantId = uuid4() # Different restaurant

    db.query().filter().first.return_value = mock_user
    db.query().filter().first.side_effect = [mock_user, None] # No RestaurantUser match either

    restaurant_id = uuid4()

    commande_in = CommandeCreate(
        userId=mock_user.id,
        articles=[{"qte": 1, "prixUnitaire": 100.0}]
    )

    with pytest.raises(HTTPException) as exc_info:
        create_commande(db, commande_in, restaurant_id)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "La serveuse sélectionnée n'appartient pas à votre restaurant"
