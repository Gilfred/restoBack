from datetime import datetime, timedelta, date
from typing import Optional, Tuple, List, Dict
from uuid import UUID
import calendar
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.models.commande import Commande
from app.models.commande_article import CommandeArticle
from app.models.repas import Repas
from app.models.boisson import Boisson
from app.enums import CommandeStatut
from app.schemas.dashboard import (
    DashboardPeriodEnum,
    MetricComparison,
    DashboardOverviewResponse,
    SalesDataPoint,
    SalesEvolutionResponse,
    WeeklySalesDataPoint,
    WeeklySalesEvolutionResponse,
    TopSellingProductItem,
    TopSellingProductsResponse,
    OrderStatusDistributionItem,
    OrderCategoryDistributionItem,
    OrdersDistributionResponse,
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


FRENCH_DAY_NAMES = {
    0: "Lundi",
    1: "Mardi",
    2: "Mercredi",
    3: "Jeudi",
    4: "Vendredi",
    5: "Samedi",
    6: "Dimanche",
}


def get_weekly_sales_evolution(
    db: Session,
    restaurant_id: UUID,
    reference_now: Optional[datetime] = None
) -> WeeklySalesEvolutionResponse:
    """
    Retourne l'évolution hebdomadaire des ventes sur 7 jours (du Lundi au Dimanche).
    Agrége le CA et le nombre de commandes pour le restaurant donné.
    """
    now = reference_now or datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Déterminer le Lundi 00:00:00 de la semaine courante
    monday_start = today_start - timedelta(days=today_start.weekday())
    sunday_end = monday_start + timedelta(days=7)

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
        Commande.createdAt >= monday_start,
        Commande.createdAt < sunday_end
    ).group_by(
        func.date(Commande.createdAt)
    ).all()

    stats_by_day: Dict[str, Dict] = {}
    for row in daily_query:
        d_str = row.day_date.strftime("%Y-%m-%d") if isinstance(row.day_date, (date, datetime)) else str(row.day_date)
        stats_by_day[d_str] = {
            "revenue": round(float(row.daily_revenue or 0.0), 2),
            "orders_count": int(row.daily_paid_orders or 0),
            "total_orders_received": int(row.daily_total_orders or 0)
        }

    data_points: List[WeeklySalesDataPoint] = []
    for day_offset in range(7):
        current_dt = monday_start + timedelta(days=day_offset)
        d_str = current_dt.strftime("%Y-%m-%d")
        day_name = FRENCH_DAY_NAMES[current_dt.weekday()]

        if d_str in stats_by_day:
            day_data = stats_by_day[d_str]
            data_points.append(WeeklySalesDataPoint(
                date=d_str,
                day=day_name,
                revenue=day_data["revenue"],
                orders_count=day_data["orders_count"],
                total_orders_received=day_data["total_orders_received"]
            ))
        else:
            data_points.append(WeeklySalesDataPoint(
                date=d_str,
                day=day_name,
                revenue=0.0,
                orders_count=0,
                total_orders_received=0
            ))

    sunday_date = (monday_start + timedelta(days=6)).strftime("%Y-%m-%d")
    monday_date = monday_start.strftime("%Y-%m-%d")

    return WeeklySalesEvolutionResponse(
        period="weekly",
        currency="XOF",
        start_date=monday_date,
        end_date=sunday_date,
        data=data_points
    )


def get_top_selling_products(
    db: Session,
    restaurant_id: UUID,
    period: DashboardPeriodEnum,
    limit: int = 10,
    reference_now: Optional[datetime] = None
) -> TopSellingProductsResponse:
    """
    Retourne le classement des produits les plus vendus pendant une période donnée.
    Agrége les quantités et le chiffre d'affaires à partir des lignes CommandeArticle.
    Exclut les commandes inactives/annulées et les lignes inactives.
    """
    c_start, c_end, _, _ = get_period_date_ranges(period, reference_now)

    # 1. Calcul de la quantité totale d'articles vendus tous produits confondus
    total_quantity_all = db.query(
        func.coalesce(func.sum(CommandeArticle.qte), 0)
    ).select_from(CommandeArticle).join(
        Commande, CommandeArticle.commandeId == Commande.id
    ).filter(
        Commande.restaurantId == restaurant_id,
        Commande.isActive == True,
        Commande.statut == CommandeStatut.PAID,
        CommandeArticle.isActive == True,
        Commande.createdAt >= c_start,
        Commande.createdAt < c_end
    ).scalar() or 0

    # 2. Agrégation par produit
    query = db.query(
        CommandeArticle.repasId,
        CommandeArticle.boissonId,
        Repas.nomRepas,
        Boisson.nomBoisson,
        func.sum(CommandeArticle.qte).label("total_qte"),
        func.sum(CommandeArticle.sousTotal).label("total_revenue")
    ).select_from(CommandeArticle).join(
        Commande, CommandeArticle.commandeId == Commande.id
    ).outerjoin(
        Repas, CommandeArticle.repasId == Repas.id
    ).outerjoin(
        Boisson, CommandeArticle.boissonId == Boisson.id
    ).filter(
        Commande.restaurantId == restaurant_id,
        Commande.isActive == True,
        Commande.statut == CommandeStatut.PAID,
        CommandeArticle.isActive == True,
        Commande.createdAt >= c_start,
        Commande.createdAt < c_end
    ).group_by(
        CommandeArticle.repasId,
        CommandeArticle.boissonId,
        Repas.nomRepas,
        Boisson.nomBoisson
    ).order_by(
        func.sum(CommandeArticle.qte).desc(),
        func.sum(CommandeArticle.sousTotal).desc()
    ).limit(limit).all()

    items: List[TopSellingProductItem] = []
    for row in query:
        qte = int(row.total_qte or 0)
        rev = round(float(row.total_revenue or 0.0), 2)

        if row.repasId is not None:
            p_id = str(row.repasId)
            p_name = row.nomRepas or "Repas supprimé"
            p_type = "repas"
        elif row.boissonId is not None:
            p_id = str(row.boissonId)
            p_name = row.nomBoisson or "Boisson supprimée"
            p_type = "boisson"
        else:
            p_id = "unknown"
            p_name = "Produit inconnu"
            p_type = "autre"

        if total_quantity_all > 0:
            pct = round((qte / float(total_quantity_all)) * 100.0, 2)
        else:
            pct = 0.0

        items.append(TopSellingProductItem(
            product_id=p_id,
            name=p_name,
            type=p_type,
            quantity=qte,
            revenue=rev,
            percentage=pct
        ))

    return TopSellingProductsResponse(
        period=period,
        currency="XOF",
        total_quantity=int(total_quantity_all),
        data=items
    )


def get_orders_distribution(
    db: Session,
    restaurant_id: UUID,
    period: DashboardPeriodEnum,
    dist_type: str = "status",
    reference_now: Optional[datetime] = None
) -> OrdersDistributionResponse:
    """
    Retourne le spectre de répartition des commandes.
    dist_type='status' -> Répartition par statut (PAID, PENDING, CANCELLED)
    dist_type='category' -> Répartition par type/famille de menu (Repas vs Boissons)
    """
    c_start, c_end, _, _ = get_period_date_ranges(period, reference_now)

    if dist_type == "status":
        # Requête par statut
        rows = db.query(
            Commande.statut,
            func.count(Commande.id).label("statut_count"),
            func.coalesce(func.sum(Commande.total), 0.0).label("statut_amount")
        ).filter(
            Commande.restaurantId == restaurant_id,
            Commande.isActive == True,
            Commande.createdAt >= c_start,
            Commande.createdAt < c_end
        ).group_by(
            Commande.statut
        ).all()

        stats_map = {row.statut: row for row in rows}

        total_orders = sum(int(row.statut_count or 0) for row in rows)
        paid_revenue = db.query(
            func.coalesce(func.sum(Commande.total), 0.0)
        ).filter(
            Commande.restaurantId == restaurant_id,
            Commande.isActive == True,
            Commande.statut == CommandeStatut.PAID,
            Commande.createdAt >= c_start,
            Commande.createdAt < c_end
        ).scalar() or 0.0

        status_labels = {
            CommandeStatut.PAID: "Payées",
            CommandeStatut.PENDING: "En attente",
            CommandeStatut.CANCELLED: "Annulées",
        }

        items: List[OrderStatusDistributionItem] = []
        # Parcourir les statuts dans un ordre fixe
        for st in [CommandeStatut.PAID, CommandeStatut.PENDING, CommandeStatut.CANCELLED]:
            row = stats_map.get(st)
            cnt = int(row.statut_count) if row else 0
            amt = round(float(row.statut_amount), 2) if row else 0.0
            pct = round((cnt / float(total_orders)) * 100.0, 2) if total_orders > 0 else 0.0

            items.append(OrderStatusDistributionItem(
                statut=st.value,
                label=status_labels.get(st, st.value),
                count=cnt,
                percentage=pct,
                total_amount=amt
            ))

        return OrdersDistributionResponse(
            period=period,
            currency="XOF",
            type="status",
            total_orders=total_orders,
            total_revenue=round(float(paid_revenue), 2),
            status_distribution=items,
            category_distribution=None
        )

    else:
        # Répartition par nature de produit (Repas vs Boisson)
        total_quantity_all = db.query(
            func.coalesce(func.sum(CommandeArticle.qte), 0)
        ).select_from(CommandeArticle).join(
            Commande, CommandeArticle.commandeId == Commande.id
        ).filter(
            Commande.restaurantId == restaurant_id,
            Commande.isActive == True,
            Commande.statut == CommandeStatut.PAID,
            CommandeArticle.isActive == True,
            Commande.createdAt >= c_start,
            Commande.createdAt < c_end
        ).scalar() or 0

        paid_revenue = db.query(
            func.coalesce(func.sum(Commande.total), 0.0)
        ).filter(
            Commande.restaurantId == restaurant_id,
            Commande.isActive == True,
            Commande.statut == CommandeStatut.PAID,
            Commande.createdAt >= c_start,
            Commande.createdAt < c_end
        ).scalar() or 0.0

        rows = db.query(
            case((CommandeArticle.repasId.isnot(None), "Repas"), else_="Boissons").label("category_type"),
            func.sum(CommandeArticle.qte).label("cat_qte"),
            func.sum(CommandeArticle.sousTotal).label("cat_revenue")
        ).select_from(CommandeArticle).join(
            Commande, CommandeArticle.commandeId == Commande.id
        ).filter(
            Commande.restaurantId == restaurant_id,
            Commande.isActive == True,
            Commande.statut == CommandeStatut.PAID,
            CommandeArticle.isActive == True,
            Commande.createdAt >= c_start,
            Commande.createdAt < c_end
        ).group_by(
            case((CommandeArticle.repasId.isnot(None), "Repas"), else_="Boissons")
        ).all()

        cat_items: List[OrderCategoryDistributionItem] = []
        for r in rows:
            qte = int(r.cat_qte or 0)
            rev = round(float(r.cat_revenue or 0.0), 2)
            pct = round((qte / float(total_quantity_all)) * 100.0, 2) if total_quantity_all > 0 else 0.0
            cat_type = "repas" if r.category_type == "Repas" else "boissons"

            cat_items.append(OrderCategoryDistributionItem(
                id=None,
                name=r.category_type,
                type=cat_type,
                quantity=qte,
                revenue=rev,
                percentage=pct
            ))

        total_orders_count = db.query(
            func.count(Commande.id)
        ).filter(
            Commande.restaurantId == restaurant_id,
            Commande.isActive == True,
            Commande.createdAt >= c_start,
            Commande.createdAt < c_end
        ).scalar() or 0

        return OrdersDistributionResponse(
            period=period,
            currency="XOF",
            type="category",
            total_orders=int(total_orders_count),
            total_revenue=round(float(paid_revenue), 2),
            status_distribution=None,
            category_distribution=cat_items
        )
