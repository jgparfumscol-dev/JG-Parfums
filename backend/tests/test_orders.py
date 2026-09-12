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


def _checkout_payload(product_id, quantity=1):
    return {
        "guest_email": "comprador@example.com",
        "guest_name": "Comprador Test",
        "guest_phone": "3001234567",
        "shipping_address": "Calle 1 # 2-3",
        "shipping_city": "Bogotá",
        "items": [{"product_id": product_id, "quantity": quantity}],
    }


def test_create_order_decrements_stock(client, admin_headers):
    product = _create_product(client, admin_headers, stock=5)

    response = client.post("/orders", json=_checkout_payload(product["id"], quantity=2))
    assert response.status_code == 201
    body = response.json()
    assert body["total"] == 700000
    assert body["status"] == "pending"

    updated_product = client.get("/products/oud-royal").json()
    assert updated_product["stock"] == 3


def test_create_order_includes_configured_shipping_cost(client, admin_headers):
    client.put("/settings", json={"shipping_cost": 15000}, headers=admin_headers)
    product = _create_product(client, admin_headers, stock=5, price=100000)

    response = client.post("/orders", json=_checkout_payload(product["id"], quantity=1))
    assert response.status_code == 201
    body = response.json()
    assert body["subtotal"] == 100000
    assert body["shipping_cost"] == 15000
    assert body["total"] == 115000


def test_create_order_insufficient_stock_rejected(client, admin_headers):
    product = _create_product(client, admin_headers, stock=1)

    response = client.post("/orders", json=_checkout_payload(product["id"], quantity=2))
    assert response.status_code == 400

    unchanged = client.get("/products/oud-royal").json()
    assert unchanged["stock"] == 1


def test_get_order_requires_matching_email_or_admin(client, admin_headers):
    product = _create_product(client, admin_headers)
    order = client.post("/orders", json=_checkout_payload(product["id"])).json()

    wrong_email = client.get(f"/orders/{order['order_number']}", params={"email": "otro@example.com"})
    assert wrong_email.status_code == 404

    right_email = client.get(f"/orders/{order['order_number']}", params={"email": "comprador@example.com"})
    assert right_email.status_code == 200

    as_admin = client.get(f"/orders/{order['order_number']}", headers=admin_headers)
    assert as_admin.status_code == 200


def test_admin_can_list_and_update_status(client, admin_headers):
    product = _create_product(client, admin_headers)
    order = client.post("/orders", json=_checkout_payload(product["id"])).json()

    listing = client.get("/orders", headers=admin_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    update = client.patch(f"/orders/{order['id']}/status", json={"status": "shipped"}, headers=admin_headers)
    assert update.status_code == 200
    assert update.json()["status"] == "shipped"


def test_list_orders_requires_admin(client, admin_headers):
    product = _create_product(client, admin_headers)
    client.post("/orders", json=_checkout_payload(product["id"]))

    response = client.get("/orders")
    assert response.status_code == 401
