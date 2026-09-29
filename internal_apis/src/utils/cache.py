import os
from flask_caching import Cache

cache = Cache()

def init_cache(app):
    """
    Inicializa o cache da aplicação Flask utilizando Redis.

    Args:
        app (Flask): Instância da aplicação Flask.
    """
    # Configuração do cache
    app.config.update({
            'CACHE_TYPE': 'RedisCache',
            'CACHE_DEFAULT_TIMEOUT': 86400,
            'CACHE_REDIS_URL': os.getenv('REDIS_URL','redis://localhost:6379/0'),
            'CACHE_KEY_PREFIX': os.getenv('CACHE_KEY_PREFIX', 'flask_cache_'),
            'CACHE_OPTIONS': {
                'socket_connect_timeout': 5,
                'socket_timeout': 5,
                'retry_on_timeout': True,
            }
            # se preferir, pode usar host/port/db separados:
            # 'CACHE_REDIS_HOST': os.getenv('REDIS_HOST', 'localhost'),
            # 'CACHE_REDIS_PORT': os.getenv('REDIS_PORT', 6379),
            # 'CACHE_REDIS_DB': os.getenv('REDIS_DB', 0),
    })
    cache.init_app(app)
