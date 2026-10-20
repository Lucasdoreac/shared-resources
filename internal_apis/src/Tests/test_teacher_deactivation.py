"""Ciclo de desativação de professor: autorização, persistência e leitura."""
import os

os.environ.setdefault("API_KEY_LIST", "chave-de-teste")
os.environ.setdefault("MONGO_URI", "mongodb://localhost/teste")
os.environ.setdefault("MONGO_DATABASE", "teste")

import mongomock
import pytest
from mongoengine import connect, disconnect

from DAL.models import Teacher

GQL = 'mutation {{ deactivateTeacher(name: "{name}") {{ success teacher {{ id name softDeleted active }} }} }}'


@pytest.fixture(scope="module")
def app():
    import SLL
    from utils import cache as cache_module

    def simple_cache(flask_app):
        flask_app.config.update({"CACHE_TYPE": "SimpleCache"})
        cache_module.cache.init_app(flask_app)

    SLL.init_cache = simple_cache
    disconnect()  # outros módulos deixam a conexão `default` aberta
    flask_app = SLL.create_app(_config())
    disconnect()
    connect(db="deactivation", host="localhost", mongo_client_class=mongomock.MongoClient)
    return flask_app


def _config():
    from config_module import get_config
    return get_config()


@pytest.fixture()
def client(app):
    from utils.cache import cache
    Teacher.drop_collection()
    Teacher(id="T1", name="Ana Silva", course=[1], active=True).save()
    Teacher(id="T2", name="Bia Souza", course=[1], active=True).save()
    Teacher(id="T3", name="Caio Lima", course=[2], active=True).save()
    Teacher(id="T4", name="Caio Lima", course=[3], active=True).save()
    # documento legado do catálogo: sem ACTIVE nem soft_deleted
    Teacher._get_collection().insert_one({"_id": "L1", "PROFESSOR": "Legado Antigo", "COD_CURS": [9]})
    with app.app_context():
        cache.clear()
    return app.test_client()


@pytest.fixture()
def key():
    from utils.auth import API_KEY_LIST
    return {"x-api-key": API_KEY_LIST[0]}


def _names(resp):
    return sorted(d["name"] for d in resp.get_json()["data"])


def _raw(teacher_id):
    return Teacher._get_collection().find_one({"_id": teacher_id})


def test_rest_sem_chave_recusa_e_nao_grava(client):
    r = client.delete("/restapi/teachers/softdel/?teacher_name=Ana Silva")
    assert r.status_code == 403
    assert "soft_deleted" not in _raw("T1") or _raw("T1")["soft_deleted"] is None


def test_rest_chave_invalida_recusa(client):
    r = client.delete("/restapi/teachers/softdel/?teacher_name=Ana Silva", headers={"x-api-key": "errada"})
    assert r.status_code == 403
    assert not _raw("T1").get("soft_deleted")


def test_graphql_sem_chave_recusa_e_nao_grava(client):
    r = client.post("/graphql/", json={"query": GQL.format(name="Ana Silva")})
    assert r.status_code == 400
    assert not _raw("T1").get("soft_deleted")


def test_graphql_leituras_continuam_sem_chave(client):
    r = client.post("/graphql/", json={"query": "{ teachers { id name } }"})
    assert r.status_code == 200


def test_rest_com_chave_grava_ambos_os_campos(client, key):
    r = client.delete("/restapi/teachers/softdel/?teacher_name=Ana Silva", headers=key)
    assert r.status_code == 200
    raw = _raw("T1")
    assert raw["ACTIVE"] is False
    assert raw["soft_deleted"]


def test_graphql_com_chave_grava_e_retorna_estado_gravado(client, key):
    r = client.post("/graphql/", json={"query": GQL.format(name="Bia Souza")}, headers=key)
    assert r.status_code == 200, r.get_json()
    out = r.get_json()["deactivateTeacher"]
    assert out["success"] is True
    assert out["teacher"]["softDeleted"] == _raw("T2")["soft_deleted"]
    assert out["teacher"]["active"] is False
    assert _raw("T2")["ACTIVE"] is False


def test_documento_legado_sem_active_e_legivel(client):
    r = client.get("/restapi/teachers/")
    assert r.status_code == 200
    assert "Legado Antigo" in _names(r)
    entry = next(d for d in r.get_json()["data"] if d["name"] == "Legado Antigo")
    assert entry["active"] is True
    r = client.post("/graphql/", json={"query": "{ teachers { name } }"})
    assert "Legado Antigo" in [t["name"] for t in r.get_json()["teachers"]]


def test_desativado_some_das_listagens_e_cache_e_invalidado(client, key):
    assert "Ana Silva" in _names(client.get("/restapi/teachers/"))  # aquece o cache
    client.delete("/restapi/teachers/softdel/?teacher_name=Ana Silva", headers=key)
    assert "Ana Silva" not in _names(client.get("/restapi/teachers/"))
    assert client.get("/restapi/teachers/?teacher_name=Ana").status_code == 404
    r = client.post("/graphql/", json={"query": "{ teachers { name } }"})
    assert "Ana Silva" not in [t["name"] for t in r.get_json()["teachers"]]
    r = client.get("/restapi/teachers/?course_id=1")
    assert "Ana Silva" not in _names(r)


def test_busca_por_id_ainda_retorna_desativado_com_active(client, key):
    client.delete("/restapi/teachers/softdel/?teacher_name=Ana Silva", headers=key)
    r = client.get("/restapi/teachers/?teacher_id=T1")
    assert r.status_code == 200
    assert r.get_json()["name"] == "Ana Silva"
    assert r.get_json()["active"] is False
    r = client.post("/graphql/", json={"query": '{ teachers(teacherId: "T1") { name active } }'})
    assert r.get_json()["teachers"][0]["name"] == "Ana Silva"


def test_nome_ambiguo_409_sem_gravar(client, key):
    r = client.delete("/restapi/teachers/softdel/?teacher_name=Caio Lima", headers=key)
    assert r.status_code == 409
    assert not _raw("T3").get("soft_deleted") and not _raw("T4").get("soft_deleted")
    r = client.post("/graphql/", json={"query": GQL.format(name="Caio Lima")}, headers=key)
    assert r.status_code == 400
    assert not _raw("T3").get("soft_deleted")


def test_nome_inexistente_404_e_parcial_nao_casa(client, key):
    assert client.delete("/restapi/teachers/softdel/?teacher_name=Zeca", headers=key).status_code == 404
    assert client.delete("/restapi/teachers/softdel/?teacher_name=Ana", headers=key).status_code == 404
    assert not _raw("T1").get("soft_deleted")


def test_idempotente_preserva_timestamp_original(client, key):
    url = "/restapi/teachers/softdel/?teacher_name=Ana Silva"
    assert client.delete(url, headers=key).status_code == 200
    primeiro = _raw("T1")["soft_deleted"]
    assert client.delete(url, headers=key).status_code == 200
    assert _raw("T1")["soft_deleted"] == primeiro
