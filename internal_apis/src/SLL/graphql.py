from flask import request, jsonify, Blueprint
from graphene import Schema
from graphql_server.flask.views import GraphQLView
from BLL import ContextLoaders, Query
from utils import log_info_request

graphql_bp = Blueprint('graphql', __name__, url_prefix='/graphql')

def setup_graphql_routes(app):
    schema = Schema(query=Query)

    class ReservasGraphQLView(GraphQLView):
        def get_context(self, request, response):
            return {"loaders": {"context-loader": ContextLoaders()}}

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
        view_func=ReservasGraphQLView.as_view(
            "graphiql",
            schema=schema.graphql_schema,
            graphql_ide="graphiql",
        ),
    )

    # Registra a Blueprint no aplicativo Flask
    app.register_blueprint(graphql_bp)
