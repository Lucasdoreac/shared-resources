import hashlib
import logging

import pytest

from utils.py_log import AppLogger, Logmessage, LogType

SECRET = "chave-secreta-9f8e7d"


def fingerprint(key):
    return "sha256:" + hashlib.sha256(key.encode()).hexdigest()[:8]


@pytest.mark.parametrize("message", [Logmessage.AUTHENTICATION_REQUEST, Logmessage.INVALID_API_KEY])
def test_api_key_never_goes_to_the_log_in_clear(caplog, message):
    # A chave válida ia para o log em TODA requisição autenticada; com a chave
    # exigida em todas as rotas, quem lesse py_log.log teria acesso ao catálogo.
    with caplog.at_level(logging.INFO):
        AppLogger.log(message, LogType.INFO, request_method="GET", request_path="/restapi/campus/",
                      ip_address="1.2.3.4", api_key=SECRET)

    assert SECRET not in caplog.text
    assert fingerprint(SECRET) in caplog.text
