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


def test_admin_can_add_note_and_it_appears_on_product(client, admin_headers):
    product = _create_product(client, admin_headers)

    response = client.post(
        f"/products/{product['id']}/notes",
        json={"name": "Bergamota", "color": "#E3CCA1"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    assert response.json()["position"] == 0

    detail = client.get("/products/oud-royal").json()
    assert len(detail["notes"]) == 1
    assert detail["notes"][0]["name"] == "Bergamota"
    assert detail["notes"][0]["color"] == "#E3CCA1"


def test_add_note_requires_admin(client, admin_headers):
    product = _create_product(client, admin_headers)
    response = client.post(f"/products/{product['id']}/notes", json={"name": "Bergamota", "color": "#E3CCA1"})
    assert response.status_code == 401


def test_add_note_rejects_invalid_color(client, admin_headers):
    product = _create_product(client, admin_headers)
    response = client.post(
        f"/products/{product['id']}/notes",
        json={"name": "Bergamota", "color": "not-a-color"},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_update_note(client, admin_headers):
    product = _create_product(client, admin_headers)
    note = client.post(
        f"/products/{product['id']}/notes", json={"name": "Bergamota", "color": "#E3CCA1"}, headers=admin_headers
    ).json()

    update = client.put(f"/products/notes/{note['id']}", json={"name": "Oud"}, headers=admin_headers)
    assert update.status_code == 200
    assert update.json()["name"] == "Oud"
    assert update.json()["color"] == "#E3CCA1"


def test_move_note_swaps_position_with_neighbor(client, admin_headers):
    product = _create_product(client, admin_headers)
    first = client.post(
        f"/products/{product['id']}/notes", json={"name": "Bergamota", "color": "#E3CCA1"}, headers=admin_headers
    ).json()
    second = client.post(
        f"/products/{product['id']}/notes", json={"name": "Oud", "color": "#6A501F"}, headers=admin_headers
    ).json()
    assert first["position"] == 0
    assert second["position"] == 1

    moved = client.put(f"/products/notes/{second['id']}/move", json={"direction": "up"}, headers=admin_headers)
    assert moved.status_code == 200
    assert moved.json()["position"] == 0

    detail = client.get("/products/oud-royal").json()
    assert detail["notes"][0]["id"] == second["id"]
    assert detail["notes"][1]["id"] == first["id"]


def test_delete_note(client, admin_headers):
    product = _create_product(client, admin_headers)
    note = client.post(
        f"/products/{product['id']}/notes", json={"name": "Bergamota", "color": "#E3CCA1"}, headers=admin_headers
    ).json()

    delete = client.delete(f"/products/notes/{note['id']}", headers=admin_headers)
    assert delete.status_code == 204
    assert client.get("/products/oud-royal").json()["notes"] == []
