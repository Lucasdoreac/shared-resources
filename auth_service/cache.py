import os
from flask_caching import Cache

cache = Cache()

def init_cache(app):
    """
    Inicializa o cache da aplicação Flask utilizando Redis.

    Args:
        app (Flask): Instância da aplicação Flask.
    """
    # Configuração do cache: usa Redis se REDIS_URL estiver definida, senao SimpleCache em memoria
    cache_type = os.getenv('CACHE_TYPE') or ('RedisCache' if os.getenv('REDIS_URL') else 'SimpleCache')
    cfg = {
        'CACHE_TYPE': cache_type,
        'CACHE_DEFAULT_TIMEOUT': 86400,
    }
    if cache_type == 'RedisCache':
        cfg['CACHE_REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        cfg['CACHE_OPTIONS'] = {
            'socket_connect_timeout': 5,
            'socket_timeout': 5,
            'retry_on_timeout': True,
        }
    app.config.update(cfg)
    cache.init_app(app)