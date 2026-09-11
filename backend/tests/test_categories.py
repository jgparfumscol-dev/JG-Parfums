def test_create_and_list_categories(client, admin_headers):
    create = client.post("/categories", json={"name": "Amaderado", "slug": "amaderado"}, headers=admin_headers)
    assert create.status_code == 201

    listing = client.get("/categories")
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["slug"] == "amaderado"


def test_create_category_requires_admin(client):
    response = client.post("/categories", json={"name": "Amaderado", "slug": "amaderado"})
    assert response.status_code == 401


def test_create_category_rejects_duplicate_slug(client, admin_headers):
    client.post("/categories", json={"name": "Amaderado", "slug": "amaderado"}, headers=admin_headers)
    duplicate = client.post("/categories", json={"name": "Otro nombre", "slug": "amaderado"}, headers=admin_headers)
    assert duplicate.status_code == 400


def test_update_and_delete_category(client, admin_headers):
    category = client.post("/categories", json={"name": "Floral", "slug": "floral"}, headers=admin_headers).json()

    update = client.put(f"/categories/{category['id']}", json={"name": "Floral fresco"}, headers=admin_headers)
    assert update.status_code == 200
    assert update.json()["name"] == "Floral fresco"

    delete = client.delete(f"/categories/{category['id']}", headers=admin_headers)
    assert delete.status_code == 204
    assert client.get("/categories").json() == []


def test_product_category_assignment_and_filter(client, admin_headers):
    category = client.post("/categories", json={"name": "Cítrico", "slug": "citrico"}, headers=admin_headers).json()

    with_category = client.post(
        "/products",
        json={
            "slug": "citrico-manana", "name": "Cítrico Mañana", "description": "Fresco.",
            "category_id": category["id"], "size_ml": 100, "price": 180000, "stock": 5,
        },
        headers=admin_headers,
    )
    assert with_category.status_code == 201
    assert with_category.json()["category"]["slug"] == "citrico"

    client.post(
        "/products",
        json={"slug": "sin-categoria", "name": "Sin Categoría", "description": "N/A.", "size_ml": 100, "price": 100000, "stock": 1},
        headers=admin_headers,
    )

    filtered = client.get(f"/products?category_id={category['id']}")
    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["slug"] == "citrico-manana"


def test_deleting_category_unsets_it_on_products_instead_of_deleting_them(client, admin_headers):
    category = client.post("/categories", json={"name": "Oriental", "slug": "oriental"}, headers=admin_headers).json()
    product = client.post(
        "/products",
        json={
            "slug": "ambar-nocturno", "name": "Ámbar Nocturno", "description": "Oriental.",
            "category_id": category["id"], "size_ml": 100, "price": 200000, "stock": 3,
        },
        headers=admin_headers,
    ).json()

    client.delete(f"/categories/{category['id']}", headers=admin_headers)

    updated = client.get("/products/ambar-nocturno")
    assert updated.status_code == 200
    assert updated.json()["category"] is None
