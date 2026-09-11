def _create_product(client, admin_headers, stock=5, price=350000):
    payload = {
        "slug": "oud-royal",
        "name": "Oud Royal",
        "description": "Amaderado oriental, para la noche.",
        "size_ml": 100,
        "price": price,
        "stock": stock,
    }
    response = client.post("/products", json=payload, headers=admin_headers)
    return response.json()


def _checkout_payload(product_id, variant_id=None, quantity=1):
    return {
        "guest_email": "comprador@example.com",
        "guest_name": "Comprador Test",
        "guest_phone": "3001234567",
        "shipping_address": "Calle 1 # 2-3",
        "shipping_city": "Bogotá",
        "items": [{"product_id": product_id, "variant_id": variant_id, "quantity": quantity}],
    }


def test_admin_can_add_variant_and_it_appears_on_product(client, admin_headers):
    product = _create_product(client, admin_headers)

    response = client.post(
        f"/products/{product['id']}/variants",
        json={"size_ml": 5, "price": 45000, "stock": 10},
        headers=admin_headers,
    )
    assert response.status_code == 201
    assert response.json()["size_ml"] == 5

    detail = client.get("/products/oud-royal").json()
    assert len(detail["variants"]) == 1
    assert detail["variants"][0]["price"] == 45000


def test_adding_variant_requires_admin(client, admin_headers):
    product = _create_product(client, admin_headers)
    response = client.post(f"/products/{product['id']}/variants", json={"size_ml": 5, "price": 45000})
    assert response.status_code == 401


def test_admin_can_update_and_delete_variant(client, admin_headers):
    product = _create_product(client, admin_headers)
    variant = client.post(
        f"/products/{product['id']}/variants",
        json={"size_ml": 10, "price": 80000, "stock": 5},
        headers=admin_headers,
    ).json()

    update = client.put(
        f"/products/variants/{variant['id']}", json={"price": 90000}, headers=admin_headers
    )
    assert update.status_code == 200
    assert update.json()["price"] == 90000

    delete = client.delete(f"/products/variants/{variant['id']}", headers=admin_headers)
    assert delete.status_code == 204

    detail = client.get("/products/oud-royal").json()
    assert detail["variants"] == []


def test_buying_decant_decrements_variant_stock_not_bottle_stock(client, admin_headers):
    product = _create_product(client, admin_headers, stock=5)
    variant = client.post(
        f"/products/{product['id']}/variants",
        json={"size_ml": 5, "price": 45000, "stock": 3},
        headers=admin_headers,
    ).json()

    response = client.post("/orders", json=_checkout_payload(product["id"], variant["id"], quantity=2))
    assert response.status_code == 201
    body = response.json()
    assert body["total"] == 90000
    item = body["items"][0]
    assert item["size_ml"] == 5
    assert item["product_variant_id"] == variant["id"]
    assert "decant" in item["product_name"].lower()

    unchanged_bottle = client.get("/products/oud-royal").json()
    assert unchanged_bottle["stock"] == 5  # el frasco completo no se toca
    assert unchanged_bottle["variants"][0]["stock"] == 1  # 3 - 2


def test_has_decant_filter_only_returns_products_with_active_variant(client, admin_headers):
    with_decant = _create_product(client, admin_headers)
    client.post(
        f"/products/{with_decant['id']}/variants",
        json={"size_ml": 5, "price": 45000, "stock": 10},
        headers=admin_headers,
    )
    client.post(
        "/products",
        json={
            "slug": "sin-decant",
            "name": "Sin Decant",
            "description": "Solo frasco completo.",
            "size_ml": 100,
            "price": 200000,
            "stock": 3,
        },
        headers=admin_headers,
    )

    response = client.get("/products?has_decant=true")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["slug"] == "oud-royal"

    unfiltered = client.get("/products").json()
    assert unfiltered["total"] == 2


def test_buying_decant_with_insufficient_variant_stock_rejected(client, admin_headers):
    product = _create_product(client, admin_headers, stock=5)
    variant = client.post(
        f"/products/{product['id']}/variants",
        json={"size_ml": 10, "price": 80000, "stock": 1},
        headers=admin_headers,
    ).json()

    response = client.post("/orders", json=_checkout_payload(product["id"], variant["id"], quantity=2))
    assert response.status_code == 400

    unchanged = client.get("/products/oud-royal").json()
    assert unchanged["variants"][0]["stock"] == 1
