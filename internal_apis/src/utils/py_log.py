import hashlib
import logging
import logging.config
from enum import Enum

# Deactivate werkzeug logs
logging.getLogger('werkzeug').setLevel(logging.ERROR)

logging.basicConfig(level=logging.INFO, filename="py_log.log", filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")


def mask_secret(value) -> str:
    """Impressão digital curta: correlaciona linhas do log sem expor a chave."""
    if not value:
        return "-"
    return "sha256:" + hashlib.sha256(str(value).encode()).hexdigest()[:8]


class Logmessage(Enum):
    REQUEST_INFO = "Method: {request_method} - Path: {request_path} - IP: {ip_address}"
    ERROR = "Message: {error_message} - Path: {request_path} - IP: {ip_address}"
    MISSING_CREDENTIALS = "Missing credentials: {request_method} - Path: {request_path} - IP: {ip_address}"
    INVALID_API_KEY = "Invalid API key: {request_method} - Path: {request_path} - IP: {ip_address} - API Key: {api_key}"
    RESOURCE_NOT_FOUND = "Resource: {resource_type} not found - Parameter: {parameter} = '{value}' - Path: {request_path} - IP: {ip_address}"
    AUTHENTICATION_REQUEST = "Authentication request: {request_method} - Path: {request_path} - IP: {ip_address} - API Key: {api_key} - User: X"



class LogType(Enum):
    INFO = logging.INFO
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    DEBUG = logging.DEBUG
    CRITICAL = logging.CRITICAL


class AppLogger:

    @staticmethod
    def log(message: Logmessage, log_type: LogType, **kwargs):
        if "api_key" in kwargs:
            kwargs["api_key"] = mask_secret(kwargs["api_key"])
        try:
            formatted_message = message.value.format(**kwargs)
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
