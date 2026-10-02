"""Login token: unpredictable, stored hashed, short-lived, bound to the e-mail, rate limited."""

import hashlib
import re
from datetime import datetime, timedelta

import pytest
from flask import Flask

import auth_routes
import rate_limit
from cache import cache, init_cache
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

    def _match(self, doc, query):
        for key, cond in query.items():
            if key == "_id" and isinstance(cond, dict):
                if doc["_id"] not in cond["$in"]:
                    return False
            elif key == "expiresAt" and isinstance(cond, dict):
                if "$lte" in cond and not doc["expiresAt"] <= cond["$lte"]:
                    return False
                if "$gt" in cond and not doc["expiresAt"] > cond["$gt"]:
                    return False
            elif doc.get(key) != cond:
                return False
        return True

    def delete_many(self, query):
        self.docs = [d for d in self.docs if not self._match(d, query)]

    def delete_one(self, query):
        for doc in self.docs:
            if self._match(doc, query):
                self.docs.remove(doc)
                return type("R", (), {"deleted_count": 1})()
        return type("R", (), {"deleted_count": 0})()

    def find(self, query, projection=None):
        return FakeCursor([d for d in self.docs if self._match(d, query)])


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


def test_only_the_hash_is_stored_and_the_link_is_bound_to_the_email(controller, collection):
    token = controller.generate_token()
    controller.insert_token("Prof@UDF.edu.br", token)
    (record,) = collection.docs
    assert token not in str(record)
    assert record["tokenHash"] == hash_token(token) and record["email"] == EMAIL and record["kind"] == "link"
    assert controller.exchange_link_token(token, "other@udf.edu.br") is None
    assert controller.exchange_link_token(token, " PROF@udf.edu.br ") is not None


def test_a_link_token_is_not_a_session(controller):
    token = controller.generate_token()
    controller.insert_token(EMAIL, token)
    assert not controller.is_token_valid(token, EMAIL)


def test_the_link_is_single_use(controller, collection):
    token = controller.generate_token()
    controller.insert_token(EMAIL, token)
    session = controller.exchange_link_token(token, EMAIL)
    assert session and TOKEN_PATTERN.fullmatch(session) and session != token
    assert controller.is_token_valid(session, EMAIL)
    assert not controller.is_token_valid(session, "other@udf.edu.br")
    assert controller.exchange_link_token(token, EMAIL) is None  # already used
    assert [d["kind"] for d in collection.docs] == ["session"]
    assert session not in str(collection.docs)


def test_two_simultaneous_exchanges_cannot_both_win(controller, collection, monkeypatch):
    token = controller.generate_token()
    controller.insert_token(EMAIL, token)
    repo = controller.tokens_repository
    real = repo._matching_record
    monkeypatch.setattr(repo, "_matching_record", lambda *a, **k: real(*a, **k) or None)
    first = repo.consume_authentication(EMAIL, hash_token(token), "link")
    # a second caller that already saw the record before the first delete
    stale = {"_id": 1, "tokenHash": hash_token(token)}
    monkeypatch.setattr(repo, "_matching_record", lambda *a, **k: stale)
    second = repo.consume_authentication(EMAIL, hash_token(token), "link")
    assert first is True and second is False


def test_the_link_expires_quickly_and_the_session_later(controller, collection, monkeypatch):
    monkeypatch.setenv("AUTH_LINK_TTL_MINUTES", "1")
    monkeypatch.setenv("AUTH_SESSION_TTL_MINUTES", "60")
    token = controller.generate_token()
    controller.insert_token(EMAIL, token)
    assert collection.docs[0]["expiresAt"] - collection.docs[0]["createdAt"] <= timedelta(minutes=1, seconds=1)
    session = controller.exchange_link_token(token, EMAIL)
    assert controller.is_token_valid(session, EMAIL)
    collection.docs[0]["expiresAt"] = datetime.now() - timedelta(seconds=1)
    assert not controller.is_token_valid(session, EMAIL)
    late = controller.generate_token()
    controller.insert_token(EMAIL, late)
    collection.docs[-1]["expiresAt"] = datetime.now() - timedelta(seconds=1)
    assert controller.exchange_link_token(late, EMAIL) is None


def test_old_format_records_are_rejected(controller, collection):
    old = hashlib.sha256(str(datetime.now()).encode()).hexdigest()
    collection.docs.append({"_id": 99, "email": EMAIL, "hash": old,
                            "expiresAt": datetime.now() + timedelta(hours=1)})
    assert not controller.is_token_valid(old, EMAIL)
    assert controller.exchange_link_token(old, EMAIL) is None
    previous = controller.generate_token()  # issued before the link/session split: no "kind"
    collection.docs.append({"_id": 100, "email": EMAIL, "tokenHash": hash_token(previous),
                            "expiresAt": datetime.now() + timedelta(hours=1)})
    assert not controller.is_token_valid(previous, EMAIL)
    assert controller.exchange_link_token(previous, EMAIL) is None
    for bad in ("", None, "a" * 42, "a" * 44, "!" * 43, 12345, "a" * 43 + "\n"):
        assert not controller.is_token_valid(bad, EMAIL)
        assert controller.exchange_link_token(bad, EMAIL) is None


def test_few_live_tokens_per_email_and_kind(controller, collection):
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
    for name in ("FLASK_ENV", "AUTH_DEV_RETURN_LINK", "AUTH_EMAIL_ALLOWLIST", "EMAIL_DRY_RUN",
                 "CACHE_TYPE", "REDIS_URL"):
        monkeypatch.delenv(name, raising=False)
    app = Flask(__name__)
    init_cache(app)  # the cache as Production has it: in-memory, no Redis
    app.register_blueprint(auth_routes.auth_bp)
    with app.app_context():
        cache.clear()
    test_client = app.test_client()
    test_client.sent = sent
    return test_client


def issued_token(client):
    link = client.sent[-1][2]
    return re.search(r"hash=([A-Za-z0-9_-]+)", link).group(1)


def exchange(client, token, email=EMAIL):
    return client.post("/auth/exchange", json={"email": email, "token": token})


def test_login_round_trip_exchanges_the_link_once(client):
    assert client.post("/auth/send-link?email=prof%2Bx@udf.edu.br").status_code == 201
    assert "email=prof%2Bx%40udf.edu.br" in client.sent[-1][2]
    link = issued_token(client)
    # the link is not a session
    assert client.get(f"/auth/validate?email=prof%2Bx@udf.edu.br&token={link}").status_code == 403
    first = exchange(client, link, "prof+x@udf.edu.br")
    assert first.status_code == 200
    session = first.get_json()["token"]
    assert session != link
    assert client.get(f"/auth/validate?email=prof%2Bx@udf.edu.br&token={session}").status_code == 200
    assert exchange(client, link, "prof+x@udf.edu.br").status_code == 403  # single use
    assert client.get(f"/auth/validate?email=prof%2Bx@udf.edu.br&token={'A' * 43}").status_code == 403


def test_exchange_rejects_bad_requests_and_is_rate_limited(client):
    client.post(f"/auth/send-link?email={EMAIL}")
    link = issued_token(client)
    assert exchange(client, link, "other@udf.edu.br").status_code == 403
    assert client.post("/auth/exchange", data="not json").status_code == 403
    assert client.post("/auth/exchange", json={"email": EMAIL}).status_code == 403
    codes = [exchange(client, "B" * 43).status_code for _ in range(33)]
    assert codes[-1] == 429


def test_a_failed_check_is_not_cached(client):
    client.post(f"/auth/send-link?email={EMAIL}")
    link = issued_token(client)
    session = exchange(client, link).get_json()["token"]
    assert client.get(f"/auth/validate?email={EMAIL}&token={'B' * 43}").status_code == 403
    assert client.get(f"/auth/validate?email={EMAIL}&token={session}").status_code == 200


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


# --- limits per person behind the API ---------------------------------------------------

FORWARD_KEY = "forward-key-for-tests"


def forwarded(client_ip, key=FORWARD_KEY, via="203.0.113.9"):
    # via = the API's address as the platform proxy sees it; client_ip = the person behind it
    headers = {"X-Forwarded-For": via, "X-Client-IP": client_ip}
    if key is not None:
        headers["X-Forward-Key"] = key
    return headers


@pytest.fixture
def behind_the_api(monkeypatch):
    monkeypatch.setenv("AUTH_FORWARD_KEY", FORWARD_KEY)


def test_a_stranger_cannot_lock_out_someone_elses_validation(client, behind_the_api):
    client.post(f"/auth/send-link?email={EMAIL}", headers=forwarded("198.51.100.20"))
    session = exchange(client, issued_token(client)).get_json()["token"]
    codes = [client.get(f"/auth/validate?email={EMAIL}&token={'C' * 43}",
                        headers=forwarded("198.51.100.99")).status_code for _ in range(33)]
    assert codes[:30] == [403] * 30 and codes[30:] == [429] * 3  # the attacker is limited...
    ok = client.get(f"/auth/validate?email={EMAIL}&token={session}", headers=forwarded("198.51.100.20"))
    assert ok.status_code == 200  # ...the owner is not


def test_a_stranger_cannot_spend_someone_elses_link_quota(client, behind_the_api):
    codes = [client.post(f"/auth/send-link?email={EMAIL}", headers=forwarded("198.51.100.99")).status_code
             for _ in range(5)]
    assert codes == [201, 201, 201, 429, 429]
    assert client.post(f"/auth/send-link?email={EMAIL}", headers=forwarded("198.51.100.20")).status_code == 201


def test_one_inbox_is_still_capped_across_many_clients(client, behind_the_api):
    codes = [client.post(f"/auth/send-link?email={EMAIL}", headers=forwarded(f"198.51.100.{i}")).status_code
             for i in range(1, 13)]
    assert codes[:10] == [201] * 10 and codes[10:] == [429] * 2


def test_spraying_one_address_from_many_clients_hits_the_ceiling(client, behind_the_api):
    for i in range(1, 12):  # 11 clients x 30 failures > 300
        for _ in range(30):
            client.get(f"/auth/validate?email={EMAIL}&token={'D' * 43}", headers=forwarded(f"198.51.100.{i}"))
    fresh = client.get(f"/auth/validate?email={EMAIL}&token={'D' * 43}", headers=forwarded("198.51.100.200"))
    assert fresh.status_code == 429


def test_exchange_failures_are_counted_per_client_too(client, behind_the_api):
    for _ in range(30):
        exchange(client, "F" * 43)  # without the proof header: counted under the connecting address
    assert exchange(client, "F" * 43).status_code == 429
    attacker = {"headers": forwarded("198.51.100.99")}
    victim = {"headers": forwarded("198.51.100.20")}
    for _ in range(30):
        client.post("/auth/exchange", json={"email": "other@udf.edu.br", "token": "F" * 43}, **attacker)
    assert client.post("/auth/exchange", json={"email": "other@udf.edu.br", "token": "F" * 43}, **attacker).status_code == 429
    assert client.post("/auth/exchange", json={"email": "other@udf.edu.br", "token": "F" * 43}, **victim).status_code == 403


def test_one_client_inventing_many_emails_hits_its_own_ceiling(client, behind_the_api):
    codes = [client.get(f"/auth/validate?email=u{i}@udf.edu.br&token={'G' * 43}",
                        headers=forwarded("198.51.100.99")).status_code for i in range(303)]
    assert codes[:300] == [403] * 300 and codes[300:] == [429] * 3
    other = client.get(f"/auth/validate?email=v1@udf.edu.br&token={'G' * 43}", headers=forwarded("198.51.100.20"))
    assert other.status_code == 403  # another person is untouched


def test_without_proof_failures_do_not_block_everyone_behind_the_api(client):
    # every caller shares the API's address: a per-address ceiling would let one attacker block all
    codes = [client.get(f"/auth/validate?email=u{i}@udf.edu.br&token={'G' * 43}",
                        headers={"X-Forwarded-For": "203.0.113.9"}).status_code for i in range(330)]
    assert set(codes) == {403}


def test_the_coarse_send_ceiling_stays_on_the_connecting_address(client, behind_the_api):
    codes = [client.post(f"/auth/send-link?email=user{i}@udf.edu.br",
                         headers=forwarded(f"198.51.100.{i % 250}")).status_code for i in range(303)]
    assert codes[:300] == [201] * 300 and codes[300:] == [429] * 3


@pytest.mark.parametrize("key", [None, "wrong-key"])
def test_the_forwarded_address_is_ignored_without_the_proof(client, behind_the_api, key):
    # an attacker calling Auth directly cannot pose as the victim's address
    victim = "198.51.100.20"
    for _ in range(35):
        client.get(f"/auth/validate?email={EMAIL}&token={'E' * 43}",
                   headers=forwarded(victim, key=key, via="198.51.100.77"))
    # counted under the attacker's own connecting address (198.51.100.77), so the victim is untouched
    assert client.get(f"/auth/validate?email={EMAIL}&token={'E' * 43}",
                      headers=forwarded(victim, via="203.0.113.9")).status_code == 403


def test_without_the_secret_nothing_changes(client):
    codes = [client.get(f"/auth/validate?email={EMAIL}&token={'C' * 43}",
                        headers={"X-Forwarded-For": "203.0.113.9", "X-Client-IP": f"198.51.100.{i}"}).status_code
             for i in range(33)]
    assert codes[:30] == [403] * 30 and codes[30:] == [429] * 3  # one bucket per address, as before


# --- headers and docs -----------------------------------------------------------------

def make_app(monkeypatch, **env):
    from SLL_auth import create_app
    from mongo import MongoDBConnectionFactory

    for name in ("ENABLE_API_DOCS", "FLASK_ENV", "ALLOW_INSECURE_DEV"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(MongoDBConnectionFactory, "init_app", lambda *a, **k: None)

    class Config:
        TESTING = True
        MONGO_URI = "mongodb://localhost:27017"
        MONGO_DATABASE = "t"

    return create_app(Config).test_client()


def test_answers_carry_security_headers_and_docs_are_closed(monkeypatch):
    client = make_app(monkeypatch)
    health = client.get("/health")
    assert health.headers["X-Content-Type-Options"] == "nosniff"
    assert health.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'none'" in health.headers["Content-Security-Policy"]
    assert client.get("/apidocs/").status_code == 404
    assert client.get("/apispec_1.json").status_code == 404


def test_docs_open_only_when_enabled(monkeypatch):
    client = make_app(monkeypatch, ENABLE_API_DOCS="true")
    assert client.get("/apispec_1.json").status_code == 200


# --- cache backend --------------------------------------------------------------------

def cache_config(monkeypatch, **env):
    from flask import Flask

    from cache import init_cache

    for name in ("CACHE_TYPE", "REDIS_URL"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    app = Flask(__name__)
    init_cache(app)
    return app.config


def test_without_redis_the_cache_is_in_memory(monkeypatch):
    # Production has no Redis: the old default (Redis on localhost) failed every request.
    assert cache_config(monkeypatch)["CACHE_TYPE"] == "SimpleCache"


def test_the_in_memory_cache_does_not_evict_counters_under_a_flood(monkeypatch):
    # SimpleCache prunes entries beyond CACHE_THRESHOLD (500 by default), which would reset
    # a limit once enough distinct addresses/e-mails have been seen.
    assert cache_config(monkeypatch)["CACHE_THRESHOLD"] >= 50000


def test_with_a_redis_url_the_cache_is_redis(monkeypatch):
    config = cache_config(monkeypatch, REDIS_URL="redis://redis:6379/0")
    assert config["CACHE_TYPE"] == "RedisCache" and config["CACHE_REDIS_URL"] == "redis://redis:6379/0"
