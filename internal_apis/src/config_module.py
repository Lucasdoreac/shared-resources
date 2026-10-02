import os
from dotenv import load_dotenv


def insecure_dev_allowed():
    """The single opt-out: only with FLASK_ENV=development AND ALLOW_INSECURE_DEV=true."""
    return (os.getenv("FLASK_ENV") == "development"
            and os.getenv("ALLOW_INSECURE_DEV", "").strip().lower() in ("1", "true", "yes", "on"))


def parse_api_keys(raw):
    """Non-empty, trimmed keys from a comma-separated list.

    An unset, empty or all-blank list stops the start with a clear error: the
    catalog is closed by default and must never fall back to open access. The
    development opt-out is the only way to run without keys.
    """
    keys = [item.strip() for item in (raw or "").split(",") if item.strip()]
    if not keys and not insecure_dev_allowed():
        raise RuntimeError(
            "API_KEY_LIST is not set or has no usable key: the Catalog would be unusable. "
            "Set one or more comma-separated keys (development only: "
            "FLASK_ENV=development and ALLOW_INSECURE_DEV=true)."
        )
    return keys


class Config:
    load_dotenv()  # Ensure the environment variables are loaded

    # Default configurations
    DEBUG = False
    TESTING = False

    # MongoDB database
    MONGO_DATABASE = os.getenv("MONGO_DATABASE")

    # MongoDB URI setup
    MONGO_URI = os.getenv("MONGO_URI")

    API_KEY_LIST = parse_api_keys(os.getenv("API_KEY_LIST"))

    SERVER_HOST = "0.0.0.0"
    SERVER_NAME = os.getenv("SERVER_NAME", "localhost:5081")


class DevelopmentConfig(Config):
    DEBUG = True


def get_config():
    return DevelopmentConfig()
