import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime
from unittest.mock import MagicMock
from app.main import app
from app.database import get_session
from app.dependencies import get_current_user, require_manager_cashier, get_user_restaurant_id
from app.models.user import User
from app.models.role import Role
from app.models.commande import Commande
from app.enums import CommandeStatut

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

    def join(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def options(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self.items[0] if self.items else None

    def all(self):
        return self.items

def test_create_commande_as_waiter_forbidden(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    waiter_user = User(id=uuid4(), name="Waiter User", email="waiter@test.com", restaurantId=restaurant_id)
    waiter_role = Role(name="WAITER")
    waiter_user.roles = [waiter_role]

    db_mock.query.side_effect = lambda model: MockQuery(None)

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: waiter_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    payload = {
        "userId": str(uuid4()),
        "articles": [
            {"boissonId": str(uuid4()), "qte": 2, "prixUnitaire": 5.0}
        ]
    }

    response = client.post("/commandes/", json=payload)
    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert "seul un gérant ou administrateur" in response.text

def test_list_waiters_as_manager(client, monkeypatch):
    db_mock = MagicMock()
    restaurant_id = uuid4()

    manager_user = User(id=uuid4(), name="Manager User", email="manager@test.com", restaurantId=restaurant_id)
    manager_role = Role(name="MANAGER_CASHIER")
    manager_user.roles = [manager_role]

    waiter = User(id=uuid4(), name="Serveuse 1", email="serveuse1@test.com", restaurantId=restaurant_id)

    db_mock.query.side_effect = lambda model: MockQuery(None)

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: manager_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id
    monkeypatch.setattr("app.services.commande_service.get_restaurant_waiters", lambda db, rest_id: [waiter])

    response = client.get("/commandes/waiters")
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Serveuse 1"
    assert data[0]["id"] == str(waiter.id)

def test_create_commande_as_manager_success(client, monkeypatch):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    waiter_id = uuid4()

    manager_user = User(id=uuid4(), name="Manager User", email="manager@test.com", restaurantId=restaurant_id)
    manager_user.roles = [Role(name="MANAGER_CASHIER")]

    waiter_user = User(id=waiter_id, name="Serveuse", email="serveuse@test.com", restaurantId=restaurant_id)

    db_mock.query.side_effect = lambda model: MockQuery(None)

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: manager_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    cmd_id = uuid4()
    mock_commande = Commande(
        id=cmd_id,
        restaurantId=restaurant_id,
        numeroCommande="CMD-12345678",
        userId=waiter_id,
        total=15.0,
        statut=CommandeStatut.PENDING,
        createdAt=datetime.now(),
        updatedAt=datetime.now(),
        isActive=True,
        articles=[],
        user=waiter_user
    )

    monkeypatch.setattr("app.services.commande_service.create_commande", lambda db, data, r_id: mock_commande)

    payload = {
        "userId": str(waiter_id),
        "articles": [
            {"boissonId": str(uuid4()), "qte": 3, "prixUnitaire": 5.0}
        ]
    }

    response = client.post("/commandes/", json=payload)
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == str(cmd_id)
    assert data["userId"] == str(waiter_id)
    assert data["total"] == 15.0

def test_list_my_commandes_as_waiter(client, monkeypatch):
    db_mock = MagicMock()
    waiter_id = uuid4()
    restaurant_id = uuid4()

    waiter_user = User(id=waiter_id, name="Serveuse", email="serveuse@test.com", restaurantId=restaurant_id)
    waiter_user.roles = [Role(name="WAITER")]

    db_mock.query.side_effect = lambda model: MockQuery(None)

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: waiter_user

    mock_commande = Commande(
        id=uuid4(),
        restaurantId=restaurant_id,
        numeroCommande="CMD-9999",
        userId=waiter_id,
        total=20.0,
        statut=CommandeStatut.PENDING,
        createdAt=datetime.now(),
        updatedAt=datetime.now(),
        isActive=True,
        articles=[],
        user=waiter_user
    )

    monkeypatch.setattr("app.services.commande_service.get_my_commandes", lambda db, uid: [mock_commande])

    response = client.get("/commandes/my-commandes")
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 1
    assert data[0]["userId"] == str(waiter_id)
    assert data[0]["numeroCommande"] == "CMD-9999"
