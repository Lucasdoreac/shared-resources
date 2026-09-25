from flask import request, jsonify, Blueprint
from graphene import Schema
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

    # Página do GraphiQL (só a interface; sem dados). Fica fora de /graphql, que
    # exige x-api-key: o navegador não manda o header ao abrir a página. As
    # consultas feitas nela vão para /graphql/ e precisam da chave, informada no
    # painel "Headers" do GraphiQL: {"x-api-key": "<chave>"}.
    @app.route("/graphiql")
    def graphiql():
        return GRAPHIQL_HTML

    # Registra a Blueprint no aplicativo Flask
    app.register_blueprint(graphql_bp)


GRAPHIQL_HTML = """<!doctype html>
<html lang="pt-br"><head><meta charset="utf-8"><title>GraphiQL — catálogo LabTech</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/graphiql@3.8.3/graphiql.min.css"></head>
<body style="margin:0;height:100vh"><div id="graphiql" style="height:100vh"></div>
<script crossorigin src="https://cdn.jsdelivr.net/npm/react@18.3.1/umd/react.production.min.js"></script>
<script crossorigin src="https://cdn.jsdelivr.net/npm/react-dom@18.3.1/umd/react-dom.production.min.js"></script>
<script crossorigin src="https://cdn.jsdelivr.net/npm/graphiql@3.8.3/graphiql.min.js"></script>
<script>
  const fetcher = GraphiQL.createFetcher({ url: "/graphql/" });
  ReactDOM.createRoot(document.getElementById("graphiql")).render(
    React.createElement(GraphiQL, { fetcher, defaultHeaders: '{"x-api-key": ""}', headerEditorEnabled: true }));
</script></body></html>"""
