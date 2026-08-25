import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime
from unittest.mock import MagicMock
from app.main import app
from app.database import get_session
from app.dependencies import get_current_user, require_admin, get_user_restaurant_id
from app.models.user import User
from app.models.repas import Repas

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

def test_create_repas(client):
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
        "nomRepas": "Poulet Yassa",
        "prix": 3500.0
    }

    response = client.post("/repas/", json=payload)
    app.dependency_overrides.clear()

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["nomRepas"] == "Poulet Yassa"
    assert data["prix"] == 3500.0
    assert data["restaurantId"] == str(restaurant_id)

def test_list_repas(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com")

    repas_obj = Repas(
        id=uuid4(),
        nomRepas="Riz Gras",
        prix=2000.0,
        restaurantId=restaurant_id,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    db_mock.query.side_effect = lambda model: MockQuery(repas_obj)

    response = client.get("/repas/")
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 1
    assert data[0]["nomRepas"] == "Riz Gras"
    assert data[0]["restaurantId"] == str(restaurant_id)

def test_get_repas(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    repas_id = uuid4()
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com")

    repas_obj = Repas(
        id=repas_id,
        nomRepas="Attiéké Poisson",
        prix=2500.0,
        restaurantId=restaurant_id,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    db_mock.query.side_effect = lambda model: MockQuery(repas_obj)

    response = client.get(f"/repas/{repas_id}")
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == str(repas_id)
    assert data["nomRepas"] == "Attiéké Poisson"

def test_get_repas_not_found(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    repas_id = uuid4()
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com")

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    db_mock.query.side_effect = lambda model: MockQuery([])

    response = client.get(f"/repas/{repas_id}")
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Repas non trouvé"

def test_update_repas(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    repas_id = uuid4()
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com")

    repas_obj = Repas(
        id=repas_id,
        nomRepas="Foutou Banane",
        prix=3000.0,
        restaurantId=restaurant_id,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    db_mock.query.side_effect = lambda model: MockQuery(repas_obj)

    payload = {"prix": 3500.0}
    response = client.put(f"/repas/{repas_id}", json=payload)
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["prix"] == 3500.0

def test_delete_repas(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    repas_id = uuid4()
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com")

    repas_obj = Repas(
        id=repas_id,
        nomRepas="Placali",
        prix=2000.0,
        restaurantId=restaurant_id,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    db_mock.query.side_effect = lambda model: MockQuery(repas_obj)

    response = client.delete(f"/repas/{repas_id}")
    app.dependency_overrides.clear()

    assert response.status_code == 204
