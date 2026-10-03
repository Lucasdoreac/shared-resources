"""Small fixed-window counters for the login endpoints.

Counters live in the Flask-Caching backend (Redis when configured, otherwise the
per-process SimpleCache). If that backend raises, the counter falls back to an
in-process dictionary: a cache outage never turns the limits off. Without Redis
each Gunicorn worker counts on its own, so the effective limit is the configured
one times the number of workers and a restart resets it.
"""

import hmac
import os
import threading
import time

from cache import cache

_local = {}
_lock = threading.Lock()
# Keys come from clients, so the fallback is bounded: at the cap, expired counters go
# first, then the oldest ones. Evicting a live counter resets its limit, which is
# preferred over unbounded memory while the cache backend is down.
LOCAL_MAX_ENTRIES = 20000


def window_seconds():
    try:
        return max(1, int(os.getenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "900")))
    except ValueError:
        return 900


def client_ip(request):
    """Client address behind the platform proxy.

    TRUSTED_PROXY_HOPS is how many proxies append to X-Forwarded-For before
    this service; the entry that many places from the right is the client.
    """
    try:
        hops = max(0, int(os.getenv("TRUSTED_PROXY_HOPS", "1")))
    except ValueError:
        hops = 1
    forwarded = [part.strip() for part in request.headers.get("X-Forwarded-For", "").split(",") if part.strip()]
    if hops and len(forwarded) >= hops:
        return forwarded[-hops]
    return request.remote_addr or "unknown"


def forwarded_client(request):
    """The client address the API forwarded, or None when there is no valid proof.

    Behind the API every user reaches this service from the API's address, so the API
    forwards the real client in X-Client-IP, proven with X-Forward-Key (AUTH_FORWARD_KEY,
    compared in constant time). Without the variable or with a wrong key the header is
    ignored: nothing changes until the variable is set on both services.
    """
    key = os.getenv("AUTH_FORWARD_KEY", "")
    forwarded = (request.headers.get("X-Client-IP") or "").strip()
    proof = request.headers.get("X-Forward-Key") or ""
    if key and forwarded and hmac.compare_digest(proof.encode("utf-8"), key.encode("utf-8")):
        return forwarded[:64]
    return None


def subject_ip(request):
    """Client address to count against: the forwarded one when proven, else the connecting one."""
    return forwarded_client(request) or client_ip(request)


def _make_room(now):
    """Keep ``_local`` below LOCAL_MAX_ENTRIES (caller holds the lock)."""
    if len(_local) < LOCAL_MAX_ENTRIES:
        return
    for key in [k for k, (_, reset_at) in _local.items() if now >= reset_at]:
        del _local[key]
    while len(_local) >= LOCAL_MAX_ENTRIES:
        del _local[next(iter(_local))]  # dicts keep insertion order: the first key is the oldest


def _local_count(key, increment):
    now = time.monotonic()
    with _lock:
        if key not in _local:
            _make_room(now)
        count, reset_at = _local.get(key, (0, 0.0))
        if now >= reset_at:
            count, reset_at = 0, now + window_seconds()
        if increment:
            count += 1
        _local[key] = (count, reset_at)
        return count


def count(key):
    """Events recorded for ``key`` in the current window."""
    full = "rl:" + key
    try:
        return int(cache.get(full) or 0)
    except Exception:
        return _local_count(full, False)


def hit(key):
    """Record one event for ``key`` and return the new count."""
    full = "rl:" + key
    try:
        if cache.get(full) is None:
            cache.set(full, 0, timeout=window_seconds())
        return int(cache.cache.inc(full))
    except Exception:
        return _local_count(full, True)


def reset_local():
    with _lock:
        _local.clear()
