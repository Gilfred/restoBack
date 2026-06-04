from enum import Enum

class BoissonContenance(str, Enum):
    CL55 = "0,55cl"
    CL33 = "0,33cl"

class MethodePaiementEnum(str, Enum):
    MOMO = "momo"
    FEDAPAY = "fedapay"
    CASH = "cash"

class CasierType(str, Enum):
    T12 = "12T"
    T20 = "20T"
    T24 = "24T"

class UniteType(str, Enum):
    KG = "kg"
    LITRES = "litres"

class CommandeStatut(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"

class ActivationStatus(str, Enum):
    PENDING = "pending"
    ACTIVATED = "activated"
    REJECTED = "rejected"
