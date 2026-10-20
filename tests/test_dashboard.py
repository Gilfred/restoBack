import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.main import app
from app.database import get_session
from app.dependencies import (
    get_current_user,
    require_manager_or_admin,
    get_user_restaurant_id,
)
from app.models.user import User
from app.models.role import Role
from app.models.commande import Commande
from app.enums import CommandeStatut
from app.schemas.dashboard import DashboardPeriodEnum
from app.services.dashboard_service import (
    get_period_date_ranges,
    calculate_metric_comparison,
    get_dashboard_overview,
    get_sales_evolution,
)


@pytest.fixture
def client():
    return TestClient(app)


# --- 1. TESTS DES DATES ET FORMULES BORNES & POURCENTAGES ---

def test_get_period_date_ranges_today():
    ref_now = datetime(2026, 3, 15, 14, 30, 0)
    c_start, c_end, p_start, p_end = get_period_date_ranges(DashboardPeriodEnum.TODAY, ref_now)

    assert c_start == datetime(2026, 3, 15, 0, 0, 0)
    assert c_end == ref_now
    assert p_start == datetime(2026, 3, 14, 0, 0, 0)
    assert p_end == datetime(2026, 3, 14, 14, 30, 0)


def test_get_period_date_ranges_7d():
    ref_now = datetime(2026, 3, 15, 12, 0, 0)
    c_start, c_end, p_start, p_end = get_period_date_ranges(DashboardPeriodEnum.SEVEN_DAYS, ref_now)

    assert c_start == datetime(2026, 3, 9, 0, 0, 0)
    assert c_end == ref_now
    assert p_start == datetime(2026, 3, 2, 0, 0, 0)
    assert p_end == datetime(2026, 3, 9, 0, 0, 0)


def test_get_period_date_ranges_30d():
    ref_now = datetime(2026, 3, 15, 10, 0, 0)
    c_start, c_end, p_start, p_end = get_period_date_ranges(DashboardPeriodEnum.THIRTY_DAYS, ref_now)

    assert c_start == datetime(2026, 2, 14, 0, 0, 0)
    assert c_end == ref_now
    assert p_start == datetime(2026, 1, 15, 0, 0, 0)
    assert p_end == datetime(2026, 2, 14, 0, 0, 0)


def test_get_period_date_ranges_current_month():
    ref_now = datetime(2026, 3, 15, 16, 0, 0)
    c_start, c_end, p_start, p_end = get_period_date_ranges(DashboardPeriodEnum.CURRENT_MONTH, ref_now)

    assert c_start == datetime(2026, 3, 1, 0, 0, 0)
    assert c_end == ref_now
    assert p_start == datetime(2026, 2, 1, 0, 0, 0)
    assert p_end == datetime(2026, 2, 15, 16, 0, 0)


def test_get_period_date_ranges_previous_month():
    ref_now = datetime(2026, 3, 15, 16, 0, 0)
    c_start, c_end, p_start, p_end = get_period_date_ranges(DashboardPeriodEnum.PREVIOUS_MONTH, ref_now)

    assert c_start == datetime(2026, 2, 1, 0, 0, 0)
    assert c_end == datetime(2026, 3, 1, 0, 0, 0)
    assert p_start == datetime(2026, 1, 1, 0, 0, 0)
    assert p_end == datetime(2026, 2, 1, 0, 0, 0)


def test_calculate_metric_comparison_percentage():
    # Cas 1 : Période précédente = 0 et actuelle > 0 -> percentage_change = None (null en JSON)
    res_zero_prev = calculate_metric_comparison(current_val=15000.0, previous_val=0.0)
    assert res_zero_prev.current == 15000.0
    assert res_zero_prev.previous == 0.0
    assert res_zero_prev.variation_absolute == 15000.0
    assert res_zero_prev.percentage_change is None

    # Cas 2 : Les deux sont nulles -> percentage_change = 0.0
    res_both_zero = calculate_metric_comparison(current_val=0.0, previous_val=0.0)
    assert res_both_zero.current == 0.0
    assert res_both_zero.previous == 0.0
    assert res_both_zero.variation_absolute == 0.0
    assert res_both_zero.percentage_change == 0.0

    # Cas 3 : Période précédente > 0 -> calcul du pourcentage classique
    res_normal = calculate_metric_comparison(current_val=150.0, previous_val=100.0)
    assert res_normal.current == 150.0
    assert res_normal.previous == 100.0
    assert res_normal.variation_absolute == 50.0
    assert res_normal.percentage_change == 50.0


# --- 2. TESTS DES ENDPOINTS HTTP DU DASHBOARD ---

def test_get_dashboard_overview_endpoint(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    manager_role = Role(name="MANAGER_CASHIER")
    manager_user = User(id=uuid4(), name="Manager", email="manager@test.com", roles=[manager_role])

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[require_manager_or_admin] = lambda: manager_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    mock_overview_res = {
        "period": "7d",
        "currency": "XOF",
        "revenue": {
            "current": 125000.0,
            "previous": 100000.0,
            "variation_absolute": 25000.0,
            "percentage_change": 25.0
        },
        "orders_count": {
            "current": 10.0,
            "previous": 8.0,
            "variation_absolute": 2.0,
            "percentage_change": 25.0
        },
        "total_orders_received": {
            "current": 12.0,
            "previous": 10.0,
            "variation_absolute": 2.0,
            "percentage_change": 20.0
        },
        "limitations_note": "Note de limitation"
    }

    with patch("app.services.dashboard_service.get_dashboard_overview") as mock_service:
        mock_service.return_value = mock_overview_res

        response = client.get("/dashboard/overview?period=7d")
        app.dependency_overrides.clear()

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["period"] == "7d"
        assert data["currency"] == "XOF"
        assert data["revenue"]["current"] == 125000.0
        assert data["revenue"]["percentage_change"] == 25.0


def test_get_sales_evolution_endpoint(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    manager_role = Role(name="MANAGER_CASHIER")
    manager_user = User(id=uuid4(), name="Manager", email="manager@test.com", roles=[manager_role])

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[require_manager_or_admin] = lambda: manager_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    mock_sales_res = {
        "period": "7d",
        "currency": "XOF",
        "data": [
            {"date": "2026-03-09", "revenue": 10000.0, "orders_count": 2, "total_orders_received": 2},
            {"date": "2026-03-10", "revenue": 0.0, "orders_count": 0, "total_orders_received": 0},
            {"date": "2026-03-11", "revenue": 15000.0, "orders_count": 3, "total_orders_received": 4},
        ]
    }

    with patch("app.services.dashboard_service.get_sales_evolution") as mock_service:
        mock_service.return_value = mock_sales_res

        response = client.get("/dashboard/sales?period=7d")
        app.dependency_overrides.clear()

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["period"] == "7d"
        assert len(data["data"]) == 3
        assert data["data"][0]["date"] == "2026-03-09"
        assert data["data"][0]["revenue"] == 10000.0
        assert data["data"][1]["revenue"] == 0.0  # Jour sans ventes


def test_dashboard_invalid_period_param(client):
    db_mock = MagicMock()
    manager_role = Role(name="MANAGER_CASHIER")
    manager_user = User(id=uuid4(), name="Manager", email="manager@test.com", roles=[manager_role])

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[require_manager_or_admin] = lambda: manager_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: uuid4()

    response = client.get("/dashboard/overview?period=invalid_period")
    app.dependency_overrides.clear()

    assert response.status_code == 422  # Unprocessable Entity pour paramètre enum invalide


def test_dashboard_waiter_role_denied(client):
    db_mock = MagicMock()
    db_mock.query.return_value.join.return_value.filter.return_value.first.return_value = None
    waiter_role = Role(name="WAITER")
    waiter_user = User(id=uuid4(), name="Waiter", email="waiter@test.com", roles=[waiter_role])

    # require_manager_or_admin va refuser l'accès aux serveurs
    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: waiter_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: uuid4()

    response = client.get("/dashboard/overview?period=7d")
    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert "Accès refusé" in response.json()["detail"]


# --- 3. TESTS DES SERVICES AVEC AGREGATIONS SIMULEES ---

def test_service_get_dashboard_overview_mock_queries():
    db_mock = MagicMock()
    restaurant_id = uuid4()
    ref_now = datetime(2026, 3, 15, 12, 0, 0)

    # Configurer les valeurs de retour des requetes scalar()
    # 1. curr_revenue (50000.0), 2. curr_orders (5), 3. curr_total_orders (7)
    # 4. prev_revenue (40000.0), 5. prev_orders (4), 6. prev_total_orders (5)
    db_mock.query.return_value.filter.return_value.scalar.side_effect = [
        50000.0, 5, 7,
        40000.0, 4, 5
    ]

    res = get_dashboard_overview(
        db=db_mock,
        restaurant_id=restaurant_id,
        period=DashboardPeriodEnum.SEVEN_DAYS,
        reference_now=ref_now
    )

    assert res.period == DashboardPeriodEnum.SEVEN_DAYS
    assert res.currency == "XOF"
    assert res.revenue.current == 50000.0
    assert res.revenue.previous == 40000.0
    assert res.revenue.variation_absolute == 10000.0
    assert res.revenue.percentage_change == 25.0

    assert res.orders_count.current == 5.0
    assert res.orders_count.previous == 4.0
    assert res.orders_count.variation_absolute == 1.0
    assert res.orders_count.percentage_change == 25.0

    assert res.total_orders_received.current == 7.0
    assert res.total_orders_received.previous == 5.0


def test_service_get_sales_evolution_completion():
    db_mock = MagicMock()
    restaurant_id = uuid4()
    ref_now = datetime(2026, 3, 3, 12, 0, 0) # Period 7d starts 2026-02-25

    # Simuler 1 seul jour avec des ventes dans daily_query.all()
    mock_row = MagicMock()
    mock_row.day_date = "2026-03-01"
    mock_row.daily_revenue = 12000.0
    mock_row.daily_paid_orders = 3
    mock_row.daily_total_orders = 4

    db_mock.query.return_value.filter.return_value.group_by.return_value.all.return_value = [mock_row]

    res = get_sales_evolution(
        db=db_mock,
        restaurant_id=restaurant_id,
        period=DashboardPeriodEnum.SEVEN_DAYS,
        reference_now=ref_now
    )

    assert res.period == DashboardPeriodEnum.SEVEN_DAYS
    # Doit contenir exactement 7 jours (2026-02-25 à 2026-03-03)
    assert len(res.data) == 7

    # Le jour 2026-03-01 doit avoir les données
    march1 = [dp for dp in res.data if dp.date == "2026-03-01"][0]
    assert march1.revenue == 12000.0
    assert march1.orders_count == 3
    assert march1.total_orders_received == 4

    # Les autres jours doivent être à 0
    feb25 = [dp for dp in res.data if dp.date == "2026-02-25"][0]
    assert feb25.revenue == 0.0
    assert feb25.orders_count == 0
    assert feb25.total_orders_received == 0
