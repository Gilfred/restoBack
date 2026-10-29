from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_session
from app.dependencies import (
    require_admin,
    get_user_restaurant_id,
)
from app.schemas.dashboard import (
    DashboardPeriodEnum,
    DashboardOverviewResponse,
    SalesEvolutionResponse,
    WeeklySalesEvolutionResponse,
    TopSellingProductsResponse,
    OrdersDistributionResponse,
)
from app.services import dashboard_service

router = APIRouter()


@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(
    period: DashboardPeriodEnum = Query(
        DashboardPeriodEnum.SEVEN_DAYS,
        description="Période sélectionnée (today, 7d, 30d, current_month, previous_month)"
    ),
    db: Session = Depends(get_session),
    current_user=Depends(require_admin),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
):
    """
    Retourne les indicateurs clés du dashboard (CA, nombre de commandes payées,
    total de commandes reçues) et leurs comparaisons à la période précédente.
    Accès réservé aux administrateurs (ADMIN, SUPERADMIN, propriétaire de restaurant).
    """
    return dashboard_service.get_dashboard_overview(
        db=db,
        restaurant_id=restaurant_id,
        period=period,
    )


@router.get("/sales/weekly", response_model=WeeklySalesEvolutionResponse)
def get_weekly_sales_evolution(
    db: Session = Depends(get_session),
    current_user=Depends(require_admin),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
):
    """
    Graphe 1 — Évolution hebdomadaire des ventes.
    Retourne les données journalières de la semaine courante (Lundi à Dimanche)
    avec libellés des jours en français et complétion à zéro.
    Accès réservé aux administrateurs (ADMIN, SUPERADMIN, propriétaire de restaurant).
    """
    return dashboard_service.get_weekly_sales_evolution(
        db=db,
        restaurant_id=restaurant_id,
    )


@router.get("/products/top-selling", response_model=TopSellingProductsResponse)
def get_top_selling_products(
    period: DashboardPeriodEnum = Query(
        DashboardPeriodEnum.SEVEN_DAYS,
        description="Période sélectionnée (today, 7d, 30d, current_month, previous_month)"
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Nombre maximal de produits retournés (par défaut 10)"
    ),
    db: Session = Depends(get_session),
    current_user=Depends(require_admin),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
):
    """
    Graphe 2 — Produit le plus vendu.
    Identifie et classe les produits les plus vendus pendant une période données.
    Distinction repas/boisson, agrégation des quantités, CA et pourcentage du total.
    Accès réservé aux administrateurs (ADMIN, SUPERADMIN, propriétaire de restaurant).
    """
    return dashboard_service.get_top_selling_products(
        db=db,
        restaurant_id=restaurant_id,
        period=period,
        limit=limit,
    )


@router.get("/orders/distribution", response_model=OrdersDistributionResponse)
def get_orders_distribution(
    period: DashboardPeriodEnum = Query(
        DashboardPeriodEnum.SEVEN_DAYS,
        description="Période sélectionnée (today, 7d, 30d, current_month, previous_month)"
    ),
    type: str = Query(
        "status",
        description="Type de distribution : 'status' (par statut) ou 'category' (par type/famille)"
    ),
    db: Session = Depends(get_session),
    current_user=Depends(require_admin),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
):
    """
    Graphe 3 — Spectre de répartition des commandes.
    Fournit la répartition des commandes par statut (Option A) ou par nature de produit (Option B).
    Accès réservé aux administrateurs (ADMIN, SUPERADMIN, propriétaire de restaurant).
    """
    return dashboard_service.get_orders_distribution(
        db=db,
        restaurant_id=restaurant_id,
        period=period,
        dist_type=type,
    )


@router.get("/sales", response_model=SalesEvolutionResponse)
def get_sales_evolution(
    period: DashboardPeriodEnum = Query(
        DashboardPeriodEnum.SEVEN_DAYS,
        description="Période sélectionnée (today, 7d, 30d, current_month, previous_month)"
    ),
    db: Session = Depends(get_session),
    current_user=Depends(require_admin),
    restaurant_id: UUID = Depends(get_user_restaurant_id),
):
    """
    Retourne la série chronologique pour le graphique 'Évolution des ventes'
    sur la période sélectionnée, complétée avec des zéro pour les jours sans vente.
    Accès réservé aux administrateurs (ADMIN, SUPERADMIN, propriétaire de restaurant).
    """
    return dashboard_service.get_sales_evolution(
        db=db,
        restaurant_id=restaurant_id,
        period=period,
    )
