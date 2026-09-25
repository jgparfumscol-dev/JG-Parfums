import logging

import httpx

from services import email_service


def _fake_post(status_code, body):
    def _post(url, **kwargs):
        return httpx.Response(status_code, json=body, request=httpx.Request("POST", url))

    return _post


def test_send_email_returns_true_on_success(monkeypatch):
    monkeypatch.setattr(email_service, "RESEND_API_KEY", "re_test")
    monkeypatch.setattr("services.email_service.httpx.post", _fake_post(200, {"id": "abc"}))

    assert email_service.send_email("cliente@example.com", "Hola", "<p>hola</p>") is True


def test_send_email_logs_the_reason_resend_rejected_it(monkeypatch, caplog):
    monkeypatch.setattr(email_service, "RESEND_API_KEY", "re_test")
    body = {"statusCode": 403, "message": "The jgparfums.com.co domain is not verified.", "name": "validation_error"}
    monkeypatch.setattr("services.email_service.httpx.post", _fake_post(403, body))

    with caplog.at_level(logging.ERROR, logger="jg_parfums.email"):
        assert email_service.send_email("cliente@example.com", "Hola", "<p>hola</p>") is False

    assert "HTTP 403" in caplog.text
    assert "domain is not verified" in caplog.text
    assert "re_test" not in caplog.text


def test_send_email_without_api_key_does_nothing(monkeypatch, caplog):
    monkeypatch.setattr(email_service, "RESEND_API_KEY", "")

    def _should_not_be_called(*args, **kwargs):
        raise AssertionError("no debería llamar a Resend sin API key")

    monkeypatch.setattr("services.email_service.httpx.post", _should_not_be_called)

    assert email_service.send_email("cliente@example.com", "Hola", "<p>hola</p>") is False
    assert "RESEND_API_KEY no configurada" in caplog.text
