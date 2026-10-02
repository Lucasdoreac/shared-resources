"""Response headers every answer carries, the docs switch and the single dev opt-out."""

import os

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
