import hashlib
import hmac
from functools import wraps
from flask import request, jsonify

from config_module import get_config, insecure_dev_allowed
from utils.log_functions import log_authentication_request, log_missing_credentials, log_invalid_credentials

config = get_config()
API_KEY_LIST = config.API_KEY_LIST

# The catalog is closed by default: every data route needs a valid key. The
# docs (/apidocs, /apispec.json) and /health stay open.
PROTECTED_PREFIXES = ("/restapi", "/graphql")


def key_fingerprint(api_key):
    """Short, non-reversible tag to correlate log lines; never the key itself."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:8]


def validate_api_key(api_key):
    """Constant-time comparison against every configured key."""
    if not api_key:
        return False
    matched = False
    for key in API_KEY_LIST:
        if hmac.compare_digest(api_key.encode("utf-8"), key.encode("utf-8")):
            matched = True
    return matched


def api_key_error():
    """Error response when x-api-key is missing, empty or invalid; None when fine."""
    api_key = request.headers.get("x-api-key")
    if not api_key:
        log_missing_credentials()
        return jsonify({"error": "Unauthorized: Missing API Key"}), 403

    if not validate_api_key(api_key):
        log_invalid_credentials(api_key_fingerprint=key_fingerprint(api_key))
        return jsonify({"error": "Unauthorized: Invalid API Key"}), 403

    log_authentication_request(api_key_fingerprint=key_fingerprint(api_key))
    return None


def require_api_key_on_catalog():
    """before_request: runs ahead of the cache and the route."""
    if insecure_dev_allowed():
        return None
    if request.path.startswith(PROTECTED_PREFIXES):
        return api_key_error()
    return None


def check_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        error = api_key_error()
        if error:
            return error
        return func(*args, **kwargs)
    return wrapper
