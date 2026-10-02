import hashlib
import os
from functools import wraps
from flask import request, jsonify

from config_module import get_config
from utils.log_functions import log_authentication_request, log_missing_credentials, log_invalid_credentials

config = get_config()
API_KEY_LIST = config.API_KEY_LIST

# Read endpoints stay open unless the operator turns the switch on; the Auth
# and API callers must send x-api-key first (python-services sends
# CATALOG_API_KEY when it is set).
PROTECTED_READ_PREFIXES = ("/restapi", "/graphql")


def key_fingerprint(api_key):
    """Short, non-reversible tag to correlate log lines; never the key itself."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:8]


def validate_api_key(api_key):
    return api_key in API_KEY_LIST


def _reject_unless_authorized():
    """Return an error response when the request lacks a valid key, else None."""
    api_key = request.headers.get("x-api-key")
    if not api_key:
        log_missing_credentials()
        return jsonify({"error": "Unauthorized: Missing API Key"}), 403

    if not validate_api_key(api_key):
        log_invalid_credentials(api_key_fingerprint=key_fingerprint(api_key))
        return jsonify({"error": "Unauthorized: Invalid API Key"}), 403

    log_authentication_request(api_key_fingerprint=key_fingerprint(api_key))
    return None


def check_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        rejection = _reject_unless_authorized()
        if rejection is not None:
            return rejection
        return func(*args, **kwargs)
    return wrapper


def require_key_for_reads():
    """``before_request`` hook; active only when REQUIRE_API_KEY_FOR_READS is true."""
    if os.getenv("REQUIRE_API_KEY_FOR_READS", "").lower() not in ("1", "true", "yes"):
        return None
    if not request.path.startswith(PROTECTED_READ_PREFIXES):
        return None
    return _reject_unless_authorized()
