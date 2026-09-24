import mongomock
import mongoengine
import pytest

from DAL import models

KEY = "test-key"  # conftest.py: API_KEY_LIST=test-key


@pytest.fixture(scope="module")
def client():
    # create_app só pode rodar uma vez por processo (o blueprint do GraphQL
    # registra rotas no nível do módulo), então o app é do módulo inteiro.
    import SLL
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(SLL, "connect", lambda **kw: mongoengine.connect(
            db="test_db", host="mongodb://localhost", alias="default", mongo_client_class=mongomock.MongoClient))
        mp.setattr("utils.auth.API_KEY_LIST", [KEY])
        from config_module import get_config
        app = SLL.create_app(get_config())
        models.Campus(id="c1", name="Campus Sede").save()
        yield app.test_client()
        mongoengine.disconnect()


@pytest.mark.parametrize("method, path", [
    ("get", "/restapi/campus/"),
    ("get", "/restapi/teachers/"),   # dados de professores
    ("get", "/restapi/rooms/"),      # rota com cache: a checagem vem antes dele
    ("get", "/restapi/offers/"),
    ("post", "/graphql/"),
])
def test_catalog_requires_the_api_key(client, method, path):
    # Antes só o POST /offers pedia x-api-key: todo o resto (inclusive
    # professores) respondia a quem alcançasse a porta.
    kwargs = {"json": {"query": "{ campus { id } }"}} if method == "post" else {}

    assert getattr(client, method)(path, **kwargs).status_code == 403
    assert getattr(client, method)(path, headers={"x-api-key": "errada"}, **kwargs).status_code == 403


def test_valid_key_gets_the_data(client):
    rest = client.get("/restapi/campus/", headers={"x-api-key": KEY})
    graph = client.post("/graphql/", json={"query": "{ campus { id } }"}, headers={"x-api-key": KEY})

    assert rest.status_code == 200
    assert graph.status_code == 200 and graph.get_json() == {"campus": [{"id": "c1"}]}


def test_api_docs_stay_open(client):
    # Documentação não expõe dados do catálogo.
    assert client.get("/apispec.json").status_code == 200
