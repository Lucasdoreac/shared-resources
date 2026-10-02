import os
from flask_caching import Cache

cache = Cache()


def init_cache(app):
    """
    Inicializa o cache da aplicação Flask.

    Usa Redis quando REDIS_URL (ou CACHE_TYPE=RedisCache) está definida; sem
    Redis, como em Production, usa SimpleCache em memória, por processo. Antes o
    padrão era sempre Redis em localhost, e sem ele toda requisição falhava.
    """
    cache_type = os.getenv('CACHE_TYPE') or ('RedisCache' if os.getenv('REDIS_URL') else 'SimpleCache')
    cfg = {
        'CACHE_TYPE': cache_type,
        'CACHE_DEFAULT_TIMEOUT': 86400,
    }
    if cache_type == 'SimpleCache':
        # The default of 500 keys is too small: beyond it entries are pruned, resetting
        # rate-limit counters. A cap is still needed because keys come from clients.
        # Memory: a counter is a key of at most ~350 bytes (e-mail <= 254 chars) plus
        # ~150 of cache overhead, so 20000 keys stay near 10 MB in the worst case. Each
        # failing address uses 2 keys, so ~10000 distinct addresses fit in one window.
        cfg['CACHE_THRESHOLD'] = 20000
    if cache_type == 'RedisCache':
        cfg['CACHE_REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        cfg['CACHE_OPTIONS'] = {
            'socket_connect_timeout': 5,
            'socket_timeout': 5,
            'retry_on_timeout': True,
        }
    app.config.update(cfg)
    cache.init_app(app)
