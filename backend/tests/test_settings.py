def test_get_settings_returns_defaults_when_none_configured(client):
    response = client.get("/settings")
    assert response.status_code == 200
    body = response.json()
    assert body["store_name"] == "JG Parfums"
    assert body["accent_color"] == "#D3AE6A"
    assert body["font_pairing"] == "classic"
    assert body["shipping_cost"] == 0


def test_update_settings_requires_admin(client):
    response = client.put("/settings", json={"store_name": "Otra tienda"})
    assert response.status_code == 401


def test_update_settings_persists_partial_changes(client, admin_headers):
    update = client.put(
        "/settings",
        json={"store_name": "JG Perfumería", "accent_color": "#3F5D73", "whatsapp_number": "573001234567"},
        headers=admin_headers,
    )
    assert update.status_code == 200
    body = update.json()
    assert body["store_name"] == "JG Perfumería"
    assert body["accent_color"] == "#3F5D73"
    assert body["whatsapp_number"] == "573001234567"
    # No enviado en el PUT: debe seguir en su default, no borrarse.
    assert body["font_pairing"] == "classic"

    fetched = client.get("/settings").json()
    assert fetched["store_name"] == "JG Perfumería"


def test_update_settings_rejects_invalid_color(client, admin_headers):
    response = client.put("/settings", json={"accent_color": "not-a-color"}, headers=admin_headers)
    assert response.status_code == 422


def test_update_settings_rejects_negative_shipping_cost(client, admin_headers):
    response = client.put("/settings", json={"shipping_cost": -100}, headers=admin_headers)
    assert response.status_code == 422
