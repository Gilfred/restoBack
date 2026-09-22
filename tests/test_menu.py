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

    def outerjoin(self, *args, **kwargs):
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

    # 1st query: Restaurant list, 2nd query: MenuFamilles, 3rd query: MenuBoissons
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

    menu_boisson_obj = MenuBoisson(
        id=uuid4(),
        boissonId=boisson_id,
        ordre=1,
        imageUrl="https://res.cloudinary.com/demo/image/upload/boisson1.png",
        boisson=boisson_obj,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    app.dependency_overrides[get_session] = lambda: db_mock

    queries = [
        MockQuery([restaurant_obj]),
        MockQuery([famille_obj]),
        MockQuery([menu_boisson_obj])
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
    assert resto_menu["boissons"][0]["boisson"]["nomBoisson"] == "Jus de Pomme"

from unittest.mock import patch

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

def test_menu_famille_image_update_and_delete(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    famille_id = uuid4()
    image_id = uuid4()
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com")

    famille_img = MenuFamilleImage(
        id=image_id,
        familleId=famille_id,
        imageUrl="https://res.cloudinary.com/demo/image/upload/v12345/gilexis/menu/old_image.jpg",
        ordre=1
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    db_mock.query.side_effect = lambda model: MockQuery(famille_img)

    with patch("app.services.cloudinary_service.upload_image") as mock_upload, \
         patch("app.services.cloudinary_service.delete_image") as mock_delete:
        mock_upload.return_value = {
            "url": "https://res.cloudinary.com/demo/image/upload/v67890/gilexis/menu/new_image.jpg",
            "public_id": "gilexis/menu/new_image"
        }

        files = {"file": ("new_image.webp", b"new image bytes", "image/webp")}
        data = {"ordre": "2"}
        response = client.patch(f"/menus/famille-images/{image_id}", files=files, data=data)

        assert response.status_code == 200, response.text
        res_json = response.json()
        assert res_json["ordre"] == 2
        assert res_json["imageUrl"] == "https://res.cloudinary.com/demo/image/upload/v67890/gilexis/menu/new_image.jpg"
        mock_upload.assert_called_once()
        mock_delete.assert_called_once_with("gilexis/menu/old_image")

    response_del = client.delete(f"/menus/famille-images/{image_id}")
    app.dependency_overrides.clear()
    assert response_del.status_code == 204

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

def test_authenticated_get_familles_uses_user_restaurant(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    famille_id = uuid4()
    user = User(id=uuid4(), name="User", email="user@test.com")

    famille_obj = MenuFamille(
        id=famille_id,
        restaurantId=restaurant_id,
        nom="User Resto Famille",
        ordre=1,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    db_mock.query.side_effect = lambda model: MockQuery([famille_obj])

    res_list = client.get("/menus/familles")
    assert res_list.status_code == 200, res_list.text
    assert len(res_list.json()) == 1
    assert res_list.json()[0]["nom"] == "User Resto Famille"

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

def test_categories_endpoints_admin_and_public(client):
    db_mock = MagicMock()
    restaurant_id = uuid4()
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com")
    cat_id = uuid4()
    famille_id = uuid4()

    famille_obj = MenuFamille(
        id=famille_id,
        restaurantId=restaurant_id,
        nom="Test Famille",
        ordre=1,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    cat_obj = MenuCategorie(
        id=cat_id,
        menuFamilleId=famille_id,
        nom=MenuCategorieNom.CLASSIQUE,
        ordre=1,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    def mock_add(obj):
        obj.id = cat_id
        obj.createdAt = datetime.now()
        obj.updatedAt = datetime.now()

    db_mock.add.side_effect = mock_add

    app.dependency_overrides[get_session] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_user_restaurant_id] = lambda: restaurant_id

    # 1. Admin creating category without menuFamilleId -> 400 Bad Request
    res_400 = client.post("/menus/categories", json={"nom": "classique"})
    assert res_400.status_code == 400

    # 2. Admin creating category with non-existent menuFamilleId -> 404 Not Found
    db_mock.query.side_effect = lambda model: MockQuery([])
    res_404 = client.post("/menus/categories", json={"nom": "classique", "menuFamilleId": str(uuid4())})
    assert res_404.status_code == 404

    # 3. Admin successfully creates category associated with family (201)
    db_mock.query.side_effect = lambda model: MockQuery(famille_obj)
    create_payload = {"nom": "classique", "menuFamilleId": str(famille_id), "ordre": 1}
    res_201 = client.post("/menus/categories", json=create_payload)
    assert res_201.status_code == 201, res_201.text
    data = res_201.json()
    assert data["nom"] == "classique"
    assert data["menuFamilleId"] == str(famille_id)

    # 4. GET categories list
    db_mock.query.side_effect = lambda model: MockQuery([cat_obj])
    res_list = client.get("/menus/categories")
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1
    assert res_list.json()[0]["id"] == str(cat_id)

    # 5. Admin can PATCH category
    db_mock.query.side_effect = lambda model: MockQuery(cat_obj)
    patch_payload = {"nom": "spécialité", "ordre": 2}
    res_patch = client.patch(f"/menus/categories/{cat_id}", json=patch_payload)
    assert res_patch.status_code == 200
    assert cat_obj.nom == MenuCategorieNom.SPECIALITE
    assert cat_obj.ordre == 2

    # 6. Admin can DELETE category (204)
    db_mock.query.side_effect = lambda model: MockQuery(cat_obj)
    res_del = client.delete(f"/menus/categories/{cat_id}")
    assert res_del.status_code == 204

    app.dependency_overrides.clear()

def test_list_categorie_noms_admin(client):
    admin_user = User(id=uuid4(), name="Admin", email="admin@test.com")
    app.dependency_overrides[require_admin] = lambda: admin_user

    response = client.get("/menus/categories/noms")
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert set(data) == {"classique", "spécialité", "premium"}

def test_list_categorie_noms_unauthorized(client):
    response = client.get("/menus/categories/noms")
    assert response.status_code in (401, 403)
