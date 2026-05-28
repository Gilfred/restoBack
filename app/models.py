from typing import List, Optional, Union
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel, Column, DateTime, func
from app.enums import (
    BoissonContenance,
    MethodePaiementEnum,
    CasierType,
    UniteType,
    CommandeStatut
)

# --- Models ---

class UserRole(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    userId: int = Field(foreign_key="user.id")
    roleId: int = Field(foreign_key="role.id")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

class RolePermission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    roleId: int = Field(foreign_key="role.id")
    permissionId: int = Field(foreign_key="permission.id")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

class Permission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    roles: List["Role"] = Relationship(back_populates="permissions", link_model=RolePermission)

class Role(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    users: List["User"] = Relationship(back_populates="roles", link_model=UserRole)
    permissions: List[Permission] = Relationship(back_populates="roles", link_model=RolePermission)

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(index=True, unique=True)
    emailVerified: Optional[datetime] = None
    image: Optional[str] = None
    password: str
    restaurantId: Optional[int] = Field(default=None, foreign_key="restaurant.id")
    isActive: bool = Field(default=True)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    roles: List[Role] = Relationship(back_populates="users", link_model=UserRole)
    restaurant: Optional["Restaurant"] = Relationship(
        back_populates="staff",
        sa_relationship_kwargs={"foreign_keys": "[User.restaurantId]"}
    )
    owned_restaurants: List["Restaurant"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"foreign_keys": "[Restaurant.ownerId]"}
    )
    sessions: List["Session"] = Relationship(back_populates="user")
    accounts: List["Account"] = Relationship(back_populates="user")
    commandes: List["Commande"] = Relationship(back_populates="user")

class Session(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    expiresAt: datetime
    token: str = Field(unique=True)
    userId: int = Field(foreign_key="user.id")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="sessions")

class Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str
    userId: int = Field(foreign_key="user.id")
    providerAccountId: str
    password: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="accounts")

class Verification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    identifier: str
    value: str
    expiresAt: datetime
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

class Restaurant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    address: str
    phone: str
    ownerId: int = Field(foreign_key="user.id")
    isActive: bool = Field(default=True)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    owner: User = Relationship(back_populates="owned_restaurants", sa_relationship_kwargs={"foreign_keys": "[Restaurant.ownerId]"})
    staff: List[User] = Relationship(back_populates="restaurant", sa_relationship_kwargs={"foreign_keys": "[User.restaurantId]"})
    boissons: List["Boisson"] = Relationship(back_populates="restaurant")
    repas: List["Repas"] = Relationship(back_populates="restaurant")
    condiments: List["Condiment"] = Relationship(back_populates="restaurant")
    commandes: List["Commande"] = Relationship(back_populates="restaurant")
    reglementFactures: List["ReglementFacture"] = Relationship(back_populates="restaurant")
    casiers: List["Casier"] = Relationship(back_populates="restaurant")
    unites: List["Unite"] = Relationship(back_populates="restaurant")

class Boisson(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    restaurantId: int = Field(foreign_key="restaurant.id")
    nomBoisson: str
    contenance: BoissonContenance
    prixVente: float
    stock: int = Field(default=0)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    restaurant: Restaurant = Relationship(back_populates="boissons")
    approBoissons: List["ApproBoisson"] = Relationship(back_populates="boisson")

class Repas(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    restaurantId: int = Field(foreign_key="restaurant.id")
    nomRepas: str
    prix: float
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    restaurant: Restaurant = Relationship(back_populates="repas")

class Casier(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    typeCasier: CasierType
    restaurantId: int = Field(foreign_key="restaurant.id")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    restaurant: Restaurant = Relationship(back_populates="casiers")
    approBoissons: List["ApproBoisson"] = Relationship(back_populates="casier")

class ApproBoisson(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    boissonId: int = Field(foreign_key="boisson.id")
    casierId: int = Field(foreign_key="casier.id")
    prixAchat: float
    nbreCasier: int
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    boisson: Boisson = Relationship(back_populates="approBoissons")
    casier: Casier = Relationship(back_populates="approBoissons")

class Unite(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    unite: UniteType
    restaurantId: int = Field(foreign_key="restaurant.id")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    restaurant: Restaurant = Relationship(back_populates="unites")
    approCuisines: List["ApproCuisine"] = Relationship(back_populates="unite")

class Condiment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    restaurantId: int = Field(foreign_key="restaurant.id")
    nomcondiment: str
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    restaurant: Restaurant = Relationship(back_populates="condiments")
    approCuisines: List["ApproCuisine"] = Relationship(back_populates="condiment")

class ApproCuisine(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    condimentId: int = Field(foreign_key="condiment.id")
    uniteId: int = Field(foreign_key="unite.id")
    prix: float
    qte: float
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    condiment: Condiment = Relationship(back_populates="approCuisines")
    unite: Unite = Relationship(back_populates="approCuisines")

class Commande(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    restaurantId: int = Field(foreign_key="restaurant.id")
    numeroCommande: str = Field(index=True)
    userId: int = Field(foreign_key="user.id")
    total: float = Field(default=0.0)
    statut: CommandeStatut = Field(default=CommandeStatut.PENDING)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    restaurant: Restaurant = Relationship(back_populates="commandes")
    user: User = Relationship(back_populates="commandes")
    articles: List["CommandeArticle"] = Relationship(back_populates="commande")
    reglementFactures: List["ReglementFacture"] = Relationship(back_populates="commande")

class CommandeArticle(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    commandeId: int = Field(foreign_key="commande.id")
    boissonId: Optional[int] = Field(default=None, foreign_key="boisson.id")
    repasId: Optional[int] = Field(default=None, foreign_key="repas.id")
    qte: int
    prixUnitaire: float
    sousTotal: float
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    commande: Commande = Relationship(back_populates="articles")

class MethodePayment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nomMethode: MethodePaiementEnum
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    reglementFactures: List["ReglementFacture"] = Relationship(back_populates="methode")

class ReglementFacture(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    restaurantId: int = Field(foreign_key="restaurant.id")
    commandeId: int = Field(foreign_key="commande.id")
    montant: float
    methodeId: int = Field(foreign_key="methodepayment.id")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    restaurant: Restaurant = Relationship(back_populates="reglementFactures")
    commande: Commande = Relationship(back_populates="reglementFactures")
    methode: MethodePayment = Relationship(back_populates="reglementFactures")
