from flask import Flask, request, jsonify
from graphene import Schema
from flask_graphql import GraphQLView


def create_app(config_class):
    app = Flask(__name__)

    app.config.from_object(config_class)

    from src.DAL import MongoDBConnectionFactory
    MongoDBConnectionFactory.init_app(app.config['MONGO_URI'], app.config['MONGO_DATABASE'])

    from .resoruce_routes import Query
    schema = Schema(query=Query)

    # GraphQL endpoint
    @app.route("/graphql", methods=["POST"])
    def graphql():
        api_key = request.headers.get('x-api-key')
        if api_key != app.config['API_KEY']:
            return jsonify({"error": "Unauthorized"}), 403

        data = request.get_json()
        result = schema.execute(data.get("query"), variables=data.get("variables"))
        return jsonify(result.data)

    # Serve GraphQL Client (GraphiQL) at '/graphiql'
    app.add_url_rule(
        "/graphiql",
        view_func=GraphQLView.as_view(
            "graphiql", schema=schema, graphiql=True
        )
    )

    return app
