"""Busca de ofertas por nome (GraphQL offers(searchDiscipline/...)).

Antes cada filtro por nome pegava só a PRIMEIRA entidade que contém o texto:
buscar "Cálculo" com Cálculo I e Cálculo II trazia só as ofertas de uma delas.
A tela de ofertas do Reservas busca por esse filtro."""
import mongomock
import pytest
from graphene import Schema
from mongoengine import connect, disconnect

from BLL import ContextLoaders, Query, Mutation
from DAL import models


@pytest.fixture
def catalog():
    connect(db="search_db", host="mongodb://localhost", alias="default", mongo_client_class=mongomock.MongoClient)
    models.Campus(id="c1", name="Sede").save()
    models.Discipline(id=1, name="Cálculo I", course=[1], workload=80).save()
    models.Discipline(id=2, name="Cálculo II", course=[1], workload=80).save()
    models.Discipline(id=3, name="Anatomia", course=[1], workload=60).save()
    models.Period(id="p1", name="NOITE").save()
    models.Room(id="r1", name="101", campus="c1").save()
    models.Room(id="r2", name="102", campus="c1").save()
    models.Teacher(id="t1", name="Ana", course=[1]).save()
    for n, (disc, room) in enumerate([(1, "r1"), (2, "r2"), (3, "r1")], start=1):
        models.Offer(discipline=disc, period="p1", campus="c1", room=room, teacher="t1", total_enrolled=10,
                     total_optatives_enrolled=0, year=2026, semester=2, offer_id=n).save()
    yield
    disconnect()


def offer_ids(args):
    result = Schema(query=Query, mutation=Mutation).execute(
        f"query{{ offers({args}) {{ offerId }} }}", context_value={"loaders": {"context-loader": ContextLoaders()}})
    assert not result.errors, result.errors
    return sorted(o["offerId"] for o in result.data["offers"])


def test_discipline_search_matches_every_discipline_with_the_text(catalog):
    assert offer_ids('searchDiscipline: "cálculo"') == [1, 2]


def test_room_search_matches_every_room_with_the_text(catalog):
    assert offer_ids('searchRoom: "10"') == [1, 2, 3]


def test_search_without_match_is_empty(catalog):
    assert offer_ids('searchDiscipline: "química"') == []
