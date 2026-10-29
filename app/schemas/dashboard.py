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


class WeeklySalesDataPoint(BaseModel):
    date: str = Field(..., description="Date au format YYYY-MM-DD")
    day: str = Field(..., description="Libellé du jour en français (ex: Lundi)")
    revenue: float = Field(..., description="Chiffre d'affaires payé du jour")
    orders_count: int = Field(..., description="Nombre de commandes payées du jour")
    total_orders_received: int = Field(default=0, description="Nombre total de commandes reçues du jour")


class WeeklySalesEvolutionResponse(BaseModel):
    period: str = Field(default="weekly", description="Identifiant de la période hebdomadaire")
    currency: str = "XOF"
    start_date: str = Field(..., description="Date de début de la semaine (Lundi)")
    end_date: str = Field(..., description="Date de fin de la semaine (Dimanche)")
    data: List[WeeklySalesDataPoint]


class TopSellingProductItem(BaseModel):
    product_id: str = Field(..., description="Identifiant UUID du produit")
    name: str = Field(..., description="Nom du produit (repas ou boisson)")
    type: str = Field(..., description="Nature du produit ('repas' ou 'boisson')")
    quantity: int = Field(..., description="Quantité totale vendue sur la période")
    revenue: float = Field(..., description="Chiffre d'affaires généré par le produit")
    percentage: float = Field(..., description="Pourcentage dans le total des quantités vendues")


class TopSellingProductsResponse(BaseModel):
    period: DashboardPeriodEnum
    currency: str = "XOF"
    total_quantity: int = Field(..., description="Quantité totale de tous les produits vendus")
    data: List[TopSellingProductItem]


class OrderStatusDistributionItem(BaseModel):
    statut: str = Field(..., description="Valeur du statut ('pending', 'paid', 'cancelled')")
    label: str = Field(..., description="Libellé affichable du statut")
    count: int = Field(..., description="Nombre de commandes rattachées au statut")
    percentage: float = Field(..., description="Pourcentage du nombre de commandes")
    total_amount: float = Field(..., description="Montant cumulé des commandes")


class OrderCategoryDistributionItem(BaseModel):
    id: Optional[str] = Field(None, description="Identifiant de la famille/catégorie")
    name: str = Field(..., description="Nom de la famille ou catégorie de menu")
    type: str = Field(..., description="Type de regroupement ('famille_repas', 'famille_boisson', 'non_classe')")
    quantity: int = Field(..., description="Quantité totale d'articles vendus")
    revenue: float = Field(..., description="Chiffre d'affaires généré")
    percentage: float = Field(..., description="Pourcentage par rapport au total (chiffre d'affaires ou quantité)")


class OrdersDistributionResponse(BaseModel):
    period: DashboardPeriodEnum
    currency: str = "XOF"
    type: str = Field(..., description="Type de distribution ('status' ou 'category')")
    total_orders: int = Field(..., description="Nombre total de commandes sur la période")
    total_revenue: float = Field(..., description="Chiffre d'affaires total sur la période")
    status_distribution: Optional[List[OrderStatusDistributionItem]] = Field(
        None, description="Répartition par statut de commande (Option A)"
    )
    category_distribution: Optional[List[OrderCategoryDistributionItem]] = Field(
        None, description="Répartition par famille/catégorie (Option B)"
    )
