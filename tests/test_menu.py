import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime
from unittest.mock import MagicMock
from app.main import app
from app.database import get_session
from app.dependencies import get_current_user, require_admin, get_user_restaurant_id
from app.models.user import User
from app.models.restaurant import Restaurant
from app.models.menu_famille import MenuFamille
from app.models.menu_famille_image import MenuFamilleImage
from app.models.menu_categorie import MenuCategorie
from app.models.menu_repas import MenuRepas
from app.models.menu_boisson import MenuBoisson
from app.models.repas import Repas
from app.models.boisson import Boisson
from app.enums import BoissonContenance, MenuCategorieNom

@pytest.fixture
def client():
    return TestClient(app)

class MockQuery:
    def __init__(self, items=None):
        if items is None:
            self.items = []
        elif isinstance(items, list):
            self.items = items
        else:
            self.items = [items]

    def options(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def join(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self.items[0] if self.items else None

    def all(self):
        return self.items

def test_get_public_menu_display_empty(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    restaurant_obj = Restaurant(
        id=restaurant_id,
        name="Test Resto",
        address="Rue 1",
        phone="123456",
        ownerId=uuid4()
    )

    app.dependency_overrides[get_session] = lambda: db_mock

    # 1st query: Restaurant, 2nd query: MenuFamilles, 3rd query: MenuBoissons
    queries = [
        MockQuery(restaurant_obj),
        MockQuery([]),
        MockQuery([])
    ]
    db_mock.query.side_effect = lambda model: queries.pop(0)

    response = client.get(f"/menus/display/{restaurant_id}")
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["restaurant"]["id"] == str(restaurant_id)
    assert data["restaurant"]["name"] == "Test Resto"
    assert data["familles"] == []
    assert data["boissons"] == []

def test_get_public_menu_display_populated(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    famille_id = uuid4()
    cat_id = uuid4()
    repas_id = uuid4()
    boisson_id = uuid4()

    restaurant_obj = Restaurant(
        id=restaurant_id,
        name="Gourmet Heaven",
        address="Central Ave",
        phone="+229 00000000",
        ownerId=uuid4()
    )

    repas_obj = Repas(
        id=repas_id,
        restaurantId=restaurant_id,
        nomRepas="Burger Chef",
        prix=4500.0,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    boisson_obj = Boisson(
        id=boisson_id,
        restaurantId=restaurant_id,
        nomBoisson="Jus de Pomme",
        contenance=BoissonContenance.CL33,
        prixVente=1000.0,
        stock=10,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    menu_repas_obj = MenuRepas(
        id=uuid4(),
        menuCategorieId=cat_id,
        repasId=repas_id,
        ordre=1,
        repas=repas_obj,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    cat_obj = MenuCategorie(
        id=cat_id,
        menuFamilleId=famille_id,
        nom=MenuCategorieNom.SPECIALITE,
        ordre=1,
        repasList=[menu_repas_obj],
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    famille_img = MenuFamilleImage(
        id=uuid4(),
        familleId=famille_id,
        imageUrl="https://uploadcenter.com/img1.png",
        ordre=1
    )

    famille_obj = MenuFamille(
        id=famille_id,
        restaurantId=restaurant_id,
        nom="Plats principaux",
        ordre=1,
        images=[famille_img],
        categories=[cat_obj],
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    menu_boisson_obj = MenuBoisson(
        id=uuid4(),
        boissonId=boisson_id,
        ordre=1,
        imageUrl="https://uploadcenter.com/boisson1.png",
        boisson=boisson_obj,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    app.dependency_overrides[get_session] = lambda: db_mock

    queries = [
        MockQuery(restaurant_obj),
        MockQuery([famille_obj]),
        MockQuery([menu_boisson_obj])
    ]
    db_mock.query.side_effect = lambda model: queries.pop(0)

    response = client.get(f"/menus/display/{restaurant_id}")
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["restaurant"]["name"] == "Gourmet Heaven"
    assert len(data["familles"]) == 1
    assert data["familles"][0]["nom"] == "Plats principaux"
    assert data["familles"][0]["images"][0]["imageUrl"] == "https://uploadcenter.com/img1.png"
    assert data["familles"][0]["categories"][0]["nom"] == MenuCategorieNom.SPECIALITE
    assert data["familles"][0]["categories"][0]["repasList"][0]["repas"]["nomRepas"] == "Burger Chef"
    assert data["boissons"][0]["boisson"]["nomBoisson"] == "Jus de Pomme"

from unittest.mock import patch

def test_upload_center_presign_and_complete_endpoints(client):
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com")
    restaurant_id = uuid4()

    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    with patch("app.services.upload_center_service.presign_upload") as mock_presign, \
         patch("app.services.upload_center_service.complete_upload") as mock_complete:

        mock_presign.return_value = {
            "file_id": "file_abc123",
            "upload_url": "https://api.uploadscenter.com/presigned-put-url",
            "expires_in": 3600
        }
        mock_complete.return_value = {
            "id": "file_abc123",
            "url": "https://cdn.uploadscenter.com/public/image123.png",
            "status": "completed",
            "original_name": "menu_plat.png",
            "mime_type": "image/png",
            "size_bytes": 1024,
            "visibility": "public"
        }

        # 1. Presign upload
        presign_payload = {
            "filename": "menu_plat.png",
            "sizeBytes": 1024,
            "mimeType": "image/png"
        }
        res_presign = client.post("/menus/upload-center/presign", json=presign_payload)
        assert res_presign.status_code == 200, res_presign.text
        data_presign = res_presign.json()
        assert data_presign["file_id"] == "file_abc123"
        assert data_presign["upload_url"] == "https://api.uploadscenter.com/presigned-put-url"

        # 2. Complete upload
        complete_payload = {"file_id": "file_abc123"}
        res_complete = client.post("/menus/upload-center/complete", json=complete_payload)
        assert res_complete.status_code == 200, res_complete.text
        data_complete = res_complete.json()
        assert data_complete["id"] == "file_abc123"
        assert data_complete["url"] == "https://cdn.uploadscenter.com/public/image123.png"

    app.dependency_overrides.clear()

def test_crud_menu_famille(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com")

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    def mock_add(obj):
        obj.id = uuid4()
        obj.createdAt = datetime.now()
        obj.updatedAt = datetime.now()

    db_mock.add.side_effect = mock_add

    # Create Famille
    payload = {"nom": "Desserts", "ordre": 2}
    response = client.post("/menus/familles", json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["nom"] == "Desserts"

    # List Familles
    famille_obj = MenuFamille(
        id=uuid4(),
        restaurantId=restaurant_id,
        nom="Desserts",
        ordre=2,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )
    db_mock.query.side_effect = lambda model: MockQuery([famille_obj])

    response = client.get("/menus/familles")
    assert response.status_code == 200
    assert len(response.json()) == 1

    app.dependency_overrides.clear()

def test_menu_famille_image_upload_center_reference(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    famille_id = uuid4()
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com")

    famille_obj = MenuFamille(
        id=famille_id,
        restaurantId=restaurant_id,
        nom="Boissons Chaudes",
        ordre=1,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    def mock_add(obj):
        obj.id = uuid4()
        obj.createdAt = datetime.now()
        obj.updatedAt = datetime.now()

    db_mock.add.side_effect = mock_add
    db_mock.query.side_effect = lambda model: MockQuery(famille_obj)

    payload = {
        "familleId": str(famille_id),
        "imageUrl": "https://uploadcenter.cloud/images/famille_hot.jpg",
        "ordre": 1
    }
    response = client.post("/menus/famille-images", json=payload)
    app.dependency_overrides.clear()

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["imageUrl"] == "https://uploadcenter.cloud/images/famille_hot.jpg"
    assert data["familleId"] == str(famille_id)

def test_multi_tenant_isolation_repas_association(client):
    db_mock = MagicMock()
    restaurant_a_id = uuid4()
    restaurant_b_id = uuid4()
    cat_id = uuid4()
    repas_belonging_to_b_id = uuid4()
    admin_user = User(id=uuid4(), name="Admin A", email="admina@test.com")

    # Category belongs to Restaurant A
    cat_obj = MenuCategorie(
        id=cat_id,
        menuFamilleId=uuid4(),
        nom=MenuCategorieNom.CLASSIQUE,
        ordre=1,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    # Repas belongs to Restaurant B!
    repas_b_obj = Repas(
        id=repas_belonging_to_b_id,
        restaurantId=restaurant_b_id,
        nomRepas="Pizza Resto B",
        prix=5000.0,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_a_id

    # 1st query gets Categorie (success for Resto A), 2nd query checks Repas for Resto A (returns None because it belongs to Resto B)
    queries = [
        MockQuery(cat_obj),
        MockQuery([]) # Repas not found for Restaurant A
    ]
    db_mock.query.side_effect = lambda model: queries.pop(0)

    payload = {
        "menuCategorieId": str(cat_id),
        "repasId": str(repas_belonging_to_b_id),
        "ordre": 1
    }

    response = client.post("/menus/repas", json=payload)
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Repas non trouvé pour ce restaurant"

def test_get_all_public_menus_display(client):
    db_mock = MagicMock()
    resto1_id = uuid4()
    resto2_id = uuid4()

    resto1 = Restaurant(id=resto1_id, name="Resto 1", address="Addr 1", phone="111", ownerId=uuid4())
    resto2 = Restaurant(id=resto2_id, name="Resto 2", address="Addr 2", phone="222", ownerId=uuid4())

    app.dependency_overrides[get_session] = lambda: db_mock

    # db.query(Restaurant).all() -> returns [resto1, resto2]
    # For resto1: 1st query gets resto1, 2nd gets familles, 3rd gets boissons
    # For resto2: 1st query gets resto2, 2nd gets familles, 3rd gets boissons
    queries = [
        MockQuery([resto1, resto2]),
        MockQuery(resto1), MockQuery([]), MockQuery([]),
        MockQuery(resto2), MockQuery([]), MockQuery([])
    ]
    db_mock.query.side_effect = lambda model: queries.pop(0)

    response = client.get("/menus/display")
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["restaurant"]["name"] == "Resto 1"
    assert data[1]["restaurant"]["name"] == "Resto 2"

def test_public_get_familles_without_auth(client):
    db_mock = MagicMock()
    famille_id = uuid4()
    famille_obj = MenuFamille(
        id=famille_id,
        restaurantId=uuid4(),
        nom="Public Famille",
        ordre=1,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    db_mock.query.side_effect = lambda model: MockQuery([famille_obj])

    # No auth dependencies overridden or passed
    res_list = client.get("/menus/familles")
    assert res_list.status_code == 200, res_list.text
    assert len(res_list.json()) == 1
    assert res_list.json()[0]["nom"] == "Public Famille"

    db_mock.query.side_effect = lambda model: MockQuery(famille_obj)
    res_detail = client.get(f"/menus/familles/{famille_id}")
    app.dependency_overrides.clear()

    assert res_detail.status_code == 200, res_detail.text
    assert res_detail.json()["id"] == str(famille_id)

def test_modification_requires_admin(client):
    # Attempting to POST /menus/familles without authentication
    payload = {"nom": "Unauthorized Famille"}
    response = client.post("/menus/familles", json=payload)
    assert response.status_code in (401, 403)

def test_direct_file_upload_endpoint(client):
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com")
    restaurant_id = uuid4()

    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    with patch("app.services.upload_center_service.upload_file_content") as mock_upload:
        mock_upload.return_value = {
            "id": "file_file123",
            "url": "https://cdn.uploadscenter.com/public/my_photo.png",
            "status": "completed",
            "original_name": "my_photo.png",
            "mime_type": "image/png",
            "size_bytes": 12,
            "visibility": "public"
        }

        files = {"file": ("my_photo.png", b"fake image bytes", "image/png")}
        response = client.post("/menus/upload", files=files)
        app.dependency_overrides.clear()

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == "file_file123"
        assert data["url"] == "https://cdn.uploadscenter.com/public/my_photo.png"
