import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.database import get_session
from app.dependencies import get_current_user, require_manager_cashier, get_user_restaurant_id
from app.models.user import User
from app.models.boisson import Boisson
from app.models.repas import Repas
from app.models.commande import Commande
from app.models.commande_article import CommandeArticle
from app.enums import CommandeStatut
from app.schemas.commande import CommandeCreate, CommandeArticleCreate, CommandeUpdate
from app.services.commande_service import (
    create_commande,
    get_restaurant_waiters,
    get_my_commandes,
    get_commandes,
    get_commande,
    update_commande,
    delete_commande,
)

@pytest.fixture
def client():
    return TestClient(app)

class MockQuery:
    def __init__(self, items=None):
        if items is None:
            self.items = []
        elif isinstance(items, list):
            self.items = items
        else:
            self.items = [items]

    def options(self, *args, **kwargs):
        return self

    def join(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self.items[0] if self.items else None

    def all(self):
        return self.items


# --- TESTS SCHÉMAS & LOGIQUE SERVICE ---

def test_create_commande_schema_requires_user_id():
    # Verify CommandeCreate requires userId
    boisson_id = uuid4()
    with pytest.raises(ValidationError):
        CommandeCreate(
            articles=[{"boissonId": str(boisson_id), "qte": 2}]
        )

    # Valid schema initialization
    user_id = uuid4()
    commande_in = CommandeCreate(
        userId=user_id,
        articles=[{"boissonId": str(boisson_id), "qte": 2}]
    )
    assert commande_in.userId == user_id
    assert len(commande_in.articles) == 1


def test_create_commande_generates_formatted_numero_commande():
    db = MagicMock()
    mock_user = MagicMock(spec=User)
    mock_user.id = uuid4()
    restaurant_id = uuid4()
    mock_user.restaurantId = restaurant_id

    boisson_id = uuid4()
    mock_boisson = MagicMock(spec=Boisson)
    mock_boisson.id = boisson_id
    mock_boisson.restaurantId = restaurant_id
    mock_boisson.prixVente = 500.0

    def query_side_effect(model):
        q = MagicMock()
        if model == User:
            q.filter().first.return_value = mock_user
        elif model == Boisson:
            q.filter().first.return_value = mock_boisson
        return q

    db.query.side_effect = query_side_effect

    commande_in = CommandeCreate(
        userId=mock_user.id,
        articles=[{"boissonId": str(boisson_id), "qte": 2}]
    )

    with patch("app.services.commande_service.get_commande") as mock_get_commande:
        create_commande(db, commande_in, restaurant_id)
        assert db.add.called
        added_commande = db.add.call_args_list[0][0][0]
        assert added_commande.restaurantId == restaurant_id
        assert added_commande.numeroCommande.startswith("CMD-")
        assert len(added_commande.numeroCommande) == 12  # "CMD-" + 8 hex chars


def test_create_commande_waiter_not_found():
    db = MagicMock()
    db.query().filter().first.return_value = None
    restaurant_id = uuid4()
    waiter_id = uuid4()

    commande_in = CommandeCreate(
        userId=waiter_id,
        articles=[{"boissonId": str(uuid4()), "qte": 1}]
    )

    with pytest.raises(HTTPException) as exc_info:
        create_commande(db, commande_in, restaurant_id)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "La serveuse sélectionnée n'existe pas"


def test_create_commande_waiter_not_in_restaurant():
    db = MagicMock()
    mock_user = MagicMock(spec=User)
    mock_user.id = uuid4()
    mock_user.restaurantId = uuid4()  # Different restaurant

    db.query().filter().first.return_value = mock_user
    db.query().filter().first.side_effect = [mock_user, None]  # No RestaurantUser match either

    restaurant_id = uuid4()

    commande_in = CommandeCreate(
        userId=mock_user.id,
        articles=[{"boissonId": str(uuid4()), "qte": 1}]
    )

    with pytest.raises(HTTPException) as exc_info:
        create_commande(db, commande_in, restaurant_id)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "La serveuse sélectionnée n'appartient pas à votre restaurant"


def test_create_commande_no_articles():
    db = MagicMock()
    mock_user = MagicMock(spec=User)
    mock_user.id = uuid4()
    restaurant_id = uuid4()
    mock_user.restaurantId = restaurant_id

    db.query().filter().first.return_value = mock_user

    commande_in = CommandeCreate(
        userId=mock_user.id,
        articles=[]
    )

    with pytest.raises(HTTPException) as exc_info:
        create_commande(db, commande_in, restaurant_id)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "La commande doit contenir au moins un article"


# --- TESTS DES ENDPOINTS FastApi ---

def test_endpoint_create_commande(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    waiter_id = uuid4()
    boisson_id = uuid4()
    manager_user = User(id=uuid4(), name="Manager", email="manager@test.com")

    waiter_user = User(id=waiter_id, name="Serveuse 1", email="waiter@test.com", restaurantId=restaurant_id)
    boisson = Boisson(id=boisson_id, nomBoisson="Coca", prixVente=500.0, restaurantId=restaurant_id)

    commande_id = uuid4()
    created_commande = Commande(
        id=commande_id,
        restaurantId=restaurant_id,
        numeroCommande="CMD-12345678",
        userId=waiter_id,
        total=1000.0,
        statut=CommandeStatut.PENDING,
        createdAt=datetime.now(),
        updatedAt=datetime.now(),
        user=waiter_user,
        articles=[
            CommandeArticle(
                id=uuid4(),
                boissonId=boisson_id,
                repasId=None,
                qte=2,
                prixUnitaire=500.0,
                sousTotal=1000.0,
                isActive=True
            )
        ]
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[require_manager_cashier] = lambda: manager_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    with patch("app.services.commande_service.create_commande") as mock_create:
        mock_create.return_value = created_commande

        payload = {
            "userId": str(waiter_id),
            "articles": [
                {"boissonId": str(boisson_id), "qte": 2}
            ]
        }

        response = client.post("/commandes/", json=payload)
        app.dependency_overrides.clear()

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == str(commande_id)
        assert data["numeroCommande"] == "CMD-12345678"
        assert data["total"] == 1000.0


def test_endpoint_list_waiters(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    manager_user = User(id=uuid4(), name="Manager", email="manager@test.com")
    waiter = User(id=uuid4(), name="Serveuse 1", email="waiter1@test.com", restaurantId=restaurant_id)

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[require_manager_cashier] = lambda: manager_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    with patch("app.services.commande_service.get_restaurant_waiters") as mock_get_waiters:
        mock_get_waiters.return_value = [waiter]

        response = client.get("/commandes/waiters")
        app.dependency_overrides.clear()

        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(waiter.id)
        assert data[0]["name"] == "Serveuse 1"


def test_endpoint_list_my_commandes(client):
    db_mock = MagicMock()
    waiter_user = User(id=uuid4(), name="Serveuse", email="waiter@test.com")
    restaurant_id = uuid4()

    commande = Commande(
        id=uuid4(),
        restaurantId=restaurant_id,
        numeroCommande="CMD-ABCDEF12",
        userId=waiter_user.id,
        total=1500.0,
        statut=CommandeStatut.PENDING,
        createdAt=datetime.now(),
        updatedAt=datetime.now(),
        user=waiter_user,
        articles=[]
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: waiter_user

    with patch("app.services.commande_service.get_my_commandes") as mock_my_cmd:
        mock_my_cmd.return_value = [commande]

        response = client.get("/commandes/my-commandes")
        app.dependency_overrides.clear()

        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) == 1
        assert data[0]["numeroCommande"] == "CMD-ABCDEF12"


def test_endpoint_get_commande_by_id(client):
    db_mock = MagicMock()
    current_user = User(id=uuid4(), name="User", email="user@test.com")
    commande_id = uuid4()
    restaurant_id = uuid4()

    commande = Commande(
        id=commande_id,
        restaurantId=restaurant_id,
        numeroCommande="CMD-98765432",
        userId=current_user.id,
        total=2000.0,
        statut=CommandeStatut.PENDING,
        createdAt=datetime.now(),
        updatedAt=datetime.now(),
        user=current_user,
        articles=[]
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: current_user

    with patch("app.services.commande_service.get_commande") as mock_get_cmd:
        mock_get_cmd.return_value = commande

        response = client.get(f"/commandes/{commande_id}")
        app.dependency_overrides.clear()

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == str(commande_id)
        assert data["numeroCommande"] == "CMD-98765432"


def test_endpoint_get_commande_not_found(client):
    db_mock = MagicMock()
    current_user = User(id=uuid4(), name="User", email="user@test.com")
    commande_id = uuid4()

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: current_user

    with patch("app.services.commande_service.get_commande") as mock_get_cmd:
        mock_get_cmd.return_value = None

        response = client.get(f"/commandes/{commande_id}")
        app.dependency_overrides.clear()

        assert response.status_code == 404
        assert response.json()["detail"] == "Commande non trouvée"


def test_endpoint_delete_commande(client):
    db_mock = MagicMock()
    current_user = User(id=uuid4(), name="User", email="user@test.com")
    commande_id = uuid4()

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: current_user

    with patch("app.services.commande_service.delete_commande") as mock_del_cmd:
        mock_del_cmd.return_value = True

        response = client.delete(f"/commandes/{commande_id}")
        app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json()["message"] == "Commande supprimée"
