import pytest
from uuid import uuid4
from unittest.mock import MagicMock
from app.models.boisson import Boisson
from app.models.casier import Casier
from app.enums import CasierType, BoissonContenance
from app.schemas.appro_boisson import ApproBoissonCreate, ApproBoissonUpdate
from app.services.appro_boisson_service import (
    create_appro_boisson,
    update_appro_boisson,
    delete_appro_boisson,
    get_casier_capacity
)

from pydantic import ValidationError

def test_casier_capacity_mapping():
    assert get_casier_capacity(CasierType.T12) == 12
    assert get_casier_capacity(CasierType.T20) == 20
    assert get_casier_capacity(CasierType.T24) == 24
    with pytest.raises(ValueError, match="Capacité inconnue ou invalide"):
        get_casier_capacity("UNKNOWN_TYPE")

def test_appro_boisson_schema_validations():
    boisson_id = uuid4()
    casier_id = uuid4()

    # Valid schema creation
    valid_create = ApproBoissonCreate(
        boissonId=boisson_id,
        casierId=casier_id,
        prixAchat=4500.0,
        nbreCasier=2
    )
    assert valid_create.nbreCasier == 2

    # Invalid nbreCasier (0 or negative)
    with pytest.raises(ValidationError):
        ApproBoissonCreate(
            boissonId=boisson_id,
            casierId=casier_id,
            prixAchat=4500.0,
            nbreCasier=0
        )

    with pytest.raises(ValidationError):
        ApproBoissonCreate(
            boissonId=boisson_id,
            casierId=casier_id,
            prixAchat=4500.0,
            nbreCasier=-1
        )

    # Invalid prixAchat (0 or negative)
    with pytest.raises(ValidationError):
        ApproBoissonCreate(
            boissonId=boisson_id,
            casierId=casier_id,
            prixAchat=0.0,
            nbreCasier=2
        )

    # Invalid ApproBoissonUpdate
    with pytest.raises(ValidationError):
        ApproBoissonUpdate(nbreCasier=0)

    with pytest.raises(ValidationError):
        ApproBoissonUpdate(prixAchat=-10.0)

def test_create_appro_boisson_stock_increment():
    db_mock = MagicMock()
    restaurant_id = uuid4()
    boisson_id = uuid4()
    
    boisson = Boisson(
        id=boisson_id,
        restaurantId=restaurant_id,
        nomBoisson="castel",
        contenance=BoissonContenance.CL55,
        prixVente=700.0,
        stock=0
    )

    casier_t12 = Casier(id=uuid4(), typeCasier=CasierType.T12, restaurantId=restaurant_id, isActive=True)
    casier_t20 = Casier(id=uuid4(), typeCasier=CasierType.T20, restaurantId=restaurant_id, isActive=True)
    casier_t24 = Casier(id=uuid4(), typeCasier=CasierType.T24, restaurantId=restaurant_id, isActive=True)

    def mock_query(model):
        q = MagicMock()
        def mock_filter(*args, **kwargs):
            fq = MagicMock()
            # boisson lookup
            if model == Boisson:
                fq.first.return_value = boisson
            # casier lookup
            elif model == Casier:
                # We can check which casier id is being requested in real tests, or handle dynamic returns
                pass
            return fq
        q.filter.side_effect = mock_filter
        return q

    # 1. Appro with T20 (3 casiers -> 3 * 20 = 60 bottles)
    db_mock.query.side_effect = lambda model: MagicMock(
        filter=lambda *args, **kwargs: MagicMock(
            first=lambda: boisson if model == Boisson else casier_t20
        )
    )

    appro1_data = ApproBoissonCreate(
        boissonId=boisson_id,
        casierId=casier_t20.id,
        prixAchat=4980.0,
        nbreCasier=3
    )

    db_appro1 = create_appro_boisson(db_mock, appro1_data, restaurant_id)
    assert boisson.stock == 60

    # 2. Successive appro with T12 (2 casiers -> 2 * 12 = 24 bottles)
    db_mock.query.side_effect = lambda model: MagicMock(
        filter=lambda *args, **kwargs: MagicMock(
            first=lambda: boisson if model == Boisson else casier_t12
        )
    )

    appro2_data = ApproBoissonCreate(
        boissonId=boisson_id,
        casierId=casier_t12.id,
        prixAchat=3000.0,
        nbreCasier=2
    )

    db_appro2 = create_appro_boisson(db_mock, appro2_data, restaurant_id)
    assert boisson.stock == 84  # 60 + 24

    # 3. Successive appro with T24 (1 casier -> 1 * 24 = 24 bottles)
    db_mock.query.side_effect = lambda model: MagicMock(
        filter=lambda *args, **kwargs: MagicMock(
            first=lambda: boisson if model == Boisson else casier_t24
        )
    )

    appro3_data = ApproBoissonCreate(
        boissonId=boisson_id,
        casierId=casier_t24.id,
        prixAchat=6000.0,
        nbreCasier=1
    )

    db_appro3 = create_appro_boisson(db_mock, appro3_data, restaurant_id)
    assert boisson.stock == 108  # 84 + 24

def test_update_and_delete_appro_boisson_stock():
    db_mock = MagicMock()
    restaurant_id = uuid4()
    boisson_id = uuid4()

    boisson = Boisson(
        id=boisson_id,
        restaurantId=restaurant_id,
        nomBoisson="castel",
        contenance=BoissonContenance.CL55,
        prixVente=700.0,
        stock=60
    )
    casier_t20 = Casier(id=uuid4(), typeCasier=CasierType.T20, restaurantId=restaurant_id, isActive=True)

    appro_mock = MagicMock()
    appro_mock.id = uuid4()
    appro_mock.boissonId = boisson_id
    appro_mock.casierId = casier_t20.id
    appro_mock.nbreCasier = 3
    appro_mock.casier = casier_t20
    appro_mock.boisson = boisson
    appro_mock.isActive = True

    db_mock.query.side_effect = lambda model: MagicMock(
        join=lambda *a, **kw: MagicMock(
            filter=lambda *args, **kwargs: MagicMock(
                first=lambda: appro_mock
            )
        )
    )

    # Update nbreCasier from 3 to 5 (+2 casiers of T20 = +40 bottles)
    update_data = ApproBoissonUpdate(nbreCasier=5)
    updated_appro = update_appro_boisson(db_mock, appro_mock.id, update_data, restaurant_id)

    assert boisson.stock == 100  # 60 + (5*20 - 3*20) = 100

    # Delete appro (removes 5 * 20 = 100 bottles)
    delete_appro_boisson(db_mock, appro_mock.id, restaurant_id)

    assert boisson.stock == 0
    assert appro_mock.isActive == False
