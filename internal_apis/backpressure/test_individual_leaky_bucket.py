import time
from functools import wraps
import pika
import pytest
import fakeredis
from flask import Flask, jsonify
from backpressure.individual_leaky_bucket import LeakyBucket
from unittest.mock import patch


@pytest.mark.parametrize("configured", [None, "redis://redis:6379/4"])
def test_redis_connection_uses_the_existing_application_configuration(monkeypatch, configured):
    if configured is None:
        monkeypatch.delenv("REDIS_URL", raising=False)
    else:
        monkeypatch.setenv("REDIS_URL", configured)
    with patch("redis.Redis.from_url") as from_url:
        assert LeakyBucket.get_redis() is from_url.return_value
    from_url.assert_called_once_with(configured or "redis://localhost:6379/0")


@pytest.fixture
def fake_redis(monkeypatch):
    r = fakeredis.FakeStrictRedis(decode_responses=True)
    r.flushdb() # Limpa o redis falso antes de cada teste

    monkeypatch.setattr(LeakyBucket, "get_redis", staticmethod(lambda: r))
    return r

#substituindo o get_redis original dentro do individual_leaky_bucket.py (que pega o redis original) pela nossa funcao que pega o redis falso

@pytest.fixture()
def app(fake_redis):
    app = Flask(__name__)

    apply_leakybucket = LeakyBucket.individual_leaky_bucket(
        bucketcapacity=5,
        leakrate=0.1,
        keytimeout=10
    )

    #Configurando o leaky bucket com capacidade de 5 requisições, vazamento de 0.1 requisições por segundo e timeout de 60 segundos

    @app.route("/api/protected")
    @apply_leakybucket
    def protected():
        return jsonify({"status": "ok", "message": "Acesso Permitido"})

    return app

    # Configurando o Flask para rodar com o leaky bucket aplicado na rota /api/protected

@pytest.fixture()
def client(app):
    return app.test_client()

# utiliza o test_client() do flask para simular as requisições sem ter que envolver o servidor

def test_requests_above_limit(client):

    for i in range(5):
        request = client.get("/api/protected")
        print(f"Requisição {i + 1}: status {request.status_code}, resposta: {request.get_data(as_text=True)}")
        assert request.status_code == 200
        assert request.get_json()["status"] == "ok"

    #realiza as 5 requisições maximas e verifica se cada uma foi aceita e se em cada uma o json foi retornado corretamente

    test_request = client.get("/api/protected")
    assert test_request.status_code == 429
    assert "limit" in test_request.get_json()["message"].lower()
    print(f"Requisição 6: status {test_request.status_code}, resposta: {test_request.get_data(as_text=True)}")

    #realiza a sexta requisição e verifica se ela foi recusada, verificando também se o json foi retornado corretamente


def test_requests_below_limit(client):

    for _ in range(5):
        request = client.get("/api/protected")
        print(request.data)
        print(request.status_code)
        print(request.get_data(as_text=True))
        assert request.status_code == 200
        assert request.get_json()["status"] == "ok"

    #realiza as 5 requisições maximas e verifica se cada uma foi aceita e se em cada uma o json foi retornado corretamente

def test_n_requests(client):

    for _ in range(99):
        request = client.get("/api/protected")
        print(request.status_code)
        print(request.get_data(as_text=True))

        #Testa n requisições (teste livre sem assert)

def test_requests_leaks(client):

    for _ in range(5):
        request = client.get("/api/protected")
        print(request.status_code)
        print(request.get_data(as_text=True))
        assert request.status_code == 200
        assert request.get_json()["status"] == "ok"

    test_request = client.get("/api/protected")
    assert test_request.status_code == 429
    assert "limit" in test_request.get_json()["message"].lower()
    print(test_request.status_code)
    print(test_request.get_data(as_text=True))

    time.sleep(1.1)

    test_request2 = client.get("/api/protected")
    assert test_request2.status_code == 200
    assert test_request2.get_json()["status"] == "ok"
    print(test_request2.status_code)
    print(test_request2.get_data(as_text=True))

    #Este teste verifica se após um vazamento de 0.1 requisições por segundo, a requisição é aceita novamente após o tempo de vazamento


def test_requests_timeout(client):

    for _ in range(5):
        request = client.get("/api/protected")
        print(request.status_code)
        print(request.get_data(as_text=True))
        assert request.status_code == 200
        assert request.get_json()["status"] == "ok"

    time.sleep(11)  # Espera o timeout de 10 segundos

    for _ in range(5):
        request = client.get("/api/protected")
        print(request.status_code)
        print(request.get_data(as_text=True))
        assert request.status_code == 200
        assert request.get_json()["status"] == "ok"

    #testa o timeout de 10 segundos, realizando 5 requisições antes e 5 depois do timeout, verificando se todas foram aceitas
