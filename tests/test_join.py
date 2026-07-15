import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from uuid import uuid4

from app.services.restaurant_user_service import join_restaurant
from app.models.restaurant import Restaurant
from app.models.restaurant_user import RestaurantUser
from app.models.role import Role

def test_join_restaurant_success():
    db = MagicMock()
    user_id = uuid4()
    restaurant_id = uuid4()

    def mock_query(model):
        m = MagicMock()
        if model == Restaurant:
            def mock_filter(*args):
                f_mock = MagicMock()
                expr = str(args[0])
                if "ownerid" in expr.lower():
                    f_mock.first.return_value = None
                else:
                    f_mock.first.return_value = Restaurant(id=restaurant_id)
                return f_mock
            m.filter.side_effect = mock_filter
        elif model == Role:
            m.join.return_value.filter.return_value.first.return_value = None
        elif model == RestaurantUser:
            m.filter.return_value.first.return_value = None
        return m

    db.query.side_effect = mock_query

    result = join_restaurant(db, user_id, restaurant_id)
    assert result is not None
    assert result.userId == user_id
    assert result.restaurantId == restaurant_id
    db.add.assert_called_once()
    db.commit.assert_called_once()

def test_join_restaurant_as_owner_fails():
    db = MagicMock()
    user_id = uuid4()
    restaurant_id = uuid4()

    def mock_query(model):
        m = MagicMock()
        if model == Restaurant:
            # User owns a restaurant (is_owner is True)
            m.filter.return_value.first.return_value = Restaurant(id=uuid4(), ownerId=user_id)
        elif model == Role:
            m.join.return_value.filter.return_value.first.return_value = None
        elif model == RestaurantUser:
            m.filter.return_value.first.return_value = None
        return m

    db.query.side_effect = mock_query

    with pytest.raises(HTTPException) as exc_info:
        join_restaurant(db, user_id, restaurant_id)

    assert exc_info.value.status_code == 400
    assert "Un administrateur ou propriétaire ne peut pas envoyer de demande d'adhésion" in exc_info.value.detail

def test_join_restaurant_as_admin_fails():
    db = MagicMock()
    user_id = uuid4()
    restaurant_id = uuid4()

    def mock_query(model):
        m = MagicMock()
        if model == Restaurant:
            m.filter.return_value.first.return_value = None
        elif model == Role:
            # User has ADMIN role
            m.join.return_value.filter.return_value.first.return_value = Role(name="ADMIN")
        elif model == RestaurantUser:
            m.filter.return_value.first.return_value = None
        return m

    db.query.side_effect = mock_query

    with pytest.raises(HTTPException) as exc_info:
        join_restaurant(db, user_id, restaurant_id)

    assert exc_info.value.status_code == 400
    assert "Un administrateur ou propriétaire ne peut pas envoyer de demande d'adhésion" in exc_info.value.detail
