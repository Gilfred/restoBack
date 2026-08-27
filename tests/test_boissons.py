import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime
from unittest.mock import MagicMock
from app.main import app
from app.database import get_session
from app.dependencies import get_current_user, require_admin, require_manager_cashier, get_user_restaurant_id
from app.models.user import User
from app.models.boisson import Boisson
from app.enums import BoissonContenance

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

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.items[0] if self.items else None

    def all(self):
        return self.items

def test_create_boisson(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com")

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    def mock_add(obj):
        obj.id = uuid4()
        obj.createdAt = datetime.now()
        obj.updatedAt = datetime.now()

    db_mock.add.side_effect = mock_add

    payload = {
        "nomBoisson": "Coca Cola",
        "prixVente": 500.0,
        "contenance": "0,33cl"
    }

    response = client.post("/boissons/", json=payload)
    app.dependency_overrides.clear()

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["nomBoisson"] == "Coca Cola"
    assert data["prixVente"] == 500.0
    assert data["restaurantId"] == str(restaurant_id)

def test_list_boissons(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    gerant_user = User(id=uuid4(), name="Gérant", email="gerant@test.com")

    boisson_obj = Boisson(
        id=uuid4(),
        nomBoisson="Fanta",
        prixVente=500.0,
        contenance=BoissonContenance.CL33,
        stock=20,
        restaurantId=restaurant_id,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: gerant_user
    app.dependency_overrides[require_manager_cashier] = lambda: gerant_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    db_mock.query.side_effect = lambda model: MockQuery(boisson_obj)

    response = client.get("/boissons/")
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 1
    assert data[0]["nomBoisson"] == "Fanta"
    assert data[0]["restaurantId"] == str(restaurant_id)

def test_get_boisson(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    boisson_id = uuid4()
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com")

    boisson_obj = Boisson(
        id=boisson_id,
        nomBoisson="Sprite",
        prixVente=500.0,
        contenance=BoissonContenance.CL33,
        stock=15,
        restaurantId=restaurant_id,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    db_mock.query.side_effect = lambda model: MockQuery(boisson_obj)

    response = client.get(f"/boissons/{boisson_id}")
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == str(boisson_id)
    assert data["nomBoisson"] == "Sprite"

def test_update_boisson(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    boisson_id = uuid4()
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com")

    boisson_obj = Boisson(
        id=boisson_id,
        nomBoisson="Juver",
        prixVente=1000.0,
        contenance=BoissonContenance.CL55,
        stock=10,
        restaurantId=restaurant_id,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    db_mock.query.side_effect = lambda model: MockQuery(boisson_obj)

    payload = {"prixVente": 1200.0}
    response = client.patch(f"/boissons/{boisson_id}", json=payload)
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["prixVente"] == 1200.0

def test_delete_boisson(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    boisson_id = uuid4()
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com")

    boisson_obj = Boisson(
        id=boisson_id,
        nomBoisson="Water",
        prixVente=300.0,
        contenance=BoissonContenance.CL55,
        stock=100,
        restaurantId=restaurant_id,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    db_mock.query.side_effect = lambda model: MockQuery(boisson_obj)

    response = client.delete(f"/boissons/{boisson_id}")
    app.dependency_overrides.clear()

    assert response.status_code == 204
