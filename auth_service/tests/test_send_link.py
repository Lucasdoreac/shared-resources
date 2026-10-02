import pytest
from flask import Flask

import auth_routes
import rate_limit

EMAIL = "prof@udf.edu.br"


TOKEN = "t" * 43


class FakeController:
    def generate_token(self):
        return TOKEN

    def insert_token(self, email, token):
        pass


class Sent:
    status_code = 200


@pytest.fixture
def client(monkeypatch):
    rate_limit.reset_local()
    sent = []
    monkeypatch.setattr(auth_routes, "AuthenticationController", FakeController)
    monkeypatch.setattr(auth_routes, "send_magic_link", lambda *args: sent.append(args) or Sent())
    monkeypatch.setenv("REACT_APP", "http://front")
    for name in ("FLASK_ENV", "AUTH_DEV_RETURN_LINK", "AUTH_ALLOWED_EMAILS"):
        monkeypatch.delenv(name, raising=False)
    app = Flask(__name__)
    app.register_blueprint(auth_routes.auth_bp)
    test_client = app.test_client()
    test_client.sent = sent
    return test_client


def send_link(client, email=EMAIL):
    return client.post(f"/auth/send-link?email={email}")


def test_only_explicitly_allowed_external_email_gets_a_link(client, monkeypatch):
    allowed = "lucas.dorea@cs.udf.edu.br"
    monkeypatch.setenv("AUTH_ALLOWED_EMAILS", f"{allowed},other@example.com")

    response = send_link(client, allowed)

    assert response.status_code == 201
    assert [args[0] for args in client.sent] == [allowed]


def test_external_email_not_on_allowlist_is_rejected(client, monkeypatch):
    monkeypatch.setenv("AUTH_ALLOWED_EMAILS", "lucas.dorea@cs.udf.edu.br")

    response = send_link(client, "someone@example.com")

    assert response.status_code == 400
    assert client.sent == []


def test_development_alone_does_not_return_the_login_link(client, monkeypatch):
    # Antes, FLASK_ENV=development bastava para o link de login voltar na
    # resposta HTTP: um deploy com o .env de dev deixava qualquer um entrar
    # como qualquer @udf.edu.br. Agora é preciso ligar AUTH_DEV_RETURN_LINK.
    monkeypatch.setenv("FLASK_ENV", "development")

    response = send_link(client)

    assert response.status_code == 201
    assert "magic_link" not in response.get_json()
    assert [args[0] for args in client.sent] == [EMAIL]


def test_link_returned_only_in_development_with_the_flag_on(client, monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("AUTH_DEV_RETURN_LINK", "true")

    response = send_link(client)

    assert response.get_json() == {"magic_link": f"http://front/auth/callback?email=prof%40udf.edu.br&hash={TOKEN}"}
    assert client.sent == []


@pytest.mark.parametrize("flask_env, flag", [
    ("production", "true"),   # flag esquecida ligada em produção
    (None, "true"),           # FLASK_ENV ausente = produção
    ("development", "false"),
    ("development", "0"),
])
def test_otherwise_the_link_goes_by_email(client, monkeypatch, flask_env, flag):
    if flask_env:
        monkeypatch.setenv("FLASK_ENV", flask_env)
    monkeypatch.setenv("AUTH_DEV_RETURN_LINK", flag)

    response = send_link(client)

    assert response.get_json() == {"message": "Magic link sent successfully"}
    assert len(client.sent) == 1
