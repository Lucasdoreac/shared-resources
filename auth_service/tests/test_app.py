import os
import uuid

from SLL_auth import create_app
from cache import cache
from mongo import MongoDBConnectionFactory


class TestConfig:
    TESTING = True
    MONGO_URI = "mongodb://localhost:27017"
    MONGO_DATABASE = "test_auth_service"


def test_health_and_cors_with_current_dependencies(monkeypatch):
    monkeypatch.setenv("REACT_APP", "http://localhost:3000")
    monkeypatch.setattr(
        MongoDBConnectionFactory, "init_app", lambda *_args, **_kwargs: None
    )
    app = create_app(TestConfig)
    client = app.test_client()

    health = client.get("/health")
    assert health.status_code == 200
    assert health.get_json() is True

    preflight = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"

    foreign = client.options(
        "/health",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "Access-Control-Allow-Origin" not in foreign.headers


def test_redis_cache_round_trip(monkeypatch):
    redis_url = os.environ.get("REDIS_URL")
    assert redis_url, "REDIS_URL must point to the isolated test Redis service"
    monkeypatch.setenv("REDIS_URL", redis_url)
    monkeypatch.setattr(
        MongoDBConnectionFactory, "init_app", lambda *_args, **_kwargs: None
    )
    app = create_app(TestConfig)
    key = f"auth-dependency-test:{uuid.uuid4()}"

    with app.app_context():
        try:
            cache.set(key, "redis-cache-round-trip", timeout=30)
            assert cache.get(key) == "redis-cache-round-trip"
        finally:
            cache.delete(key)
