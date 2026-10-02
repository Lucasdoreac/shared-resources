"""Small fixed-window counters for the login endpoints.

Counters live in the Flask-Caching backend (Redis when configured, otherwise the
per-process SimpleCache). If that backend raises, the counter falls back to an
in-process dictionary: a cache outage never turns the limits off. Without Redis
each Gunicorn worker counts on its own, so the effective limit is the configured
one times the number of workers and a restart resets it.
"""

import ipaddress
import os
import threading
import time

from cache import cache

_local = {}
_lock = threading.Lock()


def window_seconds():
    try:
        return max(1, int(os.getenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "900")))
    except ValueError:
        return 900


def client_ip(request):
    """Client address for per-client limits.

    Order: the platform's True-Client-IP header, then X-Forwarded-For, then the
    socket address. Measured on Render: X-Forwarded-For arrives as
    [values sent by the client, real client, two private hops], because each
    hop appends, so the entry TRUSTED_PROXY_HOPS places from the right
    (default 1) is a private proxy, not the client. True-Client-IP is set by the
    platform to the real client and a client-sent value is overwritten. The
    socket address is always the local proxy. Health checks carry no forwarding
    headers. TRUSTED_PROXY_HOPS only applies when the platform header is absent
    or invalid (other proxies, local runs).
    """
    platform = (request.headers.get("True-Client-IP") or "").strip()[:64]
    if platform:
        try:
            return str(ipaddress.ip_address(platform))
        except ValueError:
            pass
    try:
        hops = max(0, int(os.getenv("TRUSTED_PROXY_HOPS", "1")))
    except ValueError:
        hops = 1
    forwarded = [part.strip() for part in request.headers.get("X-Forwarded-For", "").split(",") if part.strip()]
    if hops and len(forwarded) >= hops:
        return forwarded[-hops]
    return request.remote_addr or "unknown"


def _local_count(key, increment):
    now = time.monotonic()
    with _lock:
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
