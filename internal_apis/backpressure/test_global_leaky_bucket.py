import time
import pytest
import pika
import threading
from flask import Flask, jsonify
from backpressure.leaky_bucket_rabbitmq import LeakyBucketRabbitMQ
from leaky_bucket_worker import start_leaky_bucket_worker

@pytest.fixture()
def app():
    app = Flask(__name__)

    apply_leakybucket = LeakyBucketRabbitMQ.rate_limit_by_leaky_bucket(
        bucketcapacity=5, queue_name="test_queue")

    @app.route("/api/protected")
    @apply_leakybucket
    def protected():
        return jsonify({"status": "ok", "message": "Acesso Permitido"})

    return app

@pytest.fixture(autouse=True)
def start_queue(monkeypatch):
    def mock_get_queue_name(name):
        return 'test_queue'

    monkeypatch.setattr('backpressure.rabbitmq_utils.get_leakybucket_queue_name', mock_get_queue_name)

    worker_thread = threading.Thread(
        target=start_leaky_bucket_worker, args=(1, "test_queue"), daemon=True
    )
    worker_thread.start()

@pytest.fixture(autouse=True)
def clean_queue():
    credentials = pika.PlainCredentials('user', 'password')
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('rabbitmq', 5672, '/', credentials)
    )
    channel = connection.channel()
    channel.queue_delete(queue='test_queue')
    channel.queue_declare(queue='test_queue', durable=True, arguments={'x-max-length': 5})
    connection.close()


@pytest.fixture()
def client(app):
    return app.test_client()



def test_requests_above_limit(client):
    for i in range(5):
        response = client.get("/api/protected")
        assert response.status_code == 200
        assert response.get_json()["status"] == "ok"
        print(f"Requisição {i + 1}: status {response.status_code}, resposta: {response.get_data(as_text=True)}")

    # Sexta requisição deve ser bloqueada
    response = client.get("/api/protected")
    print("Requisição 6: status", response.status_code, "resposta:", response.get_data(as_text=True))
    assert response.status_code == 429
    assert "limit" in response.get_json()["message"].lower()



def test_requests_leaks(client):
    for i in range(5):
        response = client.get("/api/protected")
        assert response.status_code == 200
        print(f"Requisição {i + 1}: status {response.status_code}, resposta: {response.get_data(as_text=True)}")
    # Aguarde o vazamento de tokens
    time.sleep(1)

    # Requisição deve ser aceita novamente
    response = client.get("/api/protected")
    print(f"Requisição acima do limite do bucket porém apos o vazamento: status {response.status_code}, resposta: {response.get_data(as_text=True)}")
    assert response.status_code == 200
