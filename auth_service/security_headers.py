"""Response headers every answer carries, the docs switch and the single dev opt-out."""

import os
from urllib.parse import urlsplit

from flask import request


def insecure_dev_allowed():
    """ALLOW_INSECURE_DEV=true is honoured only together with FLASK_ENV=development."""
    return (os.getenv("FLASK_ENV") == "development"
            and os.getenv("ALLOW_INSECURE_DEV", "").strip().lower() in ("1", "true", "yes", "on"))


def docs_enabled():
    """Swagger UI and the spec are off unless ENABLE_API_DOCS=true (or the development opt-out)."""
    return (os.getenv("ENABLE_API_DOCS", "").strip().lower() in ("1", "true", "yes", "on")
            or insecure_dev_allowed())


def apply_security_headers(response):
    headers = response.headers
    headers.setdefault("X-Content-Type-Options", "nosniff")
    headers.setdefault("X-Frame-Options", "DENY")
    headers.setdefault("Referrer-Policy", "no-referrer")
    if request.is_secure or request.headers.get("X-Forwarded-Proto", "").lower() == "https":
        headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if response.mimetype == "application/json":
        headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
    return response


def _origin(url):
    parts = urlsplit((url or "").strip())
    return f"{parts.scheme}://{parts.netloc}" if parts.scheme in ("http", "https") and parts.netloc else None


def cors_origins():
    """Origins allowed to call this service from a browser: the frontend's own.

    The origin of REACT_APP or FRONTEND_URL, plus the exact origins in
    CORS_ALLOWED_ORIGINS. With none of them no origin is allowed (never "*");
    only the development opt-out opens everything.
    """
    if insecure_dev_allowed():
        return "*"
    origins = []
    for candidate in [os.getenv("REACT_APP"), os.getenv("FRONTEND_URL")] + (os.getenv("CORS_ALLOWED_ORIGINS") or "").split(","):
        origin = _origin(candidate)
        if origin and origin not in origins:
            origins.append(origin)
    return origins
