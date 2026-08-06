import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from unittest.mock import MagicMock
from datetime import datetime
from app.main import app
from app.database import get_session
from app.models.restaurant import Restaurant

@pytest.fixture
def client():
    return TestClient(app)

class MockQuery:
    def __init__(self, value=None):
        self._value = value

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self._value if isinstance(self._value, list) else [self._value] if self._value is not None else []

def test_list_restaurants_unauthenticated(client):
    db_mock = MagicMock()
    app.dependency_overrides[get_session] = lambda: db_mock

    restaurant_id = uuid4()
    owner_id = uuid4()
    mock_restaurant = Restaurant(
        id=restaurant_id,
        name="Test Restaurant",
        address="123 Street",
        phone="123456789",
        ownerId=owner_id,
        isActive=True,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    # Mock DB query
    db_mock.query.side_effect = lambda model: MockQuery([mock_restaurant])

    # No authorization headers, meaning the request is completely unauthenticated
    response = client.get("/restaurants/")
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Restaurant"
    assert data[0]["address"] == "123 Street"
    assert data[0]["phone"] == "123456789"
    assert data[0]["id"] == str(restaurant_id)
    assert data[0]["ownerId"] == str(owner_id)
    assert data[0]["isActive"] is True
