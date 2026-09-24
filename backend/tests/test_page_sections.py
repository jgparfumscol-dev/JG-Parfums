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
        ("chat_widget", {"title": "Habla con nosotros", "position": "right", "offset": 24, "size": "small"}),
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


def test_create_classes_carousel_with_defaults(client, admin_headers):
    create = client.post(
        "/page-sections",
        json={"page": "home", "type": "classes_carousel", "content": {"heading": "Explora por clase"}},
        headers=admin_headers,
    )
    assert create.status_code == 201
    content = create.json()["content"]
    assert content["heading"] == "Explora por clase"
    assert content["mode"] == "all"
    assert content["category_ids"] == []
    assert content["layout"] == "contained"
    assert content["cards_mobile"] == 1.3
    assert content["cards_tablet"] == 3
    assert content["cards_desktop"] == 4
    assert content["show_arrows"] is True
    assert content["autoplay"] is False


def test_create_classes_carousel_manual_mode_with_selection(client, admin_headers):
    create = client.post(
        "/page-sections",
        json={
            "page": "home", "type": "classes_carousel",
            "content": {"mode": "manual", "category_ids": [3, 1, 2], "cards_mobile": 1, "cards_desktop": 5},
        },
        headers=admin_headers,
    )
    assert create.status_code == 201
    content = create.json()["content"]
    assert content["mode"] == "manual"
    assert content["category_ids"] == [3, 1, 2]
    assert content["cards_desktop"] == 5


def test_create_classes_carousel_rejects_invalid_mode(client, admin_headers):
    response = client.post(
        "/page-sections",
        json={"page": "home", "type": "classes_carousel", "content": {"mode": "featured"}},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_create_classes_carousel_full_layout(client, admin_headers):
    create = client.post(
        "/page-sections",
        json={"page": "home", "type": "classes_carousel", "content": {"layout": "full"}},
        headers=admin_headers,
    )
    assert create.status_code == 201
    assert create.json()["content"]["layout"] == "full"


def test_create_classes_carousel_spacing_and_card_ratio_with_defaults(client, admin_headers):
    create = client.post(
        "/page-sections",
        json={"page": "home", "type": "classes_carousel", "content": {}},
        headers=admin_headers,
    )
    assert create.status_code == 201
    content = create.json()["content"]
    assert content["spacing"] == "normal"
    assert content["card_ratio_w"] == 3
    assert content["card_ratio_h"] == 4

    custom = client.post(
        "/page-sections",
        json={
            "page": "home", "type": "classes_carousel",
            "content": {"spacing": "flush", "card_ratio_w": 16, "card_ratio_h": 9},
        },
        headers=admin_headers,
    )
    assert custom.status_code == 201
    custom_content = custom.json()["content"]
    assert custom_content["spacing"] == "flush"
    assert custom_content["card_ratio_w"] == 16
    assert custom_content["card_ratio_h"] == 9


def test_create_classes_carousel_rejects_invalid_spacing(client, admin_headers):
    response = client.post(
        "/page-sections",
        json={"page": "home", "type": "classes_carousel", "content": {"spacing": "huge"}},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_create_classes_carousel_rejects_zero_card_ratio(client, admin_headers):
    response = client.post(
        "/page-sections",
        json={"page": "home", "type": "classes_carousel", "content": {"card_ratio_w": 0}},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_create_classes_carousel_rejects_invalid_layout(client, admin_headers):
    response = client.post(
        "/page-sections",
        json={"page": "home", "type": "classes_carousel", "content": {"layout": "huge"}},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_create_classes_carousel_rejects_cards_out_of_range(client, admin_headers):
    response = client.post(
        "/page-sections",
        json={"page": "home", "type": "classes_carousel", "content": {"cards_desktop": 20}},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_create_classes_carousel_continuous_mode_with_direction(client, admin_headers):
    create = client.post(
        "/page-sections",
        json={
            "page": "home", "type": "classes_carousel",
            "content": {"carousel_mode": "continuous", "carousel_direction": "right"},
        },
        headers=admin_headers,
    )
    assert create.status_code == 201
    content = create.json()["content"]
    assert content["carousel_mode"] == "continuous"
    assert content["carousel_direction"] == "right"


def test_create_classes_carousel_rejects_invalid_carousel_mode(client, admin_headers):
    response = client.post(
        "/page-sections",
        json={"page": "home", "type": "classes_carousel", "content": {"carousel_mode": "fade"}},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_create_classes_carousel_rejects_invalid_carousel_direction(client, admin_headers):
    response = client.post(
        "/page-sections",
        json={"page": "home", "type": "classes_carousel", "content": {"carousel_direction": "up"}},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_create_classes_carousel_continuous_speed(client, admin_headers):
    create = client.post(
        "/page-sections",
        json={
            "page": "home", "type": "classes_carousel",
            "content": {"carousel_mode": "continuous", "carousel_speed": "fast"},
        },
        headers=admin_headers,
    )
    assert create.status_code == 201
    assert create.json()["content"]["carousel_speed"] == "fast"


def test_create_classes_carousel_rejects_invalid_carousel_speed(client, admin_headers):
    response = client.post(
        "/page-sections",
        json={"page": "home", "type": "classes_carousel", "content": {"carousel_speed": "turbo"}},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_update_classes_carousel_validates_content(client, admin_headers):
    section = client.post(
        "/page-sections", json={"page": "home", "type": "classes_carousel", "content": {}}, headers=admin_headers
    ).json()
    update = client.put(
        f"/page-sections/{section['id']}",
        json={"content": {"autoplay_interval": 30}},
        headers=admin_headers,
    )
    assert update.status_code == 422


def test_create_brands_carousel_with_defaults(client, admin_headers):
    create = client.post(
        "/page-sections",
        json={"page": "home", "type": "brands_carousel", "content": {}},
        headers=admin_headers,
    )
    assert create.status_code == 201
    content = create.json()["content"]
    assert content["mode"] == "all"
    assert content["layout"] == "contained"
    assert content["spacing"] == "normal"
    assert content["carousel_mode"] == "arrows"
    assert content["logos_mobile"] == 3
    assert content["logos_tablet"] == 5
    assert content["logos_desktop"] == 7
    assert content["logo_color"] == "grayscale"


def test_create_brands_carousel_layout_and_spacing(client, admin_headers):
    create = client.post(
        "/page-sections",
        json={"page": "home", "type": "brands_carousel", "content": {"layout": "full", "spacing": "flush"}},
        headers=admin_headers,
    )
    assert create.status_code == 201
    content = create.json()["content"]
    assert content["layout"] == "full"
    assert content["spacing"] == "flush"


def test_create_brands_carousel_rejects_invalid_layout(client, admin_headers):
    response = client.post(
        "/page-sections",
        json={"page": "home", "type": "brands_carousel", "content": {"layout": "huge"}},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_create_brands_carousel_rejects_invalid_spacing(client, admin_headers):
    response = client.post(
        "/page-sections",
        json={"page": "home", "type": "brands_carousel", "content": {"spacing": "huge"}},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_create_brands_carousel_continuous_mode_with_manual_selection(client, admin_headers):
    create = client.post(
        "/page-sections",
        json={
            "page": "home", "type": "brands_carousel",
            "content": {"mode": "manual", "brand_ids": [2, 1], "carousel_mode": "continuous", "logo_color": "original"},
        },
        headers=admin_headers,
    )
    assert create.status_code == 201
    content = create.json()["content"]
    assert content["brand_ids"] == [2, 1]
    assert content["carousel_mode"] == "continuous"
    assert content["logo_color"] == "original"


def test_create_brands_carousel_rejects_invalid_carousel_mode(client, admin_headers):
    response = client.post(
        "/page-sections",
        json={"page": "home", "type": "brands_carousel", "content": {"carousel_mode": "fade"}},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_create_brands_carousel_continuous_speed(client, admin_headers):
    create = client.post(
        "/page-sections",
        json={
            "page": "home", "type": "brands_carousel",
            "content": {"carousel_mode": "continuous", "carousel_speed": "slow"},
        },
        headers=admin_headers,
    )
    assert create.status_code == 201
    assert create.json()["content"]["carousel_speed"] == "slow"


def test_create_brands_carousel_rejects_invalid_carousel_speed(client, admin_headers):
    response = client.post(
        "/page-sections",
        json={"page": "home", "type": "brands_carousel", "content": {"carousel_speed": "turbo"}},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_new_carousel_types_require_admin(client):
    response = client.post(
        "/page-sections", json={"page": "home", "type": "classes_carousel", "content": {}}
    )
    assert response.status_code == 401


def test_restore_classes_carousel_from_history(client, admin_headers):
    section = client.post(
        "/page-sections",
        json={"page": "home", "type": "classes_carousel", "content": {"heading": "Explora"}},
        headers=admin_headers,
    ).json()
    client.put(
        f"/page-sections/{section['id']}", json={"content": {"heading": "Nuestras clases"}}, headers=admin_headers
    )

    history = client.get("/page-sections/history", params={"page": "home"}, headers=admin_headers).json()
    created_entry = next(h for h in history if h["action"] == "created")

    restore = client.post(f"/page-sections/history/{created_entry['id']}/restore", headers=admin_headers)
    assert restore.status_code == 200
    assert restore.json()["content"]["heading"] == "Explora"
