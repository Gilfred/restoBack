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
from app.models.menu_boisson import MenuBoisson
from app.models.menu_boisson_famille import MenuBoissonFamille
from app.models.menu_boisson_image import MenuBoissonImage
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

    def join(self, *args, **kwargs):
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

def test_list_boissons_unauthenticated_public(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()

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
    db_mock.query.side_effect = lambda model: MockQuery(boisson_obj)

    # Public call without authentication headers/cookies
    response = client.get("/boissons/")
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 1
    assert data[0]["nomBoisson"] == "Fanta"
    assert data[0]["restaurantId"] == str(restaurant_id)

def test_get_boisson_unauthenticated_public(client):
    db_mock = MagicMock()
    boisson_id = uuid4()
    restaurant_id = uuid4()

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
    db_mock.query.side_effect = lambda model: MockQuery(boisson_obj)

    # Public call without authentication
    response = client.get(f"/boissons/{boisson_id}")
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == str(boisson_id)
    assert data["nomBoisson"] == "Sprite"

def test_list_my_restaurant_boissons_authenticated(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    famille_id = uuid4()
    boisson_id = uuid4()

    user = User(id=uuid4(), name="User Resto A", email="user@test.com")

    boisson_obj = Boisson(
        id=boisson_id,
        nomBoisson="Heineken",
        prixVente=1500.0,
        contenance=BoissonContenance.CL33,
        stock=30,
        restaurantId=restaurant_id,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    famille_obj = MenuBoissonFamille(
        id=famille_id,
        restaurantId=restaurant_id,
        nom="Bières",
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    image_obj = MenuBoissonImage(
        id=uuid4(),
        menuBoissonFamilleId=famille_id,
        url="https://res.cloudinary.com/test/bieres.png",
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )
    famille_obj.images = [image_obj]

    menu_boisson_obj = MenuBoisson(
        id=uuid4(),
        menuBoissonFamilleId=famille_id,
        boissonId=boisson_id,
        menuBoissonFamille=famille_obj,
        boisson=boisson_obj,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    queries = [
        MockQuery([boisson_obj]),
        MockQuery([menu_boisson_obj])
    ]
    db_mock.query.side_effect = lambda model: queries.pop(0)

    response = client.get("/boissons/me")
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert item["boisson"]["nomBoisson"] == "Heineken"
    assert item["boisson"]["prixVente"] == 1500.0
    assert item["boisson"]["contenance"] == "0,33cl"
    assert item["boisson"]["stock"] == 30
    assert item["famille"]["nom"] == "Bières"
    assert len(item["images"]) == 1
    assert item["images"][0]["url"] == "https://res.cloudinary.com/test/bieres.png"

def test_list_my_restaurant_boissons_unauthenticated_fails(client):
    db_mock = MagicMock()
    app.dependency_overrides[get_session] = lambda: db_mock

    # Without get_user_restaurant_id override, unauthenticated call returns 401
    response = client.get("/boissons/me")
    app.dependency_overrides.clear()

    assert response.status_code == 401

def test_multi_tenant_isolation_boissons_authenticated(client):
    db_mock = MagicMock()
    restaurant_a_id = uuid4()
    restaurant_b_id = uuid4()

    user_a = User(id=uuid4(), name="User Resto A", email="usera@test.com")

    boisson_a = Boisson(
        id=uuid4(),
        nomBoisson="Boisson Resto A",
        prixVente=1000.0,
        contenance=BoissonContenance.CL33,
        stock=10,
        restaurantId=restaurant_a_id,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: user_a
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_a_id

    # The service query will filter strictly by Boisson.restaurantId == restaurant_a_id
    queries = [
        MockQuery([boisson_a]),
        MockQuery([])
    ]
    db_mock.query.side_effect = lambda model: queries.pop(0)

    # Client passes extra query parameters attempting BOLA
    response = client.get(f"/boissons/me?restaurant_id={restaurant_b_id}&restaurantId={restaurant_b_id}")
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 1
    assert data[0]["boisson"]["restaurantId"] == str(restaurant_a_id)
    assert data[0]["boisson"]["nomBoisson"] == "Boisson Resto A"

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
