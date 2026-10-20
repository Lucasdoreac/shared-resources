from unittest.mock import patch


def test_http_factory_does_not_start_a_background_consumer(monkeypatch):
    monkeypatch.setenv("API_KEY_LIST", "isolated-test-key")
    monkeypatch.setenv("MONGO_DATABASE", "isolated-test")
    monkeypatch.setenv("MONGO_URI", "mongodb://127.0.0.1:27017/isolated-test")
    monkeypatch.setenv("GLOBAL_BUCKET_SIZE", "5")
    monkeypatch.setenv("GLOBAL_QUEUE_NAME", "isolated-test")
    monkeypatch.setenv("GLOBAL_LEAK_RATE", "1")

    import SLL
    from config_module import get_config
    from utils.cache import cache

    def isolated_cache(app):
        cache.init_app(app, config={"CACHE_TYPE": "SimpleCache"})

    with patch.object(SLL, "connect"), patch.object(SLL, "init_cache", isolated_cache), \
            patch("threading.Thread.start") as thread_start:
        app = SLL.create_app(get_config())

    thread_start.assert_not_called()
    assert "/graphql/" in {rule.rule for rule in app.url_map.iter_rules()}
