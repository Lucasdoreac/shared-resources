import os

from flasgger import Swagger
from flask import Flask, jsonify
from mongoengine import connect
from utils import log_error_request
import threading
from backpressure.leaky_bucket_worker import start_leaky_bucket_worker
from utils import log_info_request
from utils.cache import init_cache
from .graphql import setup_graphql_routes
from .restapi import setup_rest_routes


def create_app(config_class):
    app = Flask(__name__)

    app.config.from_object(config_class)


    init_cache(app)

    # Registra as rotas REST e GraphQL
    setup_rest_routes(app)
    setup_graphql_routes(app)
    worker_thread = threading.Thread(
        target=start_leaky_bucket_worker, args=(float(os.getenv('GLOBAL_LEAK_RATE')), int(os.getenv('GLOBAL_BUCKET_SIZE')), os.getenv('GLOBAL_QUEUE_NAME')), daemon=True
    )
    worker_thread.start()

    # Configuração do Swagger
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: rule.rule.startswith('/restapi'),
                "model_filter": lambda tag: True
            }
        ],
        "swagger_ui": True,
        "specs_route": "/apidocs/"
    }
    swagger = Swagger(app, config=swagger_config, merge=True) # merge=True para mesclar a nossa config com o padrão

    # Conexão com o banco de dados
    connect(
        db=app.config['MONGO_DATABASE'],
        host=app.config['MONGO_URI'],
    )

    # Error handlers
    @app.errorhandler(400)
    @log_error_request("Bad request")
    def bad_request(error):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(401)
    @log_error_request("Unauthorized")
    def unauthorized(error):
        return jsonify({"error": "Unauthorized"}), 401

    @app.errorhandler(403)
    @log_error_request("Forbidden")
    def forbidden(error):
        return jsonify({"error": "Forbidden"}), 403

    @app.errorhandler(404)
    @log_error_request("Not Found")
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    @log_error_request("Internal Server Error")
    def internal_server_error(error):
        return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500

    @app.route("/error")
    def trigger_error():
        raise RuntimeError("This is a test error for 500 handler")



    return app

