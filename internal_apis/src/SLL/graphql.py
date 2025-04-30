from flask import request, jsonify, Blueprint
from graphene import Schema
from flask_graphql import GraphQLView
from BLL import ContextLoaders, Query, Mutation
from utils import log_info_request

graphql_bp = Blueprint('graphql', __name__, url_prefix='/graphql')

def setup_graphql_routes(app):
    schema = Schema(query=Query, mutation=Mutation)

    # Endpoint do GraphQL
    @graphql_bp.route("/", methods=["POST"])
    @log_info_request
    def graphql():
        data = request.get_json()
        result = schema.execute(
            data.get("query"),
            variables=data.get("variables"),
            context_value={"loaders": {"context-loader": ContextLoaders()}},
        )
        if result.errors:
            return jsonify({"errors": [str(e) for e in result.errors]}), 400
        return jsonify(result.data)

    # Endpoint para GraphiQL
    graphql_bp.add_url_rule(
        "/graphiql",
        view_func=GraphQLView.as_view(
            "graphiql",
            schema=schema,
            graphiql=True,
            get_context=lambda: {"loaders": {"context-loader": ContextLoaders()}},
        ),
    )

    # Registra a Blueprint no aplicativo Flask
    app.register_blueprint(graphql_bp)
