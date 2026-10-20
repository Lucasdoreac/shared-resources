"""Contrato de inicialização: o módulo da API deve subir sem as variáveis opcionais.

Os testes rodam em subprocesso para medir o import real do entrypoint, sem depender
do estado de sys.modules deste processo de teste.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GLOBAL_VARS = ("GLOBAL_BUCKET_SIZE", "GLOBAL_LEAK_RATE", "GLOBAL_QUEUE_NAME")


def _env(*, drop=(), extra=None):
    env = {k: v for k, v in os.environ.items() if k not in GLOBAL_VARS and k not in drop}
    defaults = {
        "MONGO_URI": "mongodb://127.0.0.1:27017/test",
        "MONGO_DATABASE": "test",
        "API_KEY_LIST": "k1",
        "SERVER_NAME": "localhost",
        "PYTHONPATH": str(ROOT / "src"),
    }
    env.update({k: v for k, v in defaults.items() if k not in drop})
    env.update(extra or {})
    return env


def _run(code, env):
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_wsgi_object_is_exposed_under_both_names():
    result = _run(
        "import main; assert main.internal_apis is main.internal_api; print('ok')",
        _env(),
    )
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_api_imports_without_global_bucket_variables():
    result = _run("import main; print('ok')", _env())
    assert result.returncode == 0, result.stderr


def test_global_bucket_defaults_apply_when_variables_are_missing(monkeypatch):
    for name in GLOBAL_VARS:
        monkeypatch.delenv(name, raising=False)
    from backpressure import rabbitmq_utils

    assert rabbitmq_utils.get_global_bucket_size() == rabbitmq_utils.GLOBAL_BUCKET_SIZE_DEFAULT
    assert rabbitmq_utils.get_global_leak_rate() == rabbitmq_utils.GLOBAL_LEAK_RATE_DEFAULT


def test_global_bucket_values_come_from_environment(monkeypatch):
    monkeypatch.setenv("GLOBAL_BUCKET_SIZE", "7")
    monkeypatch.setenv("GLOBAL_LEAK_RATE", "2.5")
    from backpressure import rabbitmq_utils

    assert rabbitmq_utils.get_global_bucket_size() == 7
    assert rabbitmq_utils.get_global_leak_rate() == 2.5


def test_missing_api_key_list_yields_empty_list_and_refuses_every_key():
    code = (
        "from config_module import Config\n"
        "from utils.auth import validate_api_key\n"
        "assert Config.API_KEY_LIST == [], Config.API_KEY_LIST\n"
        "assert not validate_api_key('')\n"
        "assert not validate_api_key(None)\n"
        "assert not validate_api_key('qualquer')\n"
        "print('ok')\n"
    )
    result = _run(code, _env(drop=("API_KEY_LIST",)))
    assert result.returncode == 0, result.stderr
