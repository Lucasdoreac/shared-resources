import importlib.util
import pathlib

import graphene

SRC = pathlib.Path(__file__).resolve().parents[1]


def test_graphql_stack_is_maintained():
    # graphene 2 (2021) + graphql-core 2 + flask-graphql (última versão em
    # 2019, abandonado) + promise: pilha sem manutenção. graphene 3 usa
    # graphql-core 3; o GraphiQL passa a ser servido pelo próprio app.
    assert int(graphene.__version__.split(".")[0]) >= 3, graphene.__version__
    assert importlib.util.find_spec("flask_graphql") is None
    # `promise` ainda vem como dependência do graphene-mongo 0.4.5, mas o
    # nosso código não pode depender do modelo de DataLoader do graphene 2.
    using_promise = [str(p.relative_to(SRC)) for p in SRC.rglob("*.py")
                     if "Tests" not in p.parts and "from promise" in p.read_text(encoding="utf-8")]
    assert using_promise == []
