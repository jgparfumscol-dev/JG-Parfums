def _product_payload(slug="oud-royal"):
    return {
        "slug": slug,
        "name": "Oud Royal",
        "house": "Casa Ejemplo",
        "description": "Amaderado oriental, para la noche.",
        "olfactory_family": "amaderado",
        "concentration": "EDP",
        "size_ml": 100,
        "price": 350000,
        "stock": 10,
    }


def test_create_and_list_product(client, admin_headers):
    create = client.post("/products", json=_product_payload(), headers=admin_headers)
    assert create.status_code == 201

    listing = client.get("/products")
    assert listing.status_code == 200
    body = listing.json()
    assert body["total"] == 1
    assert body["items"][0]["slug"] == "oud-royal"


def test_create_product_requires_admin(client):
    response = client.post("/products", json=_product_payload())
    assert response.status_code == 401


def test_get_product_by_slug_not_found(client):
    response = client.get("/products/no-existe")
    assert response.status_code == 404


def test_inactive_product_not_listed(client, admin_headers):
    client.post("/products", json=_product_payload(), headers=admin_headers)
    product = client.get("/products/oud-royal").json()

    client.delete(f"/products/{product['id']}", headers=admin_headers)

    listing = client.get("/products")
    assert listing.json()["total"] == 0
    assert client.get("/products/oud-royal").status_code == 404


def test_include_inactive_requires_admin(client, admin_headers):
    client.post("/products", json=_product_payload(), headers=admin_headers)
    product = client.get("/products/oud-royal").json()
    client.delete(f"/products/{product['id']}", headers=admin_headers)

    as_guest = client.get("/products?include_inactive=true")
    assert as_guest.json()["total"] == 0

    as_admin = client.get("/products?include_inactive=true", headers=admin_headers)
    assert as_admin.json()["total"] == 1
    assert as_admin.json()["items"][0]["is_active"] is False


def test_update_product_partial(client, admin_headers):
    client.post("/products", json=_product_payload(), headers=admin_headers)
    product = client.get("/products/oud-royal").json()

    response = client.put(f"/products/{product['id']}", json={"price": 400000}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["price"] == 400000
    assert response.json()["name"] == "Oud Royal"
