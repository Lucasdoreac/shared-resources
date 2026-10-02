"""API key handling: no key in logs, and reads protected on demand."""

import logging

import pytest
from flask import Flask

KEY = "test-api-key-0123456789"
WRONG = "wrong-key-typed-by-a-caller"


@pytest.fixture
def auth(monkeypatch):
    monkeypatch.setenv("API_KEY_LIST", KEY)
    from utils import auth as auth_module

    monkeypatch.setattr(auth_module, "API_KEY_LIST", [KEY])
    return auth_module


@pytest.fixture
def client(auth):
    app = Flask(__name__)
    app.before_request(auth.require_key_for_reads)

    @app.route("/restapi/teachers/")
    def teachers():
        return {"data": []}

    @app.route("/restapi/offers/", methods=["POST"])
    @auth.check_api_key
    def offers():
        return {"ok": True}

    @app.route("/graphql/", methods=["POST"])
    def graphql():
        return {"data": {}}

    @app.route("/apispec.json")
    def spec():
        return {}

    @app.route("/health")
    def health():
        return "ok"

    return app.test_client()


def test_logs_carry_a_fingerprint_never_the_key(client, caplog):
    caplog.set_level(logging.INFO)
    assert client.post("/restapi/offers/", headers={"x-api-key": KEY}).status_code == 200
    assert client.post("/restapi/offers/", headers={"x-api-key": WRONG}).status_code == 403
    assert KEY not in caplog.text and WRONG not in caplog.text
    from utils.auth import key_fingerprint

    assert key_fingerprint(KEY) in caplog.text and key_fingerprint(WRONG) in caplog.text
    assert len(key_fingerprint(KEY)) == 8


def test_reads_stay_open_by_default(client, monkeypatch):
    monkeypatch.delenv("REQUIRE_API_KEY_FOR_READS", raising=False)
    assert client.get("/restapi/teachers/").status_code == 200


@pytest.mark.parametrize("flag", ["true", "1", "yes", "TRUE"])
def test_reads_require_a_key_when_enabled(client, monkeypatch, flag):
    monkeypatch.setenv("REQUIRE_API_KEY_FOR_READS", flag)
    assert client.get("/restapi/teachers/").status_code == 403
    assert client.get("/restapi/teachers/", headers={"x-api-key": WRONG}).status_code == 403
    assert client.get("/restapi/teachers/", headers={"x-api-key": KEY}).status_code == 200
    assert client.post("/graphql/", json={}).status_code == 403
    assert client.post("/graphql/", json={}, headers={"x-api-key": KEY}).status_code == 200


def test_docs_and_health_stay_open_when_enabled(client, monkeypatch):
    monkeypatch.setenv("REQUIRE_API_KEY_FOR_READS", "true")
    assert client.get("/apispec.json").status_code == 200
    assert client.get("/health").status_code == 200
