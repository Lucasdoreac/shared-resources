"""The public catalog only reads: no route or mutation can create offers."""

import importlib
import os
import sys

import pytest

HEADERS = {"x-api-key": os.environ["API_KEY_LIST"]}  # conftest.py sets a default before anything is imported
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


def _write_rules(app):
    return sorted(
        (rule.rule, sorted(rule.methods & WRITE_METHODS))
        for rule in app.url_map.iter_rules()
        if rule.methods & WRITE_METHODS
    )


def test_no_rest_route_accepts_a_write(app):
    assert [r for r in _write_rules(app) if r[0].startswith("/restapi")] == []


def test_the_only_routes_that_accept_a_write_method_are_under_graphql(app):
    # Everything in the url_map, not only /restapi: POST on /graphql is how a query is sent,
    # and the schema below has nothing to write to.
    assert [r for r in _write_rules(app) if not r[0].startswith("/graphql")] == []


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


@pytest.mark.parametrize("path", ["/graphql/", "/graphql/graphiql"])
def test_the_schema_has_no_mutation_type(app, path):
    response = app.test_client().post(path, headers=HEADERS, json={"query": "{ __schema { mutationType { name } queryType { name } } }"})
    assert response.status_code == 200
    body = response.get_json()
    data = body.get("data", body)  # /graphql/ answers the bare data, GraphiQL wraps it
    assert data == {"__schema": {"mutationType": None, "queryType": {"name": "Query"}}}


@pytest.mark.parametrize("path", ["/graphql/", "/graphql/graphiql"])
def test_a_mutation_is_rejected_without_data(app, path):
    response = app.test_client().post(path, headers=HEADERS, json={"query": "mutation { anything { id } }"})
    body = response.get_json()
    assert body.get("errors"), "a mutation must be refused"
    assert not body.get("data")  # rejected at validation: nothing was executed
