from unittest.mock import Mock

import auth_routes
from SLL_auth import create_app
from mongo import MongoDBConnectionFactory


class TestConfig:
    TESTING = True
    MONGO_URI = "mongodb://localhost:27017"
    MONGO_DATABASE = "test_auth_service"


def make_client(monkeypatch):
    monkeypatch.setattr(
        MongoDBConnectionFactory, "init_app", lambda *_args, **_kwargs: None
    )
    app = create_app(TestConfig)
    return app.test_client()


def test_send_link_accepts_exact_allowlist_without_sending_email(monkeypatch):
    controller = Mock()
    controller.generate_hash = "test-token"
    monkeypatch.setattr(auth_routes, "AuthenticationController", lambda: controller)
    send_email = Mock(side_effect=AssertionError("email delivery must stay disabled"))
    monkeypatch.setattr(auth_routes, "send_magic_link", send_email)
    monkeypatch.setenv("AUTH_EMAIL_ALLOWLIST", "reviewer@cs.udf.edu.br")
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("REACT_APP", "http://localhost:3000")

    response = make_client(monkeypatch).post(
        "/auth/send-link?email=%20Reviewer%40cs.udf.edu.br%20"
    )

    assert response.status_code == 201
    assert response.get_json()["magic_link"].startswith(
        "http://localhost:3000/auth/callback?email=Reviewer@cs.udf.edu.br"
    )
    controller.insert_token.assert_called_once_with(
        "Reviewer@cs.udf.edu.br", "test-token"
    )
    send_email.assert_not_called()


def test_send_link_rejects_other_developer_addresses(monkeypatch):
    controller = Mock()
    monkeypatch.setattr(auth_routes, "AuthenticationController", lambda: controller)
    monkeypatch.setenv("AUTH_EMAIL_ALLOWLIST", "reviewer@cs.udf.edu.br")

    response = make_client(monkeypatch).post(
        "/auth/send-link?email=someone%40cs.udf.edu.br"
    )

    assert response.status_code == 400
    controller.insert_token.assert_not_called()


def test_send_link_dry_run_suppresses_delivery_and_token_write(monkeypatch):
    controller = Mock()
    controller.generate_hash = "test-token"
    monkeypatch.setattr(auth_routes, "AuthenticationController", lambda: controller)
    send_email = Mock(side_effect=AssertionError("dry-run must not send email"))
    monkeypatch.setattr(auth_routes, "send_magic_link", send_email)
    monkeypatch.setenv("AUTH_EMAIL_ALLOWLIST", "reviewer@cs.udf.edu.br")
    monkeypatch.setenv("EMAIL_DRY_RUN", "true")
    monkeypatch.setenv("FLASK_ENV", "production")

    response = make_client(monkeypatch).post(
        "/auth/send-link?email=reviewer%40cs.udf.edu.br"
    )

    assert response.status_code == 202
    assert response.get_json() == {"message": "Email dry-run enabled; no email sent"}
    controller.insert_token.assert_not_called()
    send_email.assert_not_called()


def test_send_link_still_delivers_when_dry_run_is_disabled(monkeypatch):
    controller = Mock()
    controller.generate_hash = "test-token"
    monkeypatch.setattr(auth_routes, "AuthenticationController", lambda: controller)
    send_email = Mock(return_value=Mock(status_code=201))
    monkeypatch.setattr(auth_routes, "send_magic_link", send_email)
    monkeypatch.setenv("AUTH_EMAIL_ALLOWLIST", "reviewer@cs.udf.edu.br")
    monkeypatch.setenv("EMAIL_DRY_RUN", "false")
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("REACT_APP", "https://reservas.example.test")

    response = make_client(monkeypatch).post(
        "/auth/send-link?email=reviewer%40cs.udf.edu.br"
    )

    assert response.status_code == 201
    controller.insert_token.assert_called_once_with(
        "reviewer@cs.udf.edu.br", "test-token"
    )
    send_email.assert_called_once_with(
        "reviewer@cs.udf.edu.br",
        "reviewer",
        "https://reservas.example.test/auth/callback?email=reviewer@cs.udf.edu.br&hash=test-token",
    )


def test_send_magic_link_uses_brevo_api(monkeypatch):
    response = Mock(status_code=201)
    request = Mock(return_value=response)
    monkeypatch.setattr(auth_routes, "render_template", lambda *_args, **_kwargs: "<p>link</p>")
    monkeypatch.setattr(auth_routes.requests, "post", request)
    monkeypatch.setenv("BREVO_API_KEY", "test-brevo-key")
    monkeypatch.setenv("BREVO_SENDER_EMAIL", "verified@example.test")
    monkeypatch.setenv("BREVO_SENDER_NAME", "Reservas UDF")
    monkeypatch.setenv("MINIO_URL", "https://objects.example.test")

    result = auth_routes.send_magic_link(
        "reviewer@cs.udf.edu.br",
        "reviewer",
        "https://reservas.example.test/auth/callback?token=test",
    )

    assert result.status_code == 201
    request.assert_called_once_with(
        "https://api.brevo.com/v3/smtp/email",
        json={
            "sender": {"name": "Reservas UDF", "email": "verified@example.test"},
            "to": [{"email": "reviewer@cs.udf.edu.br", "name": "reviewer"}],
            "subject": "Autorização de Acesso",
            "htmlContent": "<p>link</p>",
        },
        headers={
            "api-key": "test-brevo-key",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        timeout=15,
    )
