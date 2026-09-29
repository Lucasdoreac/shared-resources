import importlib

from flask import Flask


def test_graphql_endpoints_work_with_graphene_v3(monkeypatch):
    monkeypatch.setenv("API_KEY_LIST", "test-key")
    graphql_routes = importlib.import_module("SLL.graphql")

    app = Flask(__name__)
    graphql_routes.setup_graphql_routes(app)
    client = app.test_client()

    response = client.post("/graphql/", json={"query": "{ __typename }"})
    assert response.status_code == 200
    assert response.get_json() == {"__typename": "Query"}

    graphiql = client.get("/graphql/graphiql", headers={"Accept": "text/html"})
    assert graphiql.status_code == 200
    assert "GraphiQL" in graphiql.get_data(as_text=True)
