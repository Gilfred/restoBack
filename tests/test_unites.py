import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from unittest.mock import MagicMock
from datetime import datetime
from app.main import app
from app.database import get_session
from app.dependencies import get_current_user, require_superadmin, get_user_restaurant_id
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.restaurant import Restaurant
from app.models.unite import Unite
from app.enums import UniteType

@pytest.fixture
def client():
    return TestClient(app)

class MockQuery:
    def __init__(self, value=None):
        self.value = value

    def join(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def options(self, *args, **kwargs):
        return self

    def first(self):
        return self.value

    def all(self):
        return [self.value] if self.value is not None else []

def test_create_unite_as_superadmin(client):
    db_mock = MagicMock()

    superadmin_user = User(id=uuid4(), name="Super Admin", email="super@test.com")
    superadmin_role = Role(name="SUPERADMIN")
    superadmin_user.roles = [superadmin_role]

    restaurant_id = uuid4()

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: superadmin_user

    # Mock DB query
    def mock_query(model):
        if model == Restaurant:
            return MockQuery(Restaurant(id=restaurant_id))
        return MockQuery(None)
    db_mock.query.side_effect = mock_query

    # Mock DB commit and refresh
    def mock_add(obj):
        obj.id = uuid4()
        obj.createdAt = datetime.now()
        obj.updatedAt = datetime.now()
        obj.isActive = True

    db_mock.add.side_effect = mock_add

    payload = {
        "unite": "kg",
        "restaurantId": str(restaurant_id)
    }

    response = client.post("/unites/", json=payload)
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["unite"] == "kg"
    assert data["restaurantId"] == str(restaurant_id)


def test_create_unite_as_restaurant_manager(client, monkeypatch):
    db_mock = MagicMock()

    manager_user = User(id=uuid4(), name="Manager", email="manager@test.com")
    manager_role = Role(name="MANAGER")
    manager_role.permissions = [Permission(name="manage_staff")]
    manager_user.roles = [manager_role]

    restaurant_id = uuid4()

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: manager_user

    # Mock DB query
    def mock_query(model):
        if model == Permission:
            # We want to return a permission for manage_staff
            return MockQuery(Permission(name="manage_staff"))
        return MockQuery(None)
    db_mock.query.side_effect = mock_query

    # Mock get_user_restaurant_id called inside route or dependencies
    monkeypatch.setattr("app.dependencies.get_user_restaurant_id", lambda user, db: restaurant_id)

    # Mock DB commit and refresh
    def mock_add(obj):
        obj.id = uuid4()
        obj.createdAt = datetime.now()
        obj.updatedAt = datetime.now()
        obj.isActive = True

    db_mock.add.side_effect = mock_add

    # Try to pass a different restaurantId (BOLA attempt)
    another_restaurant_id = uuid4()
    payload = {
        "unite": "kg",
        "restaurantId": str(another_restaurant_id)
    }

    response = client.post("/unites/", json=payload)
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["unite"] == "kg"
    # It must ignore the BOLA attempt and force-use their own restaurant_id!
    assert data["restaurantId"] == str(restaurant_id)


def test_create_unite_unauthorized_user(client):
    db_mock = MagicMock()

    waiter_user = User(id=uuid4(), name="Waiter", email="waiter@test.com")
    waiter_role = Role(name="WAITER")
    waiter_role.permissions = [] # No permissions
    waiter_user.roles = [waiter_role]

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: waiter_user

    # Mock DB query
    db_mock.query.side_effect = lambda model: MockQuery(None)

    payload = {
        "unite": "kg"
    }

    response = client.post("/unites/", json=payload)
    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert "Vous n'avez pas la permission de créer des unités" in response.text


def test_create_unite_non_existent_restaurant(client):
    db_mock = MagicMock()
    superadmin_user = User(id=uuid4(), name="Super Admin", email="super@test.com")
    superadmin_user.roles = [Role(name="SUPERADMIN")]

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: superadmin_user

    # Restaurant does not exist
    db_mock.query.side_effect = lambda model: MockQuery(None)

    payload = {
        "unite": "kg",
        "restaurantId": str(uuid4())
    }

    response = client.post("/unites/", json=payload)
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert "Le restaurant spécifié n'existe pas" in response.text


def test_read_unites_as_superadmin_no_restaurant_id(client):
    db_mock = MagicMock()
    superadmin_user = User(id=uuid4(), name="Super Admin", email="super@test.com")
    superadmin_user.roles = [Role(name="SUPERADMIN")]

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: superadmin_user

    restaurant_id = uuid4()
    mock_unite = Unite(
        id=uuid4(),
        unite=UniteType.KG,
        restaurantId=restaurant_id,
        isActive=True,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    # Mock return list of units
    db_mock.query.side_effect = lambda model: MockQuery(mock_unite)

    response = client.get("/unites/")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["unite"] == "kg"
    assert data[0]["restaurantId"] == str(restaurant_id)


def test_read_unites_as_normal_user(client, monkeypatch):
    db_mock = MagicMock()
    normal_user = User(id=uuid4(), name="Normal User", email="user@test.com")
    normal_user.roles = [Role(name="WAITER")]

    restaurant_id = uuid4()
    mock_unite = Unite(
        id=uuid4(),
        unite=UniteType.LITRES,
        restaurantId=restaurant_id,
        isActive=True,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: normal_user

    # Mock get_user_restaurant_id inside dependencies
    monkeypatch.setattr("app.dependencies.get_user_restaurant_id", lambda user, db: restaurant_id)

    db_mock.query.side_effect = lambda model: MockQuery(mock_unite)

    response = client.get("/unites/")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["unite"] == "litres"
    assert data[0]["restaurantId"] == str(restaurant_id)
