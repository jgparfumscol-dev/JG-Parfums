def _create_product(client, admin_headers, **overrides):
    payload = {
        "slug": "oud-royal",
        "name": "Oud Royal",
        "description": "Amaderado oriental, para la noche.",
        "size_ml": 100,
        "price": 200000,
        "stock": 5,
        **overrides,
    }
    response = client.post("/products", json=payload, headers=admin_headers)
    assert response.status_code == 201, response.text
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


def test_product_without_discount_keeps_its_price(client, admin_headers):
    product = _create_product(client, admin_headers)
    assert product["discount_percent"] == 0
    assert product["final_price"] == 200000


def test_create_product_with_discount_exposes_final_price(client, admin_headers):
    product = _create_product(client, admin_headers, discount_percent=25)
    assert product["price"] == 200000
    assert product["final_price"] == 150000


def test_admin_can_set_and_clear_discount_on_existing_product(client, admin_headers):
    product = _create_product(client, admin_headers)

    updated = client.put(f"/products/{product['id']}", json={"discount_percent": 10}, headers=admin_headers)
    assert updated.status_code == 200
    assert updated.json()["final_price"] == 180000

    cleared = client.put(f"/products/{product['id']}", json={"discount_percent": 0}, headers=admin_headers)
    assert cleared.json()["final_price"] == 200000


def test_discount_percent_must_be_between_0_and_99(client, admin_headers):
    product = _create_product(client, admin_headers)
    for invalid in (-1, 100, 150):
        response = client.put(f"/products/{product['id']}", json={"discount_percent": invalid}, headers=admin_headers)
        assert response.status_code == 422


def test_discount_rounds_to_nearest_peso(client, admin_headers):
    product = _create_product(client, admin_headers, price=99999, discount_percent=33)
    assert product["final_price"] == 66999  # 99999 * 0.67 = 66999.33 -> 66999


def test_discount_applies_to_decants(client, admin_headers):
    product = _create_product(client, admin_headers, discount_percent=20)
    variant = client.post(
        f"/products/{product['id']}/variants",
        json={"size_ml": 5, "price": 50000, "stock": 10},
        headers=admin_headers,
    ).json()
    assert variant["price"] == 50000
    assert variant["final_price"] == 40000

    fetched = client.get("/products/oud-royal").json()
    assert fetched["variants"][0]["final_price"] == 40000


def test_order_charges_discounted_price(client, admin_headers):
    product = _create_product(client, admin_headers, discount_percent=25)

    response = client.post("/orders", json=_checkout_payload(product["id"], quantity=2))
    assert response.status_code == 201
    body = response.json()
    assert body["items"][0]["unit_price"] == 150000
    assert body["subtotal"] == 300000


def test_order_charges_discounted_decant_price(client, admin_headers):
    product = _create_product(client, admin_headers, discount_percent=20)
    variant = client.post(
        f"/products/{product['id']}/variants",
        json={"size_ml": 5, "price": 50000, "stock": 10},
        headers=admin_headers,
    ).json()

    response = client.post("/orders", json=_checkout_payload(product["id"], variant["id"], quantity=3))
    assert response.status_code == 201
    body = response.json()
    assert body["items"][0]["unit_price"] == 40000
    assert body["subtotal"] == 120000


def test_price_filter_uses_discounted_price(client, admin_headers):
    _create_product(client, admin_headers, slug="con-descuento", price=200000, discount_percent=50)
    _create_product(client, admin_headers, slug="sin-descuento", price=150000)

    # 100.000 con descuento vs 150.000 sin él
    cheap = client.get("/products?max_price=120000").json()
    assert [p["slug"] for p in cheap["items"]] == ["con-descuento"]
