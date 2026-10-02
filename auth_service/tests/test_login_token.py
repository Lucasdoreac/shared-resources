"""Login token: unpredictable, stored hashed, short-lived, bound to the e-mail, rate limited."""

import hashlib
import re
from datetime import datetime, timedelta

import pytest
from flask import Flask

import auth_routes
import rate_limit
from cache import cache
from controller import AuthenticationController, TOKEN_PATTERN, hash_token
from DAL_auth import AuthenticationRepository

EMAIL = "prof@udf.edu.br"


class FakeCollection:
    """The few pymongo calls the repository makes, over an in-memory list."""

    def __init__(self):
        self.docs = []
        self.counter = 0

    def insert_one(self, record):
        self.counter += 1
        record = {"_id": self.counter, **record}
        self.docs.append(record)
        return type("R", (), {"inserted_id": record["_id"]})()

    def delete_many(self, query):
        keep = []
        for doc in self.docs:
            hit = doc["email"] == query.get("email", doc["email"]) if "email" in query else True
            if "expiresAt" in query and "$lte" in query["expiresAt"]:
                hit = hit and doc["expiresAt"] <= query["expiresAt"]["$lte"]
            if "_id" in query:
                hit = doc["_id"] in query["_id"]["$in"]
            if not hit:
                keep.append(doc)
        self.docs = keep

    def find(self, query, projection=None):
        docs = [d for d in self.docs if d["email"] == query["email"]]
        if "expiresAt" in query:
            docs = [d for d in docs if d["expiresAt"] > query["expiresAt"]["$gt"]]
        if "tokenHash" in query:
            docs = [d for d in docs if "tokenHash" in d]
        return FakeCursor(docs)


class FakeCursor(list):
    def sort(self, field, direction):
        return FakeCursor(sorted(self, key=lambda d: d[field], reverse=direction < 0))

    def limit(self, n):
        return FakeCursor(self[:n])


@pytest.fixture
def collection(monkeypatch):
    fake = FakeCollection()
    monkeypatch.setattr(AuthenticationRepository, "__init__", lambda self: None)
    monkeypatch.setattr(AuthenticationRepository, "get_collection_name", lambda self: fake)
    AuthenticationController._authentication_instance = None
    return fake


@pytest.fixture
def controller(collection):
    return AuthenticationController()


@pytest.fixture(autouse=True)
def clean_limits():
    rate_limit.reset_local()


def test_tokens_are_random_urlsafe_and_distinct(controller):
    tokens = {controller.generate_token() for _ in range(200)}
    assert len(tokens) == 200
    assert all(TOKEN_PATTERN.match(t) and len(t) == 43 for t in tokens)


def test_token_is_not_derivable_from_the_clock(controller):
    token = controller.generate_token()
    now = datetime.now()
    for offset_ms in range(-2000, 2000):
        guess = hashlib.sha256(str(now + timedelta(milliseconds=offset_ms)).encode()).hexdigest()
        assert guess != token


def test_only_the_hash_is_stored_and_the_token_is_bound_to_the_email(controller, collection):
    token = controller.generate_token()
    controller.insert_token("Prof@UDF.edu.br", token)
    (record,) = collection.docs
    assert token not in str(record)
    assert record["tokenHash"] == hash_token(token) and record["email"] == EMAIL
    assert controller.is_token_valid(token, EMAIL)
    assert controller.is_token_valid(token, " PROF@udf.edu.br ")
    assert not controller.is_token_valid(token, "other@udf.edu.br")


def test_token_expires(controller, collection, monkeypatch):
    monkeypatch.setenv("AUTH_TOKEN_TTL_MINUTES", "1")
    token = controller.generate_token()
    controller.insert_token(EMAIL, token)
    assert controller.is_token_valid(token, EMAIL)
    collection.docs[0]["expiresAt"] = datetime.now() - timedelta(seconds=1)
    assert not controller.is_token_valid(token, EMAIL)


def test_old_format_tokens_are_rejected(controller, collection):
    old = hashlib.sha256(str(datetime.now()).encode()).hexdigest()
    collection.docs.append({"_id": 99, "email": EMAIL, "hash": old,
                            "expiresAt": datetime.now() + timedelta(hours=1)})
    assert not controller.is_token_valid(old, EMAIL)
    for bad in ("", None, "a" * 42, "a" * 44, "!" * 43, 12345, "a" * 43 + "\n"):
        assert not controller.is_token_valid(bad, EMAIL)


def test_few_live_tokens_per_email(controller, collection):
    for _ in range(12):
        controller.insert_token(EMAIL, controller.generate_token())
    assert len(collection.docs) <= AuthenticationRepository.MAX_ACTIVE_PER_EMAIL


# --- HTTP layer ---------------------------------------------------------------

class Sent:
    status_code = 200


@pytest.fixture
def client(monkeypatch, collection):
    sent = []
    monkeypatch.setattr(auth_routes, "send_magic_link", lambda *a: sent.append(a) or Sent())
    monkeypatch.setenv("REACT_APP", "http://front")
    for name in ("FLASK_ENV", "AUTH_DEV_RETURN_LINK", "AUTH_EMAIL_ALLOWLIST", "EMAIL_DRY_RUN"):
        monkeypatch.delenv(name, raising=False)
    app = Flask(__name__)
    app.config.update(CACHE_TYPE="SimpleCache")
    cache.init_app(app)
    app.register_blueprint(auth_routes.auth_bp)
    with app.app_context():
        cache.clear()
    test_client = app.test_client()
    test_client.sent = sent
    return test_client


def issued_token(client):
    link = client.sent[-1][2]
    return re.search(r"hash=([A-Za-z0-9_-]+)", link).group(1)


def test_login_round_trip_and_link_is_urlencoded(client):
    assert client.post("/auth/send-link?email=prof%2Bx@udf.edu.br").status_code == 201
    link = client.sent[-1][2]
    assert "email=prof%2Bx%40udf.edu.br" in link
    token = issued_token(client)
    ok = client.get(f"/auth/validate?email=prof%2Bx@udf.edu.br&token={token}")
    assert ok.status_code == 200
    assert client.get(f"/auth/validate?email=prof%2Bx@udf.edu.br&token={'A' * 43}").status_code == 403


def test_a_failed_check_is_not_cached(client):
    client.post(f"/auth/send-link?email={EMAIL}")
    token = issued_token(client)
    assert client.get(f"/auth/validate?email={EMAIL}&token={'B' * 43}").status_code == 403
    assert client.get(f"/auth/validate?email={EMAIL}&token={token}").status_code == 200


def test_send_link_is_limited_per_email(client):
    codes = [client.post(f"/auth/send-link?email={EMAIL}").status_code for _ in range(5)]
    assert codes == [201, 201, 201, 429, 429]
    assert len(client.sent) == 3
    limited = client.post(f"/auth/send-link?email={EMAIL}")
    assert limited.headers["Retry-After"] == str(rate_limit.window_seconds())
    assert client.post("/auth/send-link?email=another@udf.edu.br").status_code == 201


def test_accounts_behind_the_api_address_do_not_block_each_other(client):
    # Every user arrives from the API server's address: ordinary traffic stays under the cap.
    codes = [client.post(f"/auth/send-link?email=user{i}@udf.edu.br",
                         headers={"X-Forwarded-For": "203.0.113.9"}).status_code for i in range(60)]
    assert codes == [201] * 60


def test_send_link_is_capped_per_address(client):
    codes = [client.post(f"/auth/send-link?email=user{i}@udf.edu.br",
                         headers={"X-Forwarded-For": "203.0.113.9"}).status_code for i in range(303)]
    assert codes[:300] == [201] * 300 and codes[300:] == [429] * 3
    assert client.post("/auth/send-link?email=fresh@udf.edu.br",
                       headers={"X-Forwarded-For": "203.0.113.10"}).status_code == 201


def test_a_spoofed_leftmost_forwarded_address_does_not_reset_the_limit(client, monkeypatch):
    # The platform proxy appends the real client; entries before it are attacker supplied.
    codes = [client.post(f"/auth/send-link?email=u{i}@udf.edu.br",
                         headers={"X-Forwarded-For": f"10.0.0.{i % 250}, 198.51.100.7"}).status_code
             for i in range(303)]
    assert codes[300:] == [429] * 3


def test_validate_failures_are_limited_per_email(client):
    codes = [client.get(f"/auth/validate?email={EMAIL}&token={'C' * 43}").status_code for _ in range(33)]
    assert codes[:30] == [403] * 30 and codes[30:] == [429] * 3


def test_limits_hold_when_the_cache_backend_fails(client, monkeypatch):
    def broken(*args, **kwargs):
        raise ConnectionError("redis down")

    monkeypatch.setattr(cache, "get", broken)
    monkeypatch.setattr(cache, "set", broken)
    codes = [client.post(f"/auth/send-link?email={EMAIL}").status_code for _ in range(5)]
    assert codes == [201, 201, 201, 429, 429]
