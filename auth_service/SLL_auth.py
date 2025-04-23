import os
from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger
from flask_caching import Cache

cache = Cache()

# create app
def create_app(config_class):
    """
        Cria e configura a aplicação Flask.

        Esta função realiza as seguintes tarefas:
          - Instancia a aplicação Flask.
          - Configura o Swagger para documentação da API.
          - Carrega as configurações a partir da classe de configuração fornecida.
          - Habilita o CORS na aplicação.
          - Inicializa a conexão com o MongoDB utilizando a fábrica de conexão.
          - Registra os blueprints dos endpoints (por exemplo, os endpoints de autenticação).
          - Define um endpoint de health check para monitorar se a aplicação está ativa.

        Args:
            config_class (class): Classe de configuração com os parâmetros da aplicação.

        Returns:
            Flask: Instância configurada da aplicação Flask.
    """

    app = Flask(__name__)
    swagger = Swagger(app)
    app.config.from_object(config_class)
    CORS(app)

    app.config.update({
        'CACHE_TYPE': 'RedisCache',
        'CACHE_DEFAULT_TIMEOUT': 86400,
        'CACHE_REDIS_URL': os.getenv('REDIS_URL','redis://localhost:6379/0'),
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

    from mongo import MongoDBConnectionFactory
    # Load MongoDB Factory
    MongoDBConnectionFactory.init_app(app.config['MONGO_URI'], app.config['MONGO_DATABASE'])

    from auth_routes import auth_bp

    # Blueprints register
    app.register_blueprint(auth_bp)

    # Health check
    @app.route('/health', methods=['GET'])
    def health():
        """
                Endpoint de Health Check.

                Este endpoint retorna um valor booleano para indicar que a aplicação está ativa.

                Returns:
                    JSON: Um JSON contendo True, indicando que o serviço está funcionando.
        """

        return jsonify(True)

    return app
