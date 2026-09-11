def _create_product(client, admin_headers, price=350000):
    payload = {
        "slug": "oud-royal", "name": "Oud Royal", "description": "Amaderado oriental.",
        "size_ml": 100, "price": price, "stock": 10,
    }
    return client.post("/products", json=payload, headers=admin_headers).json()


def _checkout_payload(product_id, quantity=1):
    return {
        "guest_email": "comprador@example.com", "guest_name": "Comprador Test", "guest_phone": "3001234567",
        "shipping_address": "Calle 1 # 2-3", "shipping_city": "Bogotá",
        "items": [{"product_id": product_id, "quantity": quantity}],
    }


def test_track_page_view_is_public_and_returns_204(client):
    response = client.post("/stats/track", json={"path": "/index.html"})
    assert response.status_code == 204


def test_summary_requires_admin(client):
    response = client.get("/stats/summary")
    assert response.status_code == 401


def test_summary_counts_views_and_orders(client, admin_headers):
    client.post("/stats/track", json={"path": "/index.html"})
    client.post("/stats/track", json={"path": "/index.html"})
    client.post("/stats/track", json={"path": "/catalogo.html"})

    product = _create_product(client, admin_headers)
    client.post("/orders", json=_checkout_payload(product["id"], quantity=2))

    summary = client.get("/stats/summary", headers=admin_headers)
    assert summary.status_code == 200
    body = summary.json()

    assert body["views_7d"] == 3
    assert body["views_30d"] == 3
    top_paths = {p["path"]: p["count"] for p in body["top_pages"]}
    assert top_paths["/index.html"] == 2
    assert top_paths["/catalogo.html"] == 1

    assert body["total_orders"] == 1
    assert body["orders_by_status"]["pending"] == 1
    assert body["top_products"][0]["name"] == "Oud Royal"
    assert body["top_products"][0]["quantity"] == 2
    # el pedido queda "pending" (sin webhook de pago simulado), así que el
    # ingreso aprobado todavía es 0 — total_revenue solo cuenta pagos aprobados.
    assert body["total_revenue"] == 0
