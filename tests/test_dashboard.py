import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.main import app
from app.database import get_session
from app.dependencies import (
    get_current_user,
    require_admin,
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
    get_weekly_sales_evolution,
    get_top_selling_products,
    get_orders_distribution,
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
    admin_role = Role(name="ADMIN")
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com", roles=[admin_role])

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[require_admin] = lambda: admin_user
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
    admin_role = Role(name="ADMIN")
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com", roles=[admin_role])

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[require_admin] = lambda: admin_user
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
    admin_role = Role(name="ADMIN")
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com", roles=[admin_role])

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: uuid4()

    response = client.get("/dashboard/overview?period=invalid_period")
    app.dependency_overrides.clear()

    assert response.status_code == 422  # Unprocessable Entity pour paramètre enum invalide


def test_dashboard_waiter_role_denied(client):
    db_mock = MagicMock()
    db_mock.query.return_value.filter.return_value.first.return_value = None
    db_mock.query.return_value.join.return_value.filter.return_value.first.return_value = None
    waiter_role = Role(name="WAITER")
    waiter_user = User(id=uuid4(), name="Waiter", email="waiter@test.com", roles=[waiter_role])

    # require_admin va refuser l'accès aux serveurs
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


# --- 4. TESTS DES NOUVEAUX GRAPHIQUES DU DASHBOARD ---

def test_service_get_weekly_sales_evolution_7_days():
    db_mock = MagicMock()
    restaurant_id = uuid4()
    # Mercredi 18 Mars 2026
    ref_now = datetime(2026, 3, 18, 15, 0, 0)

    # Simuler des ventes le Lundi 2026-03-16 et Mardi 2026-03-17
    mock_row1 = MagicMock()
    mock_row1.day_date = "2026-03-16"
    mock_row1.daily_revenue = 125000.0
    mock_row1.daily_paid_orders = 12
    mock_row1.daily_total_orders = 15

    mock_row2 = MagicMock()
    mock_row2.day_date = "2026-03-17"
    mock_row2.daily_revenue = 180000.0
    mock_row2.daily_paid_orders = 17
    mock_row2.daily_total_orders = 18

    db_mock.query.return_value.filter.return_value.group_by.return_value.all.return_value = [mock_row1, mock_row2]

    res = get_weekly_sales_evolution(
        db=db_mock,
        restaurant_id=restaurant_id,
        reference_now=ref_now
    )

    assert res.period == "weekly"
    assert res.currency == "XOF"
    assert res.start_date == "2026-03-16"  # Lundi
    assert res.end_date == "2026-03-22"    # Dimanche
    assert len(res.data) == 7

    # Vérifier l'ordre des jours et les libellés
    expected_days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    for idx, item in enumerate(res.data):
        assert item.day == expected_days[idx]

    # Lundi
    lundi = res.data[0]
    assert lundi.date == "2026-03-16"
    assert lundi.revenue == 125000.0
    assert lundi.orders_count == 12

    # Mardi
    mardi = res.data[1]
    assert mardi.date == "2026-03-17"
    assert mardi.revenue == 180000.0
    assert mardi.orders_count == 17

    # Dimanche (sans vente)
    dimanche = res.data[6]
    assert dimanche.date == "2026-03-22"
    assert dimanche.revenue == 0.0
    assert dimanche.orders_count == 0


def test_endpoint_get_weekly_sales_evolution(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    admin_role = Role(name="ADMIN")
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com", roles=[admin_role])

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    mock_weekly_res = {
        "period": "weekly",
        "currency": "XOF",
        "start_date": "2026-03-16",
        "end_date": "2026-03-22",
        "data": [
            {"date": "2026-03-16", "day": "Lundi", "revenue": 125000.0, "orders_count": 12, "total_orders_received": 15},
            {"date": "2026-03-17", "day": "Mardi", "revenue": 180000.0, "orders_count": 17, "total_orders_received": 18},
            {"date": "2026-03-18", "day": "Mercredi", "revenue": 0.0, "orders_count": 0, "total_orders_received": 0},
            {"date": "2026-03-19", "day": "Jeudi", "revenue": 0.0, "orders_count": 0, "total_orders_received": 0},
            {"date": "2026-03-20", "day": "Vendredi", "revenue": 0.0, "orders_count": 0, "total_orders_received": 0},
            {"date": "2026-03-21", "day": "Samedi", "revenue": 0.0, "orders_count": 0, "total_orders_received": 0},
            {"date": "2026-03-22", "day": "Dimanche", "revenue": 0.0, "orders_count": 0, "total_orders_received": 0},
        ]
    }

    with patch("app.services.dashboard_service.get_weekly_sales_evolution") as mock_service:
        mock_service.return_value = mock_weekly_res

        response = client.get("/dashboard/sales/weekly")
        app.dependency_overrides.clear()

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["period"] == "weekly"
        assert len(data["data"]) == 7
        assert data["data"][0]["day"] == "Lundi"


def test_service_get_top_selling_products():
    db_mock = MagicMock()
    restaurant_id = uuid4()
    ref_now = datetime(2026, 3, 18, 15, 0, 0)

    # 1. Quantité totale d'articles vendus = 100
    db_mock.query.return_value.select_from.return_value.join.return_value.filter.return_value.scalar.return_value = 100

    # 2. Produits retournés par l'agrégation
    repas_id = uuid4()
    boisson_id = uuid4()

    row_repas = MagicMock()
    row_repas.repasId = repas_id
    row_repas.boissonId = None
    row_repas.nomRepas = "Poulet Yassa"
    row_repas.nomBoisson = None
    row_repas.total_qte = 60
    row_repas.total_revenue = 180000.0

    row_boisson = MagicMock()
    row_boisson.repasId = None
    row_boisson.boissonId = boisson_id
    row_boisson.nomRepas = None
    row_boisson.nomBoisson = "Coca-Cola 55cl"
    row_boisson.total_qte = 40
    row_boisson.total_revenue = 20000.0

    db_mock.query.return_value.select_from.return_value.join.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [row_repas, row_boisson]

    res = get_top_selling_products(
        db=db_mock,
        restaurant_id=restaurant_id,
        period=DashboardPeriodEnum.SEVEN_DAYS,
        limit=10,
        reference_now=ref_now
    )

    assert res.period == DashboardPeriodEnum.SEVEN_DAYS
    assert res.total_quantity == 100
    assert len(res.data) == 2

    top1 = res.data[0]
    assert top1.product_id == str(repas_id)
    assert top1.name == "Poulet Yassa"
    assert top1.type == "repas"
    assert top1.quantity == 60
    assert top1.revenue == 180000.0
    assert top1.percentage == 60.0

    top2 = res.data[1]
    assert top2.product_id == str(boisson_id)
    assert top2.name == "Coca-Cola 55cl"
    assert top2.type == "boisson"
    assert top2.quantity == 40
    assert top2.revenue == 20000.0
    assert top2.percentage == 40.0


def test_endpoint_get_top_selling_products(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    admin_role = Role(name="ADMIN")
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com", roles=[admin_role])

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    mock_top_res = {
        "period": "7d",
        "currency": "XOF",
        "total_quantity": 100,
        "data": [
            {
                "product_id": str(uuid4()),
                "name": "Atcheke Poisson",
                "type": "repas",
                "quantity": 70,
                "revenue": 210000.0,
                "percentage": 70.0
            }
        ]
    }

    with patch("app.services.dashboard_service.get_top_selling_products") as mock_service:
        mock_service.return_value = mock_top_res

        response = client.get("/dashboard/products/top-selling?period=7d&limit=5")
        app.dependency_overrides.clear()

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["period"] == "7d"
        assert data["total_quantity"] == 100
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "Atcheke Poisson"


def test_service_get_orders_distribution_status():
    db_mock = MagicMock()
    restaurant_id = uuid4()
    ref_now = datetime(2026, 3, 18, 15, 0, 0)

    row_paid = MagicMock()
    row_paid.statut = CommandeStatut.PAID
    row_paid.statut_count = 80
    row_paid.statut_amount = 800000.0

    row_pending = MagicMock()
    row_pending.statut = CommandeStatut.PENDING
    row_pending.statut_count = 15
    row_pending.statut_amount = 150000.0

    row_cancelled = MagicMock()
    row_cancelled.statut = CommandeStatut.CANCELLED
    row_cancelled.statut_count = 5
    row_cancelled.statut_amount = 50000.0

    db_mock.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
        row_paid, row_pending, row_cancelled
    ]
    db_mock.query.return_value.filter.return_value.scalar.return_value = 800000.0

    res = get_orders_distribution(
        db=db_mock,
        restaurant_id=restaurant_id,
        period=DashboardPeriodEnum.SEVEN_DAYS,
        dist_type="status",
        reference_now=ref_now
    )

    assert res.period == DashboardPeriodEnum.SEVEN_DAYS
    assert res.type == "status"
    assert res.total_orders == 100
    assert res.total_revenue == 800000.0
    assert res.status_distribution is not None
    assert len(res.status_distribution) == 3

    paid_item = [x for x in res.status_distribution if x.statut == "paid"][0]
    assert paid_item.count == 80
    assert paid_item.percentage == 80.0
    assert paid_item.total_amount == 800000.0

    pending_item = [x for x in res.status_distribution if x.statut == "pending"][0]
    assert pending_item.count == 15
    assert pending_item.percentage == 15.0

    cancelled_item = [x for x in res.status_distribution if x.statut == "cancelled"][0]
    assert cancelled_item.count == 5
    assert cancelled_item.percentage == 5.0


def test_endpoint_get_orders_distribution(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    admin_role = Role(name="ADMIN")
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com", roles=[admin_role])

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    mock_dist_res = {
        "period": "7d",
        "currency": "XOF",
        "type": "status",
        "total_orders": 10,
        "total_revenue": 100000.0,
        "status_distribution": [
            {"statut": "paid", "label": "Payées", "count": 8, "percentage": 80.0, "total_amount": 80000.0},
            {"statut": "pending", "label": "En attente", "count": 2, "percentage": 20.0, "total_amount": 20000.0},
            {"statut": "cancelled", "label": "Annulées", "count": 0, "percentage": 0.0, "total_amount": 0.0},
        ],
        "category_distribution": None
    }

    with patch("app.services.dashboard_service.get_orders_distribution") as mock_service:
        mock_service.return_value = mock_dist_res

        response = client.get("/dashboard/orders/distribution?period=7d&type=status")
        app.dependency_overrides.clear()

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["period"] == "7d"
        assert data["type"] == "status"
        assert len(data["status_distribution"]) == 3
