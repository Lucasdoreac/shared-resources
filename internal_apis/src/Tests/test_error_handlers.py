"""Every error answers generic JSON (no stack trace, no internal detail) and is logged."""

import logging

import pytest
from flask import abort

import SLL

KEY = "test-api-key"  # conftest.py sets API_KEY_LIST=test-api-key


class TestConfig:
    TESTING = False
    MONGO_DATABASE = "contract_test"
    MONGO_URI = "mongodb://localhost:27017"


@pytest.fixture(scope="module")
def client():
    # The error handlers need neither the database nor the data routes. create_app
    # registers module-level blueprints (and test_graphql builds its own app from
    # the same blueprint), so here the connection and the route registration are
    # stubbed out and only the handlers, the key check and /health are exercised.
    names = ("connect", "setup_rest_routes", "setup_graphql_routes")
    originals = {name: getattr(SLL, name) for name in names}
    for name in names:
        setattr(SLL, name, lambda *args, **kwargs: None)
    try:
        app = SLL.create_app(TestConfig)
    finally:
        for name, original in originals.items():
            setattr(SLL, name, original)
    app.config["PROPAGATE_EXCEPTIONS"] = False
    for code in (400, 401, 403):
        app.add_url_rule(f"/__abort/{code}", f"abort_{code}", lambda code=code: abort(code))

    def boom():
        raise RuntimeError("secret internal detail /srv/app/models.py")

    app.add_url_rule("/__boom", "boom", boom)
    return app.test_client()


HEADERS = {"x-api-key": KEY}


@pytest.mark.parametrize("path, status, message", [
    ("/__abort/400", 400, "Bad request"),
    ("/__abort/401", 401, "Unauthorized"),
    ("/__abort/403", 403, "Forbidden"),
    ("/no-such-route", 404, "Resource not found"),
    ("/__boom", 500, "An unexpected error occurred. Please try again later."),
])
def test_each_error_is_generic_json(client, path, status, message):
    response = client.get(path, headers=HEADERS)
    assert response.status_code == status
    assert response.is_json
    assert response.get_json() == {"error": message}


def test_the_500_does_not_leak_the_exception_or_a_traceback(client):
    body = client.get("/__boom", headers=HEADERS).get_data(as_text=True)
    for leaked in ("Traceback", "RuntimeError", "secret internal detail", "/srv/app"):
        assert leaked not in body


@pytest.mark.parametrize("path, label", [
    ("/__abort/400", "Bad request"),
    ("/no-such-route", "Not Found"),
    ("/__boom", "Internal Server Error"),
])
def test_each_error_is_logged_at_error_level_with_the_path(client, caplog, path, label):
    with caplog.at_level(logging.ERROR):
        client.get(path, headers=HEADERS)
    lines = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    assert any(label in line and path in line for line in lines)


def test_a_wrong_method_is_json_too(client):
    response = client.post("/health", headers=HEADERS)
    assert response.status_code == 405
    assert response.is_json
    assert response.get_json() == {"error": "Method not allowed"}


def test_the_405_still_lists_the_allowed_methods(client):
    response = client.post("/health", headers=HEADERS)
    assert {m.strip() for m in response.headers["Allow"].split(",")} >= {"GET"}
