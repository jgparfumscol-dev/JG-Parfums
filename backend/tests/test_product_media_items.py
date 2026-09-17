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


def test_admin_can_add_media_item_and_it_appears_on_product(client, admin_headers):
    product = _create_product(client, admin_headers)

    response = client.post(
        f"/products/{product['id']}/media",
        json={
            "url": "https://cdn.example.com/oud.gif",
            "alt_text": "Botella girando",
            "title": "Elegancia atemporal",
            "text_position": "center",
            "text_position_vertical": "bottom",
            "overlay_opacity": 40,
            "blur": 5,
            "height_px": 520,
            "width_pct": 80,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["position"] == 0
    assert body["overlay_opacity"] == 40

    detail = client.get("/products/oud-royal").json()
    assert len(detail["media_items"]) == 1
    assert detail["media_items"][0]["url"] == "https://cdn.example.com/oud.gif"


def test_add_media_item_defaults(client, admin_headers):
    product = _create_product(client, admin_headers)
    response = client.post(
        f"/products/{product['id']}/media",
        json={"url": "https://cdn.example.com/oud.jpg"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["text_position"] == "left"
    assert body["text_position_vertical"] == "bottom"
    assert body["overlay_opacity"] == 0
    assert body["blur"] == 0
    assert body["height_px"] == 480
    assert body["width_pct"] == 100


def test_add_media_item_requires_admin(client, admin_headers):
    product = _create_product(client, admin_headers)
    response = client.post(f"/products/{product['id']}/media", json={"url": "https://cdn.example.com/oud.jpg"})
    assert response.status_code == 401


def test_add_media_item_rejects_out_of_range_values(client, admin_headers):
    product = _create_product(client, admin_headers)
    response = client.post(
        f"/products/{product['id']}/media",
        json={"url": "https://cdn.example.com/oud.jpg", "overlay_opacity": 150},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_update_media_item(client, admin_headers):
    product = _create_product(client, admin_headers)
    item = client.post(
        f"/products/{product['id']}/media",
        json={"url": "https://cdn.example.com/oud.jpg"},
        headers=admin_headers,
    ).json()

    update = client.put(
        f"/products/media/{item['id']}", json={"blur": 12, "width_pct": 60}, headers=admin_headers
    )
    assert update.status_code == 200
    assert update.json()["blur"] == 12
    assert update.json()["width_pct"] == 60


def test_move_media_item_swaps_position_with_neighbor(client, admin_headers):
    product = _create_product(client, admin_headers)
    first = client.post(
        f"/products/{product['id']}/media",
        json={"url": "https://cdn.example.com/a.jpg"},
        headers=admin_headers,
    ).json()
    second = client.post(
        f"/products/{product['id']}/media",
        json={"url": "https://cdn.example.com/b.jpg"},
        headers=admin_headers,
    ).json()

    moved = client.put(f"/products/media/{second['id']}/move", json={"direction": "up"}, headers=admin_headers)
    assert moved.status_code == 200
    assert moved.json()["position"] == 0

    detail = client.get("/products/oud-royal").json()
    assert detail["media_items"][0]["id"] == second["id"]
    assert detail["media_items"][1]["id"] == first["id"]


def test_delete_media_item(client, admin_headers):
    product = _create_product(client, admin_headers)
    item = client.post(
        f"/products/{product['id']}/media",
        json={"url": "https://cdn.example.com/a.jpg"},
        headers=admin_headers,
    ).json()

    delete = client.delete(f"/products/media/{item['id']}", headers=admin_headers)
    assert delete.status_code == 204
    assert client.get("/products/oud-royal").json()["media_items"] == []
