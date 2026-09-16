def test_create_and_list_brand(client, admin_headers):
    create = client.post(
        "/brands", json={"name": "Casa Norte", "logo_url": "https://cdn.jg/casa-norte.svg"}, headers=admin_headers
    )
    assert create.status_code == 201
    body = create.json()
    assert body["name"] == "Casa Norte"
    assert body["link_url"] is None
    assert body["is_active"] is True
    assert body["sort_order"] == 0

    listing = client.get("/brands")
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_create_brand_requires_admin(client):
    response = client.post("/brands", json={"name": "Casa Norte", "logo_url": "https://cdn.jg/logo.svg"})
    assert response.status_code == 401


def test_create_brand_accepts_relative_and_https_link(client, admin_headers):
    relative = client.post(
        "/brands",
        json={"name": "A", "logo_url": "https://cdn.jg/a.svg", "link_url": "/catalogo.html"},
        headers=admin_headers,
    )
    assert relative.status_code == 201
    https = client.post(
        "/brands",
        json={"name": "B", "logo_url": "https://cdn.jg/b.svg", "link_url": "https://casa-norte.com"},
        headers=admin_headers,
    )
    assert https.status_code == 201


def test_create_brand_rejects_bare_domain_without_scheme(client, admin_headers):
    response = client.post(
        "/brands", json={"name": "A", "logo_url": "https://cdn.jg/a.svg", "link_url": "casa-norte.com"},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_update_and_delete_brand(client, admin_headers):
    brand = client.post("/brands", json={"name": "Casa Norte", "logo_url": "https://cdn.jg/a.svg"}, headers=admin_headers).json()

    update = client.put(f"/brands/{brand['id']}", json={"name": "Casa Sur", "is_active": False}, headers=admin_headers)
    assert update.status_code == 200
    assert update.json()["name"] == "Casa Sur"
    assert update.json()["is_active"] is False

    delete = client.delete(f"/brands/{brand['id']}", headers=admin_headers)
    assert delete.status_code == 204
    assert client.get("/brands?include_inactive=true", headers=admin_headers).json() == []


def test_public_endpoint_excludes_inactive_and_orders_by_sort_order(client, admin_headers):
    a = client.post("/brands", json={"name": "A", "logo_url": "https://cdn.jg/a.svg"}, headers=admin_headers).json()
    b = client.post("/brands", json={"name": "B", "logo_url": "https://cdn.jg/b.svg"}, headers=admin_headers).json()
    client.put(f"/brands/{a['id']}", json={"is_active": False}, headers=admin_headers)

    public = client.get("/brands")
    assert public.status_code == 200
    assert [item["id"] for item in public.json()] == [b["id"]]


def test_include_inactive_requires_admin(client, admin_headers):
    client.post("/brands", json={"name": "A", "logo_url": "https://cdn.jg/a.svg"}, headers=admin_headers)
    response = client.get("/brands?include_inactive=true")
    # Sin admin, include_inactive se ignora — sigue devolviendo solo activas, no 401.
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_move_brand_swaps_sort_order_with_neighbor(client, admin_headers):
    a = client.post("/brands", json={"name": "A", "logo_url": "https://cdn.jg/a.svg"}, headers=admin_headers).json()
    b = client.post("/brands", json={"name": "B", "logo_url": "https://cdn.jg/b.svg"}, headers=admin_headers).json()
    assert [item["name"] for item in client.get("/brands").json()] == ["A", "B"]

    move = client.put(f"/brands/{b['id']}/move", json={"direction": "up"}, headers=admin_headers)
    assert move.status_code == 200
    assert [item["name"] for item in client.get("/brands").json()] == ["B", "A"]
