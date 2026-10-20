from datetime import datetime, timedelta, date
from typing import Optional, Tuple, List, Dict
from uuid import UUID
import calendar
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.models.commande import Commande
from app.enums import CommandeStatut
from app.schemas.dashboard import (
    DashboardPeriodEnum,
    MetricComparison,
    DashboardOverviewResponse,
    SalesDataPoint,
    SalesEvolutionResponse,
)


def get_period_date_ranges(
    period: DashboardPeriodEnum,
    reference_now: Optional[datetime] = None
) -> Tuple[datetime, datetime, datetime, datetime]:
    """
    Retourne (current_start, current_end, previous_start, previous_end)
    avec une sémantique d'intervalle [start, end).
    """
    now = reference_now or datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == DashboardPeriodEnum.TODAY:
        current_start = today_start
        current_end = now
        previous_start = current_start - timedelta(days=1)
        previous_end = previous_start + (current_end - current_start)

    elif period == DashboardPeriodEnum.SEVEN_DAYS:
        current_start = today_start - timedelta(days=6)
        current_end = now
        previous_start = current_start - timedelta(days=7)
        previous_end = current_start

    elif period == DashboardPeriodEnum.THIRTY_DAYS:
        current_start = today_start - timedelta(days=29)
        current_end = now
        previous_start = current_start - timedelta(days=30)
        previous_end = current_start

    elif period == DashboardPeriodEnum.CURRENT_MONTH:
        current_start = today_start.replace(day=1)
        current_end = now
        delta = current_end - current_start

        # Calcul du 1er jour du mois précédent
        first_of_this_month = current_start
        last_day_prev_month = first_of_this_month - timedelta(days=1)
        previous_start = last_day_prev_month.replace(day=1)
        previous_end = min(previous_start + delta, first_of_this_month)

    elif period == DashboardPeriodEnum.PREVIOUS_MONTH:
        first_of_this_month = today_start.replace(day=1)
        last_day_prev_month = first_of_this_month - timedelta(days=1)
        current_start = last_day_prev_month.replace(day=1)
        current_end = first_of_this_month

        last_day_month_before = current_start - timedelta(days=1)
        previous_start = last_day_month_before.replace(day=1)
        previous_end = current_start

    else:
        raise ValueError(f"Période non supportée: {period}")

    return current_start, current_end, previous_start, previous_end


def calculate_metric_comparison(current_val: float, previous_val: float) -> MetricComparison:
    curr = round(float(current_val or 0.0), 2)
    prev = round(float(previous_val or 0.0), 2)
    var_abs = round(curr - prev, 2)

    if prev == 0.0:
        if curr > 0.0:
            pct_change = None  # Conforme aux consignes (null si prev == 0 et curr > 0)
        else:
            pct_change = 0.0
    else:
        pct_change = round(((curr - prev) / prev) * 100.0, 2)

    return MetricComparison(
        current=curr,
        previous=prev,
        variation_absolute=var_abs,
        percentage_change=pct_change
    )


def get_dashboard_overview(
    db: Session,
    restaurant_id: UUID,
    period: DashboardPeriodEnum,
    reference_now: Optional[datetime] = None
) -> DashboardOverviewResponse:

    c_start, c_end, p_start, p_end = get_period_date_ranges(period, reference_now)

    # Requetes SQL d'agrégation pour la période actuelle
    curr_revenue = db.query(
        func.coalesce(func.sum(Commande.total), 0.0)
    ).filter(
        Commande.restaurantId == restaurant_id,
        Commande.isActive == True,
        Commande.statut == CommandeStatut.PAID,
        Commande.createdAt >= c_start,
        Commande.createdAt < c_end
    ).scalar() or 0.0

    curr_orders = db.query(
        func.count(Commande.id)
    ).filter(
        Commande.restaurantId == restaurant_id,
        Commande.isActive == True,
        Commande.statut == CommandeStatut.PAID,
        Commande.createdAt >= c_start,
        Commande.createdAt < c_end
    ).scalar() or 0

    curr_total_orders = db.query(
        func.count(Commande.id)
    ).filter(
        Commande.restaurantId == restaurant_id,
        Commande.isActive == True,
        Commande.createdAt >= c_start,
        Commande.createdAt < c_end
    ).scalar() or 0

    # Requetes SQL d'agrégation pour la période de comparaison
    prev_revenue = db.query(
        func.coalesce(func.sum(Commande.total), 0.0)
    ).filter(
        Commande.restaurantId == restaurant_id,
        Commande.isActive == True,
        Commande.statut == CommandeStatut.PAID,
        Commande.createdAt >= p_start,
        Commande.createdAt < p_end
    ).scalar() or 0.0

    prev_orders = db.query(
        func.count(Commande.id)
    ).filter(
        Commande.restaurantId == restaurant_id,
        Commande.isActive == True,
        Commande.statut == CommandeStatut.PAID,
        Commande.createdAt >= p_start,
        Commande.createdAt < p_end
    ).scalar() or 0

    prev_total_orders = db.query(
        func.count(Commande.id)
    ).filter(
        Commande.restaurantId == restaurant_id,
        Commande.isActive == True,
        Commande.createdAt >= p_start,
        Commande.createdAt < p_end
    ).scalar() or 0

    return DashboardOverviewResponse(
        period=period,
        currency="XOF",
        revenue=calculate_metric_comparison(curr_revenue, prev_revenue),
        orders_count=calculate_metric_comparison(float(curr_orders), float(prev_orders)),
        total_orders_received=calculate_metric_comparison(float(curr_total_orders), float(prev_total_orders))
    )


def get_sales_evolution(
    db: Session,
    restaurant_id: UUID,
    period: DashboardPeriodEnum,
    reference_now: Optional[datetime] = None
) -> SalesEvolutionResponse:

    c_start, c_end, _, _ = get_period_date_ranges(period, reference_now)

    # Requête avec agrégation quotidienne PostgreSQL / SQL
    # func.date(...) extrait la portion 'YYYY-MM-DD'
    daily_query = db.query(
        func.date(Commande.createdAt).label("day_date"),
        func.coalesce(
            func.sum(case((Commande.statut == CommandeStatut.PAID, Commande.total), else_=0.0)),
            0.0
        ).label("daily_revenue"),
        func.count(case((Commande.statut == CommandeStatut.PAID, Commande.id))).label("daily_paid_orders"),
        func.count(Commande.id).label("daily_total_orders")
    ).filter(
        Commande.restaurantId == restaurant_id,
        Commande.isActive == True,
        Commande.createdAt >= c_start,
        Commande.createdAt < c_end
    ).group_by(
        func.date(Commande.createdAt)
    ).all()

    # Organiser les résultats par date au format string "YYYY-MM-DD"
    stats_by_day: Dict[str, Dict] = {}
    for row in daily_query:
        # row.day_date peut être un objet date ou str selon l'adaptateur DB
        d_str = row.day_date.strftime("%Y-%m-%d") if isinstance(row.day_date, (date, datetime)) else str(row.day_date)
        stats_by_day[d_str] = {
            "revenue": round(float(row.daily_revenue or 0.0), 2),
            "orders_count": int(row.daily_paid_orders or 0),
            "total_orders_received": int(row.daily_total_orders or 0)
        }

    # Génération de la séquence continue de dates
    start_date = c_start.date()
    end_date = c_end.date()

    # Si c_end tombe pile à minuit (ex: PREVIOUS_MONTH), le dernier jour inclus est end_date - 1 day
    if c_end.hour == 0 and c_end.minute == 0 and c_end.second == 0 and c_end > c_start:
        last_date = end_date - timedelta(days=1)
    else:
        last_date = end_date

    data_points: List[SalesDataPoint] = []
    curr_date = start_date

    while curr_date <= last_date:
        d_str = curr_date.strftime("%Y-%m-%d")
        if d_str in stats_by_day:
            day_data = stats_by_day[d_str]
            data_points.append(SalesDataPoint(
                date=d_str,
                revenue=day_data["revenue"],
                orders_count=day_data["orders_count"],
                total_orders_received=day_data["total_orders_received"]
            ))
        else:
            data_points.append(SalesDataPoint(
                date=d_str,
                revenue=0.0,
                orders_count=0,
                total_orders_received=0
            ))
        curr_date += timedelta(days=1)

    return SalesEvolutionResponse(
        period=period,
        currency="XOF",
        data=data_points
    )
