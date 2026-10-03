from flask import Flask


def test_cache_key_prefix_is_configurable(monkeypatch):
    prefix = "reservas-staging-catalog-2026-2"
    monkeypatch.setenv("CACHE_KEY_PREFIX", prefix)
    # Importing utils.cache also loads the package's API settings module.
    monkeypatch.setenv("API_KEY_LIST", "test-api-key-0123456789-abcdef")
    from utils.cache import init_cache

    app = Flask(__name__)

    init_cache(app)

    assert app.config["CACHE_KEY_PREFIX"] == prefix


def test_without_redis_the_cache_is_in_memory(monkeypatch):
    # Production has no Redis: the old default (Redis on localhost) failed every cached route.
    monkeypatch.setenv("API_KEY_LIST", "test-api-key-0123456789-abcdef")
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("CACHE_TYPE", raising=False)
    from utils.cache import init_cache

    app = Flask(__name__)
    init_cache(app)

    assert app.config["CACHE_TYPE"] == "SimpleCache"


def test_with_a_redis_url_the_cache_is_redis(monkeypatch):
    monkeypatch.setenv("API_KEY_LIST", "test-api-key-0123456789-abcdef")
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/0")
    monkeypatch.delenv("CACHE_TYPE", raising=False)
    from utils.cache import init_cache

    app = Flask(__name__)
    init_cache(app)

    assert app.config["CACHE_TYPE"] == "RedisCache"
