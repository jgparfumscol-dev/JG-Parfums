from datetime import datetime, timedelta, timezone

import pytest


def _message(**overrides):
    base = {"text": "Envío gratis desde $250.000"}
    base.update(overrides)
    return base


def _bar_content(**overrides):
    base = {"messages": [_message()]}
    base.update(overrides)
    return base


def test_create_announcement_bar_with_defaults(client, admin_headers):
    response = client.post(
        "/page-sections",
        json={"page": "home", "type": "announcement_bar", "content": _bar_content()},
        headers=admin_headers,
    )
    assert response.status_code == 201, response.text
    content = response.json()["content"]
    assert content["position"] == "inline"
    assert content["rotation_interval"] == 5
    assert content["transition"] == "fade"
    assert content["closable"] is False
    assert content["variant"] == "onyx"
    assert content["messages"][0]["text"] == "Envío gratis desde $250.000"


def test_rejects_empty_messages(client, admin_headers):
    response = client.post(
        "/page-sections",
        json={"page": "home", "type": "announcement_bar", "content": {"messages": []}},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_rejects_text_over_90_chars(client, admin_headers):
    response = client.post(
        "/page-sections",
        json={"page": "home", "type": "announcement_bar", "content": _bar_content(messages=[_message(text="a" * 91)])},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_rejects_javascript_link(client, admin_headers):
    response = client.post(
        "/page-sections",
        json={
            "page": "home",
            "type": "announcement_bar",
            "content": _bar_content(messages=[_message(link_url="javascript:alert(1)")]),
        },
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_accepts_relative_and_https_links(client, admin_headers):
    for link in ["/catalogo.html", "https://wa.me/573001234567"]:
        response = client.post(
            "/page-sections",
            json={
                "page": "home",
                "type": "announcement_bar",
                "content": _bar_content(messages=[_message(link_url=link)]),
            },
            headers=admin_headers,
        )
        assert response.status_code == 201, f"{link} -> {response.text}"


def test_rejects_bare_domain_without_scheme(client, admin_headers):
    response = client.post(
        "/page-sections",
        json={
            "page": "home",
            "type": "announcement_bar",
            "content": _bar_content(messages=[_message(link_url="example.com")]),
        },
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_rejects_html_in_text_and_highlight(client, admin_headers):
    for overrides in [{"text": "Envío <b>gratis</b>"}, {"highlight": "<script>"}]:
        response = client.post(
            "/page-sections",
            json={"page": "home", "type": "announcement_bar", "content": _bar_content(messages=[_message(**overrides)])},
            headers=admin_headers,
        )
        assert response.status_code == 422, overrides


def test_rejects_invalid_variant(client, admin_headers):
    response = client.post(
        "/page-sections",
        json={"page": "home", "type": "announcement_bar", "content": _bar_content(variant="azul")},
        headers=admin_headers,
    )
    assert response.status_code == 422


@pytest.mark.parametrize("interval", [2, 11])
def test_rejects_rotation_interval_outside_range(client, admin_headers, interval):
    response = client.post(
        "/page-sections",
        json={"page": "home", "type": "announcement_bar", "content": _bar_content(rotation_interval=interval)},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_rejects_end_date_before_start_date(client, admin_headers):
    response = client.post(
        "/page-sections",
        json={
            "page": "home",
            "type": "announcement_bar",
            "content": _bar_content(
                messages=[_message(start_date="2026-06-01T00:00:00", end_date="2026-05-01T00:00:00")]
            ),
        },
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_public_endpoint_excludes_inactive_messages(client, admin_headers):
    content = _bar_content(messages=[_message(text="Mensaje activo"), _message(text="Mensaje oculto", is_active=False)])
    client.post("/page-sections", json={"page": "home", "type": "announcement_bar", "content": content}, headers=admin_headers)

    public = client.get("/page-sections", params={"page": "home"}).json()
    messages = public[0]["content"]["messages"]
    assert len(messages) == 1
    assert messages[0]["text"] == "Mensaje activo"


def test_public_endpoint_excludes_messages_outside_date_range(client, admin_headers):
    now = datetime.now(timezone.utc)
    future = (now + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")
    past = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")

    content = _bar_content(
        messages=[
            _message(text="Vigente"),
            _message(text="Todavia no empieza", start_date=future),
            _message(text="Ya termino", end_date=past),
        ]
    )
    client.post("/page-sections", json={"page": "home", "type": "announcement_bar", "content": content}, headers=admin_headers)

    public = client.get("/page-sections", params={"page": "home"}).json()
    texts = [m["text"] for m in public[0]["content"]["messages"]]
    assert texts == ["Vigente"]


def test_admin_sees_all_messages_regardless_of_date_or_active(client, admin_headers):
    content = _bar_content(
        messages=[_message(text="Vigente"), _message(text="Oculto", is_active=False)]
    )
    client.post("/page-sections", json={"page": "home", "type": "announcement_bar", "content": content}, headers=admin_headers)

    as_admin = client.get("/page-sections", params={"page": "home", "include_inactive": True}, headers=admin_headers).json()
    assert len(as_admin[0]["content"]["messages"]) == 2


def test_only_one_active_top_bar_per_page(client, admin_headers):
    first = client.post(
        "/page-sections",
        json={"page": "home", "type": "announcement_bar", "content": _bar_content(position="top")},
        headers=admin_headers,
    )
    assert first.status_code == 201

    second = client.post(
        "/page-sections",
        json={"page": "home", "type": "announcement_bar", "content": _bar_content(position="top")},
        headers=admin_headers,
    )
    assert second.status_code == 400

    # "inline" no compite por el mismo lugar, así que no choca.
    inline = client.post(
        "/page-sections",
        json={"page": "home", "type": "announcement_bar", "content": _bar_content(position="inline")},
        headers=admin_headers,
    )
    assert inline.status_code == 201

    # Otra página no comparte el límite.
    other_page = client.post(
        "/page-sections",
        json={"page": "catalogo", "type": "announcement_bar", "content": _bar_content(position="top")},
        headers=admin_headers,
    )
    assert other_page.status_code == 201


def test_top_bar_conflict_ignores_inactive_bars(client, admin_headers):
    first = client.post(
        "/page-sections",
        json={
            "page": "home",
            "type": "announcement_bar",
            "content": _bar_content(position="top"),
            "is_active": False,
        },
        headers=admin_headers,
    )
    assert first.status_code == 201

    second = client.post(
        "/page-sections",
        json={"page": "home", "type": "announcement_bar", "content": _bar_content(position="top")},
        headers=admin_headers,
    )
    assert second.status_code == 201


def test_update_to_top_conflicts_with_existing_top_bar(client, admin_headers):
    client.post(
        "/page-sections",
        json={"page": "home", "type": "announcement_bar", "content": _bar_content(position="top")},
        headers=admin_headers,
    )
    inline = client.post(
        "/page-sections",
        json={"page": "home", "type": "announcement_bar", "content": _bar_content(position="inline")},
        headers=admin_headers,
    ).json()

    update = client.put(
        f"/page-sections/{inline['id']}",
        json={"content": _bar_content(position="top")},
        headers=admin_headers,
    )
    assert update.status_code == 400
