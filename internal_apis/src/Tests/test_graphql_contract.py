"""Contrato GraphQL com o python-services: as 13 consultas que ele envia
(src/SLL/cluster_api/request_methods.py), sobre um conjunto fixo de dados,
comparadas com respostas gravadas no graphene 2. Rede de segurança da
migração para o graphene 3: a resposta não pode mudar.

Regravar (só se o contrato mudar de propósito): RECORD_CONTRACT=1 pytest ...
"""
import json
import os
import pathlib

import mongomock
import pytest
from graphene import Schema
from mongoengine import connect, disconnect

from BLL import ContextLoaders, Query, Mutation
from DAL import models

SNAPSHOTS = pathlib.Path(__file__).with_name("contract_snapshots.json")

# Exatamente como o python-services monta (argumentos de exemplo).
QUERIES = {
    "disciplines_por_nome": 'query{ disciplines(search: "Cálculo") { name } }',
    "disciplines_todas": "query{ disciplines { name } }",
    "periods": "query{ periods { name } }",
    "teachers_por_nome": 'query{ teachers(search: "Ana") { name id } }',
    "teachers_todos": "query{ teachers { name id } }",
    "rooms_todas": "query{ rooms{ name campus{ name id } } }",
    "offers_por_dia": "query{ offers(searchWeekday: 3, searchYear: 2026, searchSemester: 2) { room { id } period { name } } }",
    "campus": "query { campus { id name } }",
    "types_todos": "query{ types{ collection types { id name } } }",
    "types_por_colecao": 'query{ types(search: "ODS"){ collection types{ name type } } }',
    "rooms_por_nome": 'query{ rooms(search: "101") { id name campus { name } } }',
    "course_por_id": "query{ courses(courseId: 31) { id coordinator name } }",
    "teacher_por_id": 'query{ teachers(teacherId: "t1") { id email name } }',
}


@pytest.fixture
def catalog():
    connect(db="contract_db", host="mongodb://localhost", alias="default", mongo_client_class=mongomock.MongoClient)
    models.Campus(id="c1", name="Campus Sede").save()
    models.Campus(id="c2", name="Campus Norte").save()
    models.Course(id=31, code="ENF", name="ENFERMAGEM", coordinator="coord-31").save()
    models.Course(id=39, code="DES", name="DESIGN").save()
    models.Discipline(id=101, name="Cálculo I", course=[31], workload=80).save()
    models.Discipline(id=102, name="Anatomia", course=[31], workload=60).save()
    models.Period(id="p1", name="NOITE").save()
    models.Period(id="p2", name="MANHÃ").save()
    models.Room(id="r1", name="101", campus="c1").save()
    models.Room(id="r2", name="202", campus="c2").save()
    models.Teacher(id="t1", name="Ana Souza", course=[31], email="ana@udf.edu.br").save()
    models.Teacher(id="t2", name="Bruno Lima", course=[39]).save()
    models.Offer(discipline=101, period="p1", campus="c1", room="r1", teacher="t1", total_enrolled=30,
                 total_optatives_enrolled=0, year=2026, semester=2, offer_id=1, weekdays=[3]).save()
    models.Offer(discipline=102, period="p2", campus="c2", room="r2", teacher="t2", total_enrolled=20,
                 total_optatives_enrolled=0, year=2026, semester=2, offer_id=2, weekdays=[1]).save()
    models.Type(id=1, collection="ODS", types=[models.TypeDetail(id=3, name="Saúde", type="ods")]).save()
    models.Type(id=2, collection="eventTypes", types=[models.TypeDetail(id=1, name="Palestra", type="lecture")]).save()
    yield
    disconnect()


def run(query):
    result = Schema(query=Query, mutation=Mutation).execute(
        query, context_value={"loaders": {"context-loader": ContextLoaders()}})
    return {"data": result.data, "errors": [str(e) for e in (result.errors or [])]}


def test_graphql_responses_match_the_recorded_contract(catalog):
    got = {name: run(q) for name, q in QUERIES.items()}
    if os.environ.get("RECORD_CONTRACT"):
        SNAPSHOTS.write_text(json.dumps(got, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
        pytest.skip("contrato regravado")
    expected = json.loads(SNAPSHOTS.read_text())
    for name in QUERIES:
        assert got[name] == expected[name], name


def test_every_contract_query_returns_data_without_errors(catalog):
    # O conjunto de dados cobre todas as consultas: resposta vazia esconderia quebra.
    for name, q in QUERIES.items():
        res = run(q)
        assert res["errors"] == [], (name, res["errors"])
        assert any(v for v in (res["data"] or {}).values()), name
