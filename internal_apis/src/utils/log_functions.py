from flask import request
from functools import wraps

from .py_log import AppLogger, Logmessage, LogType


def log_resource_not_found(resource_type, parameter, value):
    AppLogger.log(
        Logmessage.RESOURCE_NOT_FOUND,
        LogType.ERROR,
        resource_type=resource_type,
        parameter=parameter,
        value=value,
        request_path=request.path,
        ip_address=request.remote_addr,
    )

def log_info_request(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        AppLogger.log(
            Logmessage.REQUEST_INFO,
            LogType.INFO,
            ip_address=request.remote_addr,
            request_method=request.method,
            request_path=request.path,
        )
        return func(*args, **kwargs)
    return wrapper

def log_error_request(erro_message):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            AppLogger.log(
                Logmessage.ERROR,
                LogType.ERROR,
                error_message=erro_message,
                ip_address=request.remote_addr,
                request_method=request.method,
                request_path=request.path,
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator

def log_authentication_request(api_key_fingerprint):

    AppLogger.log(
        Logmessage.AUTHENTICATION_REQUEST,
        LogType.INFO,
        request_method=request.method,
        request_path=request.path,
        ip_address=request.remote_addr,
        api_key_fingerprint=api_key_fingerprint,
    )

def log_missing_credentials():
    AppLogger.log(
        Logmessage.MISSING_CREDENTIALS,
        LogType.WARNING,
        request_method=request.method,
        request_path=request.path,
        ip_address=request.remote_addr,
    )

def log_invalid_credentials(api_key_fingerprint):
    AppLogger.log(
        Logmessage.INVALID_API_KEY,
        LogType.WARNING,
        request_method=request.method,
        request_path=request.path,
        ip_address=request.remote_addr,
        api_key_fingerprint=api_key_fingerprint,
    )