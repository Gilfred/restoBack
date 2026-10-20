from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DashboardPeriodEnum(str, Enum):
    TODAY = "today"
    SEVEN_DAYS = "7d"
    THIRTY_DAYS = "30d"
    CURRENT_MONTH = "current_month"
    PREVIOUS_MONTH = "previous_month"


class MetricComparison(BaseModel):
    current: float = Field(..., description="Valeur de la période actuelle")
    previous: float = Field(..., description="Valeur de la période de référence précédente")
    variation_absolute: float = Field(..., description="Variation absolue (current - previous)")
    percentage_change: Optional[float] = Field(
        None,
        description="Taux d'évolution en % (null si previous == 0 et current > 0)"
    )


class DashboardOverviewResponse(BaseModel):
    period: DashboardPeriodEnum
    currency: str = "XOF"
    revenue: MetricComparison
    orders_count: MetricComparison
    total_orders_received: MetricComparison
    limitations_note: Optional[str] = (
        "Le chiffre d'affaires est basé sur le montant total des commandes validées "
        "et payées (statut PAID). Le modèle de données actuel ne traçant pas les règlements "
        "dans ReglementFacture, les éventuels paiements partiels ou remboursements ne sont pas inclus."
    )


class SalesDataPoint(BaseModel):
    date: str = Field(..., description="Date au format YYYY-MM-DD")
    revenue: float = Field(..., description="Chiffre d'affaires payé du jour")
    orders_count: int = Field(..., description="Nombre de commandes payées du jour")
    total_orders_received: int = Field(..., description="Nombre total de commandes reçues du jour")


class SalesEvolutionResponse(BaseModel):
    period: DashboardPeriodEnum
    currency: str = "XOF"
    data: List[SalesDataPoint]
