def _payload(**overrides):
    data = {
        "name": "Laura Gómez",
        "contact": "laura@example.com",
        "message": "Hola, quiero saber si tienen el perfume X en decant de 5ml.",
    }
    data.update(overrides)
    return data


def test_create_contact_message(client):
    response = client.post("/contact-messages", json=_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Laura Gómez"
    assert body["is_read"] is False


def test_create_contact_message_rejects_blank_fields(client):
    response = client.post("/contact-messages", json=_payload(message="   "))
    assert response.status_code == 422


def test_list_contact_messages_requires_admin(client):
    client.post("/contact-messages", json=_payload())
    response = client.get("/contact-messages")
    assert response.status_code == 401


def test_list_contact_messages_as_admin(client, admin_headers):
    client.post("/contact-messages", json=_payload())
    client.post("/contact-messages", json=_payload(name="Otro cliente"))

    response = client.get("/contact-messages", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2


def test_mark_contact_message_read(client, admin_headers):
    created = client.post("/contact-messages", json=_payload()).json()

    response = client.put(f"/contact-messages/{created['id']}", json={"is_read": True}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["is_read"] is True


def test_delete_contact_message(client, admin_headers):
    created = client.post("/contact-messages", json=_payload()).json()

    response = client.delete(f"/contact-messages/{created['id']}", headers=admin_headers)
    assert response.status_code == 204

    listing = client.get("/contact-messages", headers=admin_headers)
    assert listing.json() == []
