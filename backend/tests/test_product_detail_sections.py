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


def test_admin_can_add_detail_section_and_it_appears_on_product(client, admin_headers):
    product = _create_product(client, admin_headers)

    response = client.post(
        f"/products/{product['id']}/detail-sections",
        json={"title": "Modo de uso", "body": "Aplicar en puntos de pulso."},
        headers=admin_headers,
    )
    assert response.status_code == 201
    assert response.json()["position"] == 0

    detail = client.get("/products/oud-royal").json()
    assert len(detail["detail_sections"]) == 1
    assert detail["detail_sections"][0]["title"] == "Modo de uso"


def test_add_detail_section_requires_admin(client, admin_headers):
    product = _create_product(client, admin_headers)
    response = client.post(
        f"/products/{product['id']}/detail-sections",
        json={"title": "Modo de uso", "body": "Aplicar en puntos de pulso."},
    )
    assert response.status_code == 401


def test_update_detail_section(client, admin_headers):
    product = _create_product(client, admin_headers)
    section = client.post(
        f"/products/{product['id']}/detail-sections",
        json={"title": "Modo de uso", "body": "Aplicar en puntos de pulso."},
        headers=admin_headers,
    ).json()

    update = client.put(
        f"/products/detail-sections/{section['id']}", json={"title": "Ingredientes"}, headers=admin_headers
    )
    assert update.status_code == 200
    assert update.json()["title"] == "Ingredientes"
    assert update.json()["body"] == "Aplicar en puntos de pulso."


def test_move_detail_section_swaps_position_with_neighbor(client, admin_headers):
    product = _create_product(client, admin_headers)
    first = client.post(
        f"/products/{product['id']}/detail-sections",
        json={"title": "Modo de uso", "body": "..."},
        headers=admin_headers,
    ).json()
    second = client.post(
        f"/products/{product['id']}/detail-sections",
        json={"title": "Ingredientes", "body": "..."},
        headers=admin_headers,
    ).json()
    assert first["position"] == 0
    assert second["position"] == 1

    moved = client.put(
        f"/products/detail-sections/{second['id']}/move", json={"direction": "up"}, headers=admin_headers
    )
    assert moved.status_code == 200
    assert moved.json()["position"] == 0

    detail = client.get("/products/oud-royal").json()
    assert detail["detail_sections"][0]["id"] == second["id"]
    assert detail["detail_sections"][1]["id"] == first["id"]


def test_delete_detail_section(client, admin_headers):
    product = _create_product(client, admin_headers)
    section = client.post(
        f"/products/{product['id']}/detail-sections",
        json={"title": "Modo de uso", "body": "..."},
        headers=admin_headers,
    ).json()

    delete = client.delete(f"/products/detail-sections/{section['id']}", headers=admin_headers)
    assert delete.status_code == 204
    assert client.get("/products/oud-royal").json()["detail_sections"] == []
