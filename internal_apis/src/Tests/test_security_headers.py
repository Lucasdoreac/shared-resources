import pytest
from flask import Flask, jsonify

from utils.security_headers import apply_security_headers, docs_enabled


@pytest.fixture
def client():
    app = Flask(__name__)
    app.after_request(apply_security_headers)

    @app.route("/json")
    def as_json():
        return jsonify(ok=True)

    return app.test_client()


def test_answers_carry_the_basic_headers(client):
    headers = client.get("/json").headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Referrer-Policy"] == "no-referrer"
    assert "default-src 'none'" in headers["Content-Security-Policy"]
    assert "Strict-Transport-Security" not in headers
    assert client.get("/json", headers={"X-Forwarded-Proto": "https"}).headers[
        "Strict-Transport-Security"].startswith("max-age=")


def test_docs_are_closed_by_default(monkeypatch):
    for name in ("ENABLE_API_DOCS", "FLASK_ENV", "ALLOW_INSECURE_DEV"):
        monkeypatch.delenv(name, raising=False)
    assert not docs_enabled()
    monkeypatch.setenv("ENABLE_API_DOCS", "true")
    assert docs_enabled()
