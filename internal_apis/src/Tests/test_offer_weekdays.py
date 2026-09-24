import os

# utils/auth.py lê API_KEY_LIST na importação; o container de teste não tem .env.
os.environ.setdefault("API_KEY_LIST", "test-key")

import pytest
import mongomock
from flask import Flask
from graphene import Schema
from mongoengine import connect, disconnect

from BLL import ContextLoaders, Query, Mutation
from DAL import models
from SLL.offers_routes import offers_bp

API_KEY = "test-key"


@pytest.fixture
def catalog():
    connect(db="test_db", host="mongodb://localhost", alias="default", mongo_client_class=mongomock.MongoClient)
    models.Campus(id="c1", name="Campus Sede").save()
    models.Discipline(id=101, name="Cálculo I", course=[1], workload=80).save()
    models.Period(id="p1", name="NOITE").save()
    models.Room(id="r1", name="101", campus="c1").save()
    models.Teacher(id="t1", name="Prof. A", course=[1]).save()
    yield
    disconnect()


@pytest.fixture
def client(catalog, monkeypatch):
    monkeypatch.setattr("utils.auth.API_KEY_LIST", [API_KEY])
    app = Flask(__name__)
    app.register_blueprint(offers_bp, url_prefix="/restapi/offers")
    return app.test_client()


def offer_payload(**extra):
    payload = {
        "campus": "c1", "discipline": 101, "period": "p1", "room": "r1",
        "teacher": "t1", "total_enrolled": 30, "offer_id": 9001,
    }
    payload.update(extra)
    return payload


def test_post_offer_stores_weekdays_and_get_filters_by_weekday(client):
    # Sem dia da semana na oferta, o Reservas não sabe quando a aula ocupa
    # a sala (python-services #29). O dia vem do calendário acadêmico.
    created = client.post("/restapi/offers/", json=offer_payload(weekdays=[1, 3]),
                          headers={"x-api-key": API_KEY})
    assert created.status_code == 201

    wednesday = client.get("/restapi/offers/?weekday=3").get_json()["data"]
    assert [o["offer_id"] for o in wednesday] == [9001]
    assert wednesday[0]["weekdays"] == [1, 3]

    assert client.get("/restapi/offers/?weekday=2").status_code == 404


def test_post_offer_without_weekdays_keeps_working(client):
    created = client.post("/restapi/offers/", json=offer_payload(),
                          headers={"x-api-key": API_KEY})
    assert created.status_code == 201
    assert client.get("/restapi/offers/").get_json()["data"][0]["weekdays"] == []


@pytest.mark.parametrize("weekdays", [[0], [8], ["segunda"], 3])
def test_post_offer_rejects_invalid_weekdays(client, weekdays):
    response = client.post("/restapi/offers/", json=offer_payload(weekdays=weekdays),
                           headers={"x-api-key": API_KEY})
    assert response.status_code == 400
    assert models.Offer.objects.count() == 0


def test_graphql_offers_filter_by_weekday(catalog):
    models.Offer(discipline=101, period="p1", campus="c1", room="r1", teacher="t1",
                 total_enrolled=30, total_optatives_enrolled=0, year=2026, semester=2,
                 offer_id=1, weekdays=[2]).save()
    models.Offer(discipline=101, period="p1", campus="c1", room="r1", teacher="t1",
                 total_enrolled=30, total_optatives_enrolled=0, year=2026, semester=2,
                 offer_id=2, weekdays=[4]).save()

    result = Schema(query=Query, mutation=Mutation).execute(
        "{ offers(searchWeekday: 2, searchYear: 2026, searchSemester: 2) "
        "{ offerId weekdays room { id } period { name } } }",
        context_value={"loaders": {"context-loader": ContextLoaders()}},
    )

    assert result.errors is None
    assert result.data["offers"] == [
        {"offerId": 1, "weekdays": [2], "room": {"id": "r1"}, "period": {"name": "NOITE"}}
    ]
