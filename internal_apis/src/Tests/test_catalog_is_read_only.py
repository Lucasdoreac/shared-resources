"""The public catalog only reads: no route or mutation can create offers."""

import importlib
import sys

import pytest

HEADERS = {"x-api-key": "test-api-key"}
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class TestConfig:
    TESTING = True
    CACHE_TYPE = "NullCache"
    MONGO_DATABASE = "readonly_test"
    MONGO_URI = "mongodb://localhost/readonly_test"


def _drop_sll_modules():
    for name in [m for m in sys.modules if m == "SLL" or m.startswith("SLL.")]:
        del sys.modules[name]


@pytest.fixture(scope="module")
def app():
    # A blueprint cannot gain routes after it was registered on an app, and test_graphql.py
    # registers the same module-level blueprints on its own app. So this module builds its app
    # from a fresh import of SLL and drops it afterwards, leaving the others a clean import.
    # The database connection is stubbed because no route here needs a live Mongo.
    _drop_sll_modules()
    sll = importlib.import_module("SLL")
    sll.connect = lambda *args, **kwargs: None
    try:
        yield sll.create_app(TestConfig)
    finally:
        _drop_sll_modules()


def test_no_data_route_accepts_a_write_except_the_graphql_endpoint(app):
    offenders = sorted(
        f"{rule.rule} {sorted(rule.methods & WRITE_METHODS)}"
        for rule in app.url_map.iter_rules()
        if rule.rule.startswith("/restapi") and rule.methods & WRITE_METHODS
    )
    assert offenders == []


def test_posting_an_offer_is_refused(app):
    response = app.test_client().post("/restapi/offers/", json={"discipline": 1}, headers=HEADERS)
    assert response.status_code == 405


def test_graphql_has_no_mutation_type(app):
    response = app.test_client().post(
        "/graphql/", headers=HEADERS,
        json={"query": "mutation { createOffer(offerData: {discipline: 1, period: \"p\", campus: \"c\", room: \"r\", teacher: \"t\", totalEnrolled: 1, totalOptativesEnrolled: 0, year: 2026, semester: 1, offerId: 1}) { offer { offerId } } }"})
    body = response.get_json()
    assert body.get("errors"), "createOffer must not exist in the schema"
    assert body.get("data") is None  # rejected at validation: nothing was executed
