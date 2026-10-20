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
