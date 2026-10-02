"""The catalog is closed by default; keys never reach the logs."""

import logging

import pytest
from flask import Flask

import config_module
from utils import auth as auth_module

KEY = "test-api-key-0123456789"
WRONG = "wrong-key-typed-by-a-caller"


@pytest.fixture(autouse=True)
def keys(monkeypatch):
    monkeypatch.setattr(auth_module, "API_KEY_LIST", [KEY])
    for name in ("FLASK_ENV", "ALLOW_INSECURE_DEV"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def client():
    app = Flask(__name__)
    app.before_request(auth_module.require_api_key_on_catalog)

    @app.route("/restapi/teachers/")
    def teachers():
        return {"data": []}

    @app.route("/restapi/offers/", methods=["POST"])
    @auth_module.check_api_key
    def offers():
        return {"ok": True}

    @app.route("/graphql/", methods=["POST"])
    def graphql():
        return {"data": {}}

    @app.route("/graphql/graphiql")
    def graphiql():
        return "ide"

    @app.route("/apispec.json")
    def spec():
        return {}

    @app.route("/health")
    def health():
        return "ok"

    return app.test_client()


def test_closed_by_default_for_every_data_route(client):
    for method, path in (("get", "/restapi/teachers/"), ("post", "/restapi/offers/"),
                         ("post", "/graphql/"), ("get", "/graphql/graphiql")):
        assert getattr(client, method)(path).status_code == 403, path
        assert getattr(client, method)(path, headers={"x-api-key": WRONG}).status_code == 403, path
    assert client.get("/restapi/teachers/", headers={"x-api-key": KEY}).status_code == 200
    assert client.post("/graphql/", json={}, headers={"x-api-key": KEY}).status_code == 200


def test_docs_and_health_stay_open(client):
    assert client.get("/apispec.json").status_code == 200
    assert client.get("/health").status_code == 200


def test_an_empty_key_header_is_invalid(client):
    assert client.get("/restapi/teachers/", headers={"x-api-key": ""}).status_code == 403


def test_a_blank_configured_key_never_authorizes(client, monkeypatch):
    monkeypatch.setattr(auth_module, "API_KEY_LIST", [])
    assert client.get("/restapi/teachers/", headers={"x-api-key": ""}).status_code == 403
    assert client.get("/restapi/teachers/", headers={"x-api-key": " "}).status_code == 403


@pytest.mark.parametrize("raw", [None, "", "   ", ",", " , ,"])
def test_missing_or_empty_key_list_stops_the_start(monkeypatch, raw):
    with pytest.raises(RuntimeError, match="API_KEY_LIST"):
        config_module.parse_api_keys(raw)


def test_key_list_is_trimmed_and_blanks_dropped():
    assert config_module.parse_api_keys(" a , ,b,, ") == ["a", "b"]


def test_the_opt_out_needs_development_and_the_flag(client, monkeypatch):
    monkeypatch.setenv("ALLOW_INSECURE_DEV", "true")
    assert client.get("/restapi/teachers/").status_code == 403  # flag alone does nothing
    monkeypatch.setenv("FLASK_ENV", "production")
    assert client.get("/restapi/teachers/").status_code == 403
    monkeypatch.setenv("FLASK_ENV", "development")
    assert client.get("/restapi/teachers/").status_code == 200
    monkeypatch.setenv("ALLOW_INSECURE_DEV", "false")
    assert client.get("/restapi/teachers/").status_code == 403
    assert config_module.parse_api_keys("") == [] if config_module.insecure_dev_allowed() else True


def test_the_opt_out_lets_the_start_proceed_without_keys(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("ALLOW_INSECURE_DEV", "true")
    assert config_module.parse_api_keys("") == []


def test_logs_carry_a_fingerprint_never_the_key(client, caplog):
    caplog.set_level(logging.INFO)
    assert client.get("/restapi/teachers/", headers={"x-api-key": KEY}).status_code == 200
    assert client.get("/restapi/teachers/", headers={"x-api-key": WRONG}).status_code == 403
    assert KEY not in caplog.text and WRONG not in caplog.text
    assert auth_module.key_fingerprint(KEY) in caplog.text and auth_module.key_fingerprint(WRONG) in caplog.text
