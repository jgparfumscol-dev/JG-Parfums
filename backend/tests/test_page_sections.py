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


def test_history_records_create_update_and_delete(client, admin_headers):
    section = client.post(
        "/page-sections",
        json={"page": "home", "type": "banner", "content": {"title": "v1"}},
        headers=admin_headers,
    ).json()
    client.put(f"/page-sections/{section['id']}", json={"content": {"title": "v2"}}, headers=admin_headers)
    client.delete(f"/page-sections/{section['id']}", headers=admin_headers)

    history = client.get("/page-sections/history", params={"page": "home"}, headers=admin_headers)
    assert history.status_code == 200
    actions = [h["action"] for h in history.json() if h["section_id"] == section["id"]]
    # más nuevo primero
    assert actions == ["deleted", "updated", "created"]


def test_history_requires_admin(client, admin_headers):
    client.post("/page-sections", json={"page": "home", "type": "banner", "content": {}}, headers=admin_headers)
    response = client.get("/page-sections/history", params={"page": "home"})
    assert response.status_code == 401


def test_restore_history_entry_for_existing_section(client, admin_headers):
    section = client.post(
        "/page-sections",
        json={"page": "home", "type": "banner", "content": {"title": "original"}},
        headers=admin_headers,
    ).json()
    client.put(f"/page-sections/{section['id']}", json={"content": {"title": "cambiado"}}, headers=admin_headers)

    history = client.get("/page-sections/history", params={"page": "home"}, headers=admin_headers).json()
    created_entry = next(h for h in history if h["action"] == "created")

    restore = client.post(f"/page-sections/history/{created_entry['id']}/restore", headers=admin_headers)
    assert restore.status_code == 200
    assert restore.json()["content"]["title"] == "original"
    assert restore.json()["id"] == section["id"]  # misma fila, no una nueva


def test_restore_history_entry_recreates_deleted_section(client, admin_headers):
    section = client.post(
        "/page-sections",
        json={"page": "home", "type": "counters", "content": {"items": [{"value": "500+"}]}},
        headers=admin_headers,
    ).json()
    client.delete(f"/page-sections/{section['id']}", headers=admin_headers)
    assert client.get("/page-sections", params={"page": "home", "include_inactive": True}, headers=admin_headers).json() == []

    history = client.get("/page-sections/history", params={"page": "home"}, headers=admin_headers).json()
    deleted_entry = next(h for h in history if h["action"] == "deleted")

    restore = client.post(f"/page-sections/history/{deleted_entry['id']}/restore", headers=admin_headers)
    assert restore.status_code == 200
    assert restore.json()["content"]["items"][0]["value"] == "500+"

    listing = client.get("/page-sections", params={"page": "home"}).json()
    assert len(listing) == 1


def test_builtin_section_is_editable_like_any_other(client, admin_headers, db):
    # El seed real de las 5 secciones fijas vive en la migración (probado
    # aparte, upgrade/downgrade/upgrade); acá se prueba el mecanismo en sí
    # -- que una fila con key/is_builtin se vea y se edite igual que
    # cualquier sección -- sin depender de que la migración haya corrido,
    # ya que los tests arman el esquema con `Base.metadata.create_all`.
    from models.page_section import PageSection

    section = PageSection(
        page="home", type="section_heading", position=0, is_active=True,
        content={"heading": "Recién llegados"}, key="home_recent_heading", is_builtin=True,
    )
    db.add(section)
    db.commit()
    db.refresh(section)

    listing = client.get("/page-sections", params={"page": "home"}).json()
    assert listing[0]["key"] == "home_recent_heading"
    assert listing[0]["is_builtin"] is True

    update = client.put(
        f"/page-sections/{section.id}",
        json={"content": {"heading": "Novedades"}},
        headers=admin_headers,
    )
    assert update.status_code == 200
    assert update.json()["content"]["heading"] == "Novedades"
    assert update.json()["key"] == "home_recent_heading"
