from flasgger import Swagger
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from mongoengine import connect
from utils import AppLogger, LogType, Logmessage, log_error_request
from utils.auth import require_api_key_on_catalog
from utils.security_headers import apply_security_headers, docs_enabled
from utils.cache import init_cache
from .graphql import setup_graphql_routes
from .restapi import setup_rest_routes

def create_app(config_class):
    app = Flask(__name__)
    app.config.from_object(config_class)

    init_cache(app)
    app.before_request(require_api_key_on_catalog)

    # Registra as rotas REST e GraphQL
    setup_rest_routes(app)
    setup_graphql_routes(app)

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
    if docs_enabled():
        Swagger(app, config=swagger_config, merge=True) # merge=True para mesclar a nossa config com o padrão
    app.after_request(apply_security_headers)

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

    @app.errorhandler(405)
    @log_error_request("Method not allowed")
    def method_not_allowed(error):
        response = jsonify({"error": "Method not allowed"})
        response.status_code = 405
        allow = error.get_response().headers.get("Allow")  # RFC 9110: a 405 must list the allowed methods
        if allow:
            response.headers["Allow"] = allow
        return response

    @app.errorhandler(500)
    @log_error_request("Internal Server Error")
    def internal_server_error(error):
        return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500

    @app.errorhandler(HTTPException)
    def http_error(error):
        # Any other HTTP error (413, 415, 422, 429, ...) answers JSON as well. The
        # specific handlers above win for their codes; redirects pass through.
        if error.code is None or error.code < 400:
            return error
        AppLogger.log(
            Logmessage.ERROR,
            LogType.ERROR,
            error_message=f"HTTP {error.code} {error.name}",
            ip_address=request.remote_addr,
            request_method=request.method,
            request_path=request.path,
        )
        response = jsonify({"error": error.name})  # the standard status name, never request data
        response.status_code = error.code
        for name, value in error.get_response().headers:  # Allow, Retry-After, ...
            if name.lower() not in ("content-type", "content-length"):
                response.headers[name] = value
        return response

    @app.route("/health")
    def health():
        return jsonify(True), 200


    return app
