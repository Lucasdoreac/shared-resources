import time
from functools import wraps
import pika
import pytest
import fakeredis
from flask import Flask, jsonify
from backpressure.individual_leaky_bucket import LeakyBucket


def mock_token_required_for_leaky_bucket(f):
    @wraps(f)
    def decorated_mock(*args, **kwargs):
        # print(f"MOCK_TOKEN_REQUIRED para {f.__name__} EXECUTADO")
        # Simula que o token é válido. Se sua rota/lógica dentro do LeakyBucket
        # depende de algo como g.user injetado pelo token_required real,
        # você precisaria simular isso aqui.
        # Ex:
        # from flask import g
        # token_no_header = request.headers.get('token')
        # g.user = {"id": token_no_header if token_no_header else "mock_user_id"}
        return f(*args, **kwargs)
    return decorated_mock

#@pytest.fixture(autouse=True)
#def patch_internal_token_required(monkeypatch):
    # Ajuste este caminho para como 'token_required' é importado em 'individual_leaky_bucket.py'
    # Caminho comum se 'individual_leaky_bucket.py' faz: from auth_service.auth_routes import token_required
    #target_path = "backpressure.leaky_bucket.token_required"
    #try:
       # monkeypatch.setattr(target_path, mock_token_required_for_leaky_bucket)
        # print(f"Monkeypatch de '{target_path}' aplicado.")
    #except AttributeError:
        # print(f"Falha ao aplicar monkeypatch em '{target_path}'. Tentando caminho alternativo...")
        # Caminho comum se 'individual_leaky_bucket.py' importa 'auth_service.auth_routes' e usa
        # @auth_service.auth_routes.token_required
        # Ou se o token_required está diretamente no módulo auth_routes e é importado
        #alternative_target_path = "auth_service.auth_routes.token_required"
        #try:
         #   monkeypatch.setattr(alternative_target_path, mock_token_required_for_leaky_bucket)
            # print(f"Monkeypatch de '{alternative_target_path}' aplicado.")
       # except AttributeError as e:
       #     print(f"ERRO: Falha ao aplicar monkeypatch para token_required em ambos os caminhos: {target_path}, {alternative_target_path}. Detalhes: {e}")
       #     print("Os testes podem falhar ou dar erro 500 se o token_required real for chamado e falhar.")

#bypass do token_required para o teste com o objetivo de acelerar e simplificar a execução dos testes


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