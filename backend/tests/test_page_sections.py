def test_create_and_list_page_section(client, admin_headers):
    create = client.post(
        "/page-sections",
        json={"page": "home", "type": "banner", "content": {"title": "Nuevo lanzamiento"}},
        headers=admin_headers,
    )
    assert create.status_code == 201
    assert create.json()["position"] == 0

    listing = client.get("/page-sections", params={"page": "home"})
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["content"]["title"] == "Nuevo lanzamiento"


def test_create_page_section_requires_admin(client):
    response = client.post("/page-sections", json={"page": "home", "type": "banner", "content": {}})
    assert response.status_code == 401


def test_inactive_section_hidden_from_public_but_visible_to_admin(client, admin_headers):
    section = client.post(
        "/page-sections",
        json={"page": "home", "type": "counters", "content": {"items": []}, "is_active": False},
        headers=admin_headers,
    ).json()

    public = client.get("/page-sections", params={"page": "home"})
    assert public.json() == []

    as_admin = client.get(
        "/page-sections", params={"page": "home", "include_inactive": True}, headers=admin_headers
    )
    assert len(as_admin.json()) == 1
    assert as_admin.json()[0]["id"] == section["id"]

    as_guest_with_flag = client.get("/page-sections", params={"page": "home", "include_inactive": True})
    assert as_guest_with_flag.json() == []


def test_update_page_section(client, admin_headers):
    section = client.post(
        "/page-sections",
        json={"page": "catalogo", "type": "custom_html", "content": {"html": "<p>hola</p>"}},
        headers=admin_headers,
    ).json()

    update = client.put(
        f"/page-sections/{section['id']}",
        json={"content": {"html": "<p>chao</p>"}},
        headers=admin_headers,
    )
    assert update.status_code == 200
    assert update.json()["content"]["html"] == "<p>chao</p>"


def test_move_page_section_swaps_position_with_neighbor(client, admin_headers):
    first = client.post(
        "/page-sections", json={"page": "home", "type": "banner", "content": {}}, headers=admin_headers
    ).json()
    second = client.post(
        "/page-sections", json={"page": "home", "type": "counters", "content": {}}, headers=admin_headers
    ).json()
    assert first["position"] == 0
    assert second["position"] == 1

    moved = client.put(
        f"/page-sections/{second['id']}/move", json={"direction": "up"}, headers=admin_headers
    )
    assert moved.status_code == 200
    assert moved.json()["position"] == 0

    listing = client.get("/page-sections", params={"page": "home"}).json()
    assert listing[0]["id"] == second["id"]
    assert listing[1]["id"] == first["id"]

    # Ya está primero: moverlo más arriba no debe hacer nada ni fallar.
    no_op = client.put(f"/page-sections/{second['id']}/move", json={"direction": "up"}, headers=admin_headers)
    assert no_op.json()["position"] == 0


def test_create_page_section_accepts_new_block_types(client, admin_headers):
    for section_type, content in [
        ("announcement", {"text": "Envío gratis desde $200.000"}),
        ("header", {"title": "Nuestra historia"}),
        ("products", {"heading": "Lo más vendido", "limit": 8}),
        ("text", {"heading": "Sobre nosotros", "body": "Texto libre."}),
        ("categories", {"heading": "Explora por familia"}),
        ("image", {"image_url": "https://example.com/foto.jpg"}),
        ("footer", {"heading": "Últimas unidades"}),
    ]:
        response = client.post(
            "/page-sections",
            json={"page": "home", "type": section_type, "content": content},
            headers=admin_headers,
        )
        assert response.status_code == 201, f"{section_type} -> {response.text}"
        assert response.json()["type"] == section_type


def test_delete_page_section(client, admin_headers):
    section = client.post(
        "/page-sections", json={"page": "home", "type": "testimonials", "content": {"items": []}}, headers=admin_headers
    ).json()

    delete = client.delete(f"/page-sections/{section['id']}", headers=admin_headers)
    assert delete.status_code == 204
    assert client.get("/page-sections", params={"page": "home"}).json() == []
