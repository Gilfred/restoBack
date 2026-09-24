import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime
from unittest.mock import MagicMock, patch
from app.main import app
from app.database import get_session
from app.dependencies import get_current_user, require_admin, get_user_restaurant_id
from app.models.user import User
from app.models.restaurant import Restaurant
from app.models.menu_famille import MenuFamille
from app.models.menu_famille_image import MenuFamilleImage
from app.models.menu_categorie import MenuCategorie
from app.models.menu_repas import MenuRepas
from app.models.menu_boisson_famille import MenuBoissonFamille
from app.models.menu_boisson_image import MenuBoissonImage
from app.models.menu_boisson import MenuBoisson
from app.models.repas import Repas
from app.models.boisson import Boisson
from app.enums import BoissonContenance, MenuCategorieNom

@pytest.fixture
def client():
    return TestClient(app)

class MockQuery:
    def __init__(self, items=None, count_value=None):
        if items is None:
            self.items = []
        elif isinstance(items, list):
            self.items = items
        else:
            self.items = [items]
        self._count_value = count_value

    def options(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def join(self, *args, **kwargs):
        return self

    def outerjoin(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def count(self):
        if self._count_value is not None:
            return self._count_value
        return len(self.items)

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

    # 1st query: Restaurant list, 2nd query: MenuFamilles, 3rd query: MenuBoissonFamilles
    queries = [
        MockQuery([restaurant_obj]),
        MockQuery([]),
        MockQuery([])
    ]
    db_mock.query.side_effect = lambda model: queries.pop(0)

    response = client.get("/menus/display")
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert "restaurants" in data
    assert len(data["restaurants"]) == 1
    resto_menu = data["restaurants"][0]
    assert resto_menu["restaurant"]["id"] == str(restaurant_id)
    assert resto_menu["restaurant"]["name"] == "Test Resto"
    assert resto_menu["familles"] == []
    assert resto_menu["boissons"] == []

def test_get_public_menu_display_populated(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    famille_id = uuid4()
    boisson_famille_id = uuid4()
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
        imageUrl="https://res.cloudinary.com/demo/image/upload/img1.png",
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

    boisson_famille_img = MenuBoissonImage(
        id=uuid4(),
        menuBoissonFamilleId=boisson_famille_id,
        url="https://res.cloudinary.com/demo/image/upload/boisson_famille_1.png",
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    menu_boisson_obj = MenuBoisson(
        id=uuid4(),
        menuBoissonFamilleId=boisson_famille_id,
        boissonId=boisson_id,
        boisson=boisson_obj,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    boisson_famille_obj = MenuBoissonFamille(
        id=boisson_famille_id,
        restaurantId=restaurant_id,
        nom="Nos boissons en bouteille",
        images=[boisson_famille_img],
        boissons=[menu_boisson_obj],
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    app.dependency_overrides[get_session] = lambda: db_mock

    queries = [
        MockQuery([restaurant_obj]),
        MockQuery([famille_obj]),
        MockQuery([boisson_famille_obj])
    ]
    db_mock.query.side_effect = lambda model: queries.pop(0)

    response = client.get("/menus/display")
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert "restaurants" in data
    assert len(data["restaurants"]) == 1
    resto_menu = data["restaurants"][0]
    assert resto_menu["restaurant"]["name"] == "Gourmet Heaven"
    assert len(resto_menu["familles"]) == 1
    assert resto_menu["familles"][0]["nom"] == "Plats principaux"
    assert resto_menu["familles"][0]["images"][0]["imageUrl"] == "https://res.cloudinary.com/demo/image/upload/img1.png"
    assert resto_menu["familles"][0]["categories"][0]["nom"] == MenuCategorieNom.SPECIALITE
    assert resto_menu["familles"][0]["categories"][0]["repasList"][0]["repas"]["nomRepas"] == "Burger Chef"

    # Verify drink family structure in display
    assert len(resto_menu["boissons"]) == 1
    assert resto_menu["boissons"][0]["nom"] == "Nos boissons en bouteille"
    assert resto_menu["boissons"][0]["images"][0]["url"] == "https://res.cloudinary.com/demo/image/upload/boisson_famille_1.png"
    assert resto_menu["boissons"][0]["boissons"][0]["nomBoisson"] == "Jus de Pomme"

def test_cloudinary_upload_endpoint(client):
    db_mock = MagicMock()
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com")
    restaurant_id = uuid4()
    famille_id = uuid4()

    famille_obj = MenuFamille(
        id=famille_id,
        restaurantId=restaurant_id,
        nom="Desserts",
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

    db_mock.add.side_effect = mock_add

    with patch("app.services.cloudinary_service.upload_image") as mock_upload:
        mock_upload.return_value = {
            "url": "https://res.cloudinary.com/dummy/image/upload/v12345678/gilexis/menu/sample.jpg",
            "public_id": "gilexis/menu/sample"
        }

        # 1. Test with non-existent famille_id -> should return 404 and NOT call Cloudinary
        db_mock.query.side_effect = lambda model: MockQuery([])
        files = {"file": ("sample.jpg", b"fake image content", "image/jpeg")}
        data_form = {"famille_id": str(uuid4()), "ordre": "1"}
        res_404 = client.post("/menus/upload", files=files, data=data_form)
        assert res_404.status_code == 404
        assert not mock_upload.called

        # 2. Test with valid famille_id -> calls Cloudinary and creates DB record
        db_mock.query.side_effect = lambda model: MockQuery(famille_obj)
        data_form = {"famille_id": str(famille_id), "ordre": "1"}
        response = client.post("/menus/upload", files=files, data=data_form)

        assert response.status_code == 201, response.text
        data = response.json()
        assert data["familleId"] == str(famille_id)
        assert data["imageUrl"] == "https://res.cloudinary.com/dummy/image/upload/v12345678/gilexis/menu/sample.jpg"
        assert data["ordre"] == 1
        assert data["public_id"] == "gilexis/menu/sample"

    app.dependency_overrides.clear()

def test_crud_menu_boisson_famille(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com")

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    def mock_add(obj):
        obj.id = uuid4()
        obj.restaurantId = restaurant_id
        obj.createdAt = datetime.now()
        obj.updatedAt = datetime.now()

    db_mock.add.side_effect = mock_add

    # Create Boisson Famille
    payload = {"nom": "Nos boissons importées"}
    response = client.post("/menus/boissons/familles", json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["nom"] == "Nos boissons importées"

    # List Boisson Familles
    famille_obj = MenuBoissonFamille(
        id=uuid4(),
        restaurantId=restaurant_id,
        nom="Nos boissons importées",
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )
    db_mock.query.side_effect = lambda model: MockQuery([famille_obj])

    response = client.get("/menus/boissons/familles")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["nom"] == "Nos boissons importées"

    # Get Boisson Famille Detail
    db_mock.query.side_effect = lambda model: MockQuery(famille_obj)
    res_get = client.get(f"/menus/boissons/familles/{famille_obj.id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == str(famille_obj.id)

    # Patch Boisson Famille
    db_mock.query.side_effect = lambda model: MockQuery(famille_obj)
    res_patch = client.patch(f"/menus/boissons/familles/{famille_obj.id}", json={"nom": "Liqueurs"})
    assert res_patch.status_code == 200
    assert famille_obj.nom == "Liqueurs"

    # Delete Boisson Famille
    db_mock.query.side_effect = lambda model: MockQuery(famille_obj)
    res_del = client.delete(f"/menus/boissons/familles/{famille_obj.id}")
    assert res_del.status_code == 204

    app.dependency_overrides.clear()

def test_boisson_famille_images_limit_and_deletion(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    famille_id = uuid4()
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com")

    famille_obj = MenuBoissonFamille(
        id=famille_id,
        restaurantId=restaurant_id,
        nom="Nos liqueurs",
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

    with patch("app.services.cloudinary_service.upload_image") as mock_upload, \
         patch("app.services.cloudinary_service.delete_image") as mock_delete, \
         patch("app.services.cloudinary_service.extract_public_id_from_url") as mock_extract:

        mock_upload.return_value = {
            "url": "https://res.cloudinary.com/demo/image/upload/v123/img.jpg",
            "public_id": "gilexis/menu/img"
        }
        mock_extract.return_value = "gilexis/menu/img"

        # 1. Upload when count < 3 -> Success
        queries_1 = [
            MockQuery(famille_obj), # get_menu_boisson_famille
            MockQuery([], count_value=2) # image count = 2
        ]
        db_mock.query.side_effect = lambda model: queries_1.pop(0)

        files = {"file": ("img.jpg", b"fake content", "image/jpeg")}
        res_upload = client.post(f"/menus/boissons/familles/{famille_id}/images", files=files)
        assert res_upload.status_code == 201, res_upload.text
        assert res_upload.json()["url"] == "https://res.cloudinary.com/demo/image/upload/v123/img.jpg"

        # 2. Upload when count == 3 -> 400 Bad Request (Limit reached)
        queries_2 = [
            MockQuery(famille_obj),
            MockQuery([], count_value=3)
        ]
        db_mock.query.side_effect = lambda model: queries_2.pop(0)

        res_limit = client.post(f"/menus/boissons/familles/{famille_id}/images", files=files)
        assert res_limit.status_code == 400
        assert "3 images maximum" in res_limit.json()["detail"]

        # 3. Delete image
        img_id = uuid4()
        img_obj = MenuBoissonImage(
            id=img_id,
            menuBoissonFamilleId=famille_id,
            url="https://res.cloudinary.com/demo/image/upload/v123/img.jpg"
        )
        db_mock.query.side_effect = lambda model: MockQuery(img_obj)
        res_del_img = client.delete(f"/menus/boissons/images/{img_id}")
        assert res_del_img.status_code == 204
        mock_delete.assert_called_once_with("gilexis/menu/img")

    app.dependency_overrides.clear()

def test_crud_menu_boisson_association(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    famille_id = uuid4()
    boisson_id = uuid4()
    mb_id = uuid4()
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com")

    famille_obj = MenuBoissonFamille(
        id=famille_id,
        restaurantId=restaurant_id,
        nom="Boissons en bouteille",
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    boisson_obj = Boisson(
        id=boisson_id,
        restaurantId=restaurant_id,
        nomBoisson="Coca",
        contenance=BoissonContenance.CL33,
        prixVente=500.0,
        stock=20,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    mb_obj = MenuBoisson(
        id=mb_id,
        menuBoissonFamilleId=famille_id,
        boissonId=boisson_id,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    def mock_add(obj):
        obj.id = mb_id
        obj.createdAt = datetime.now()
        obj.updatedAt = datetime.now()

    db_mock.add.side_effect = mock_add

    # 1. Create MenuBoisson association
    queries_create = [
        MockQuery(famille_obj), # get_menu_boisson_famille
        MockQuery(boisson_obj) # Boisson query
    ]
    db_mock.query.side_effect = lambda model: queries_create.pop(0)

    payload = {
        "menuBoissonFamilleId": str(famille_id),
        "boissonId": str(boisson_id)
    }
    res_create = client.post("/menus/boissons", json=payload)
    assert res_create.status_code == 201, res_create.text
    data = res_create.json()
    assert data["menuBoissonFamilleId"] == str(famille_id)
    assert data["boissonId"] == str(boisson_id)
    assert "ordre" not in data
    assert "imageUrl" not in data

    # 2. Delete MenuBoisson association
    db_mock.query.side_effect = lambda model: MockQuery(mb_obj)
    res_del = client.delete(f"/menus/boissons/{mb_id}")
    assert res_del.status_code == 204

    app.dependency_overrides.clear()

def test_multi_tenant_isolation_boissons(client):
    db_mock = MagicMock()
    restaurant_a_id = uuid4()
    restaurant_b_id = uuid4()
    famille_b_id = uuid4()
    boisson_a_id = uuid4()
    admin_user = User(id=uuid4(), name="Admin A", email="admina@test.com")

    # Family belongs to Restaurant B
    famille_b_obj = MenuBoissonFamille(
        id=famille_b_id,
        restaurantId=restaurant_b_id,
        nom="Famille Resto B"
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_a_id

    # Admin A tries to add drink to Famille B -> get_menu_boisson_famille returns None
    db_mock.query.side_effect = lambda model: MockQuery([])

    payload = {
        "menuBoissonFamilleId": str(famille_b_id),
        "boissonId": str(boisson_a_id)
    }
    response = client.post("/menus/boissons", json=payload)
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Famille de boissons non trouvée pour ce restaurant"
