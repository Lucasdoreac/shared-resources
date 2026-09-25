import mongomock
import pytest
from graphene import Schema
from mongoengine import connect, disconnect

from BLL import ContextLoaders, Query, Mutation
from DAL import models


@pytest.fixture
def catalog():
    connect(db="room_campus_db", host="mongodb://localhost", alias="default", mongo_client_class=mongomock.MongoClient)
    models.Campus(id="c1", name="Campus Sede").save()
    # Como a carga da planilha grava: a sala guarda o ID do campus, não o nome.
    models.Room(id="r1", name="101", campus="c1").save()
    yield
    disconnect()


def test_room_campus_is_resolved_from_the_campus_id(catalog):
    # Antes o resolver procurava o campus pelo NOME usando o ID guardado na
    # sala: nunca achava, e rooms { campus } vinha sempre null.
    result = Schema(query=Query, mutation=Mutation).execute(
        "{ rooms { name campus { id name } } }",
        context_value={"loaders": {"context-loader": ContextLoaders()}})

    assert result.errors is None
    assert result.data["rooms"] == [{"name": "101", "campus": {"id": "c1", "name": "Campus Sede"}}]
