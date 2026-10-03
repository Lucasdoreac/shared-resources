"""The log goes to the platform's retention: no e-mail address may reach it."""

import logging
import string
import subprocess
import sys
from pathlib import Path

import pytest

from utils.py_log import AppLogger, Logmessage, LogType, mask_email, scrub_emails

ADDRESS = "docente.teste@udf.edu.br"


@pytest.mark.parametrize("message", list(Logmessage), ids=lambda m: m.name)
def test_no_message_writes_an_address(message, caplog):
    fields = {name: ADDRESS for _, name, _, _ in string.Formatter().parse(message.value) if name}
    with caplog.at_level(logging.DEBUG):
        AppLogger.log(message, LogType.INFO, **fields)
    text = "\n".join(r.getMessage() for r in caplog.records)
    assert text, f"{message.name} wrote nothing"
    assert ADDRESS not in text and "@udf.edu.br" not in text


def test_an_address_becomes_a_keyed_fingerprint_that_is_stable():
    line = scrub_emails(f"searched {ADDRESS} then {ADDRESS.upper()}")
    assert line == f"searched {mask_email(ADDRESS)} then {mask_email(ADDRESS)}"
    assert mask_email(ADDRESS) != mask_email("outra.pessoa@udf.edu.br")


def test_log_lines_go_to_stdout_not_only_to_a_file_in_the_container():
    # a fresh interpreter: pytest installs its own root handlers, so the import-time setup is checked here
    code = (
        "import logging\n"
        "from utils.py_log import AppLogger, Logmessage, LogType\n"
        "AppLogger.log(Logmessage.ERROR, LogType.ERROR, error_message='boom', request_path='/p', ip_address='1.2.3.4')\n"
        "print([type(h).__name__ for h in logging.getLogger().handlers])\n"
    )
    src = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, "-c", code], cwd=src, capture_output=True, text=True,
                            env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(src), "PYTHONDONTWRITEBYTECODE": "1", "API_KEY_LIST": "test-api-key-0123456789-abcdef"})
    assert "Message: boom" in result.stdout, result.stderr
    assert "FileHandler" not in result.stdout.splitlines()[-1], "a file is written only when LOG_FILE is set"
