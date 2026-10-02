import hashlib
import hmac
import logging
import logging.config
import os
import re
import sys
from enum import Enum

# Deactivate werkzeug logs
logging.getLogger('werkzeug').setLevel(logging.ERROR)

def _handlers():
    """Log to stdout, which the platform keeps; a file only when LOG_FILE asks for one.

    The file used to be the only destination (py_log.log inside the container): nothing
    reached the platform's logs and it vanished with each deploy.
    """
    handlers = [logging.StreamHandler(sys.stdout)]
    if os.getenv("LOG_FILE"):
        handlers.append(logging.FileHandler(os.getenv("LOG_FILE"), mode="a"))
    return handlers


logging.basicConfig(level=logging.INFO, handlers=_handlers(),
                    format="%(asctime)s - %(levelname)s - %(message)s")

_process_key = os.urandom(32)
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _fingerprint_key() -> bytes:
    keys = (os.getenv("API_KEY_LIST") or "").strip()
    if not keys:
        return _process_key
    return hmac.new(keys.encode("utf-8"), b"log-email-v1", hashlib.sha256).digest()


def mask_email(email) -> str:
    """Short keyed fingerprint of an e-mail: tells callers apart without writing who they are."""
    digest = hmac.new(_fingerprint_key(), str(email).strip().lower().encode("utf-8"), hashlib.sha256).hexdigest()
    return "hmac:" + digest[:12]


def scrub_emails(text: str) -> str:
    """The log goes to the platform's retention, so no address is written in clear (the teacher
    catalog is searched by e-mail, and a not-found line repeats the value searched)."""
    return _EMAIL.sub(lambda match: mask_email(match.group(0)), text)


class Logmessage(Enum):
    REQUEST_INFO = "Method: {request_method} - Path: {request_path} - IP: {ip_address}"
    ERROR = "Message: {error_message} - Path: {request_path} - IP: {ip_address}"
    MISSING_CREDENTIALS = "Missing credentials: {request_method} - Path: {request_path} - IP: {ip_address}"
    INVALID_API_KEY = "Invalid API key: {request_method} - Path: {request_path} - IP: {ip_address} - API key fingerprint: {api_key_fingerprint}"
    RESOURCE_NOT_FOUND = "Resource: {resource_type} not found - Parameter: {parameter} = '{value}' - Path: {request_path} - IP: {ip_address}"
    AUTHENTICATION_REQUEST = "Authentication request: {request_method} - Path: {request_path} - IP: {ip_address} - API key fingerprint: {api_key_fingerprint} - User: X"



class LogType(Enum):
    INFO = logging.INFO
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    DEBUG = logging.DEBUG
    CRITICAL = logging.CRITICAL


class AppLogger:

    @staticmethod
    def log(message: Logmessage, log_type: LogType, **kwargs):
        try:
            formatted_message = scrub_emails(message.value.format(**kwargs))
        except KeyError as e:
            logging.error(f"Log format error:{e}")
            return

        log_function = {
            logging.INFO: logging.info,
            logging.ERROR: logging.error,
            logging.WARNING: logging.warning,
            logging.DEBUG: logging.debug,
            logging.CRITICAL: logging.critical,
        }.get(log_type.value, logging.info)

        log_function(formatted_message)
