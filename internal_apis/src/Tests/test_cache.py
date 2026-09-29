from flask import Flask


def test_cache_key_prefix_is_configurable(monkeypatch):
    prefix = "reservas-staging-catalog-2026-2"
    monkeypatch.setenv("CACHE_KEY_PREFIX", prefix)
    # Importing utils.cache also loads the package's API settings module.
    monkeypatch.setenv("API_KEY_LIST", "test-api-key")
    from utils.cache import init_cache

    app = Flask(__name__)

    init_cache(app)

    assert app.config["CACHE_KEY_PREFIX"] == prefix
