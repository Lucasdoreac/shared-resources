from unittest.mock import Mock

import auth_routes
import rate_limit
from SLL_auth import create_app
from mongo import MongoDBConnectionFactory


class TestConfig:
    TESTING = True
    MONGO_URI = "mongodb://localhost:27017"
    MONGO_DATABASE = "test_auth_service"


def make_client(monkeypatch):
    rate_limit.reset_local()
    monkeypatch.setattr(
        MongoDBConnectionFactory, "init_app", lambda *_args, **_kwargs: None
    )
    app = create_app(TestConfig)
    return app.test_client()


def test_send_link_accepts_exact_allowlist_without_sending_email(monkeypatch):
    controller = Mock()
    controller.generate_token.return_value = "test-token"
    monkeypatch.setattr(auth_routes, "AuthenticationController", lambda: controller)
    send_email = Mock(side_effect=AssertionError("email delivery must stay disabled"))
    monkeypatch.setattr(auth_routes, "send_magic_link", send_email)
    monkeypatch.setenv("AUTH_EMAIL_ALLOWLIST", "reviewer@cs.udf.edu.br")
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("AUTH_DEV_RETURN_LINK", "true")
    monkeypatch.setenv("REACT_APP", "http://localhost:3000")

    response = make_client(monkeypatch).post(
        "/auth/send-link?email=%20Reviewer%40cs.udf.edu.br%20"
    )

    assert response.status_code == 201
    assert response.get_json()["magic_link"].startswith(
        "http://localhost:3000/auth/callback?email=reviewer%40cs.udf.edu.br"
    )
    controller.insert_token.assert_called_once_with(
        "reviewer@cs.udf.edu.br", "test-token"
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
    controller.generate_token.return_value = "test-token"
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
    controller.generate_token.return_value = "test-token"
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
        "https://reservas.example.test/auth/callback?email=reviewer%40cs.udf.edu.br&hash=test-token",
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



# --- e-mail logo: rendered from the real template ------------------------------

def render_magic_link(monkeypatch):
    app = create_app(TestConfig)
    monkeypatch.setattr(MongoDBConnectionFactory, "init_app", lambda *_args, **_kwargs: None)
    with app.test_request_context():
        return auth_routes.render_template(
            "email/magic_link.html",
            username="reviewer",
            magic_link="https://reservas.example.test/auth/callback?email=r@udf.edu.br&hash=abc",
            logo_url=auth_routes.email_logo_url(),
        )


def test_logo_url_comes_from_email_assets_url_without_a_trailing_slash(monkeypatch):
    monkeypatch.setenv("EMAIL_ASSETS_URL", "https://web.example.test/labtech/email-icones/")
    monkeypatch.delenv("MINIO_URL", raising=False)

    assert auth_routes.email_logo_url() == "https://web.example.test/labtech/email-icones/dw-corp-logo.png"


def test_the_email_shows_the_logo_above_the_greeting_with_alt_text(monkeypatch):
    monkeypatch.setenv("EMAIL_ASSETS_URL", "https://web.example.test/labtech/email-icones")

    html = render_magic_link(monkeypatch)

    assert '<img src="https://web.example.test/labtech/email-icones/dw-corp-logo.png"' in html
    assert 'alt="DW Corp"' in html
    assert html.index("<img") < html.index("Olá reviewer")
    assert 'href="https://reservas.example.test/auth/callback?email=r@udf.edu.br&amp;hash=abc"' in html \
        or 'href="https://reservas.example.test/auth/callback?email=r@udf.edu.br&hash=abc"' in html


def test_without_a_configured_host_the_email_has_no_broken_image(monkeypatch):
    monkeypatch.delenv("EMAIL_ASSETS_URL", raising=False)
    monkeypatch.delenv("MINIO_URL", raising=False)

    html = render_magic_link(monkeypatch)

    assert "<img" not in html
    assert "None/" not in html          # the old code produced src="None/labtech/..."
    assert "Autorizar!" in html


def test_an_unrelated_minio_url_no_longer_leaks_into_the_email(monkeypatch):
    monkeypatch.delenv("EMAIL_ASSETS_URL", raising=False)
    monkeypatch.setenv("MINIO_URL", "http://dwcorp.com.br:9000")

    assert "dwcorp.com.br" not in render_magic_link(monkeypatch)


def test_development_alone_does_not_return_the_login_link(monkeypatch):
    controller = Mock()
    controller.generate_token.return_value = "test-token"
    monkeypatch.setattr(auth_routes, "AuthenticationController", lambda: controller)
    send_email = Mock(return_value=Mock(status_code=200))
    monkeypatch.setattr(auth_routes, "send_magic_link", send_email)
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.delenv("AUTH_DEV_RETURN_LINK", raising=False)
    monkeypatch.setenv("EMAIL_DRY_RUN", "false")
    monkeypatch.setenv("REACT_APP", "http://localhost:3000")

    response = make_client(monkeypatch).post("/auth/send-link?email=prof@udf.edu.br")

    assert "magic_link" not in (response.get_json() or {})
    send_email.assert_called_once()


def test_the_old_allowlist_name_is_still_honoured_when_the_new_one_is_unset(monkeypatch):
    monkeypatch.delenv("AUTH_EMAIL_ALLOWLIST", raising=False)
    monkeypatch.setenv("AUTH_ALLOWED_EMAILS", "legacy@example.com")
    assert auth_routes.allowlist_setting() == "legacy@example.com"
    monkeypatch.setenv("AUTH_EMAIL_ALLOWLIST", "new@example.com")
    assert auth_routes.allowlist_setting() == "new@example.com"
    monkeypatch.setenv("AUTH_EMAIL_ALLOWLIST", "")
    assert auth_routes.allowlist_setting() == ""  # an explicit empty value wins
