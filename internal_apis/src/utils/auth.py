import os
from functools import wraps
from flask import request, jsonify

from config_module import get_config
from utils.log_functions import log_authentication_request, log_missing_credentials, log_invalid_credentials

config = get_config()
API_KEY_LIST = config.API_KEY_LIST

def validate_api_key(api_key):
    if api_key in API_KEY_LIST:
        log_authentication_request(api_key)
        return True
    return False


def api_key_error():
    """Resposta de erro se a x-api-key faltar ou for inválida; None se ok."""
    api_key = request.headers.get("x-api-key")
    if not api_key:
        log_missing_credentials()
        return jsonify({"error": "Unauthorized: Missing API Key"}), 403

    if not validate_api_key(api_key):
        log_invalid_credentials(api_key=api_key)
        return jsonify({"error": "Unauthorized: Invalid API Key"}), 403
    return None


# Rotas com dados do catálogo. A documentação (/apidocs, /apispec.json) fica aberta.
PROTECTED_PREFIXES = ("/restapi", "/graphql")


def require_api_key_on_catalog():
    """before_request: exige a chave em todo o catálogo, antes do cache e da
    rota. Antes só o POST /offers pedia; o resto (inclusive professores)
    respondia a quem alcançasse a porta."""
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
