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


def test_create_category_with_class_card_fields_and_defaults(client, admin_headers):
    create = client.post(
        "/categories",
        json={
            "name": "Amaderado", "slug": "amaderado", "image_url": "https://cdn.jg/amaderado.jpg",
            "eyebrow": "Perfumes", "display_name": "Amaderados", "overlay_darkness": 55, "text_position": "center",
        },
        headers=admin_headers,
    )
    assert create.status_code == 201
    body = create.json()
    assert body["image_url"] == "https://cdn.jg/amaderado.jpg"
    assert body["eyebrow"] == "Perfumes"
    assert body["display_name"] == "Amaderados"
    assert body["overlay_darkness"] == 55
    assert body["text_position"] == "center"
    assert body["is_active"] is True
    assert body["sort_order"] == 0

    defaults = client.post("/categories", json={"name": "Floral", "slug": "floral"}, headers=admin_headers).json()
    assert defaults["overlay_darkness"] == 40
    assert defaults["text_position"] == "left"
    assert defaults["image_url"] is None
    assert defaults["sort_order"] == 1


def test_create_category_rejects_overlay_darkness_out_of_range(client, admin_headers):
    response = client.post(
        "/categories", json={"name": "Cítrico", "slug": "citrico", "overlay_darkness": 101}, headers=admin_headers
    )
    assert response.status_code == 422


def test_create_category_rejects_invalid_text_position(client, admin_headers):
    response = client.post(
        "/categories", json={"name": "Cítrico", "slug": "citrico", "text_position": "top"}, headers=admin_headers
    )
    assert response.status_code == 422


def test_update_category_can_toggle_is_active(client, admin_headers):
    category = client.post("/categories", json={"name": "Oriental", "slug": "oriental"}, headers=admin_headers).json()
    update = client.put(f"/categories/{category['id']}", json={"is_active": False}, headers=admin_headers)
    assert update.status_code == 200
    assert update.json()["is_active"] is False


def test_move_category_swaps_sort_order_with_neighbor(client, admin_headers):
    a = client.post("/categories", json={"name": "A", "slug": "a"}, headers=admin_headers).json()
    b = client.post("/categories", json={"name": "B", "slug": "b"}, headers=admin_headers).json()
    c = client.post("/categories", json={"name": "C", "slug": "c"}, headers=admin_headers).json()
    assert [cat["slug"] for cat in client.get("/categories").json()] == ["a", "b", "c"]

    move = client.put(f"/categories/{b['id']}/move", json={"direction": "up"}, headers=admin_headers)
    assert move.status_code == 200
    assert [cat["slug"] for cat in client.get("/categories").json()] == ["b", "a", "c"]

    # En el extremo, moverse más allá no rompe nada — se queda quieto.
    edge = client.put(f"/categories/{b['id']}/move", json={"direction": "up"}, headers=admin_headers)
    assert edge.status_code == 200
    assert [cat["slug"] for cat in client.get("/categories").json()] == ["b", "a", "c"]


def test_move_category_requires_admin(client, admin_headers):
    category = client.post("/categories", json={"name": "A", "slug": "a"}, headers=admin_headers).json()
    response = client.put(f"/categories/{category['id']}/move", json={"direction": "up"})
    assert response.status_code == 401


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
