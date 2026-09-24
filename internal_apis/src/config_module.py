import os
from dotenv import load_dotenv


class Config:
    load_dotenv()  # Ensure the environment variables are loaded

    # Default configurations
    DEBUG = False
    TESTING = False

    # MongoDB database
    MONGO_DATABASE = os.getenv("MONGO_DATABASE")

    # MongoDB URI setup
    MONGO_URI = os.getenv("MONGO_URI")

    API_KEY_LIST = os.getenv("API_KEY_LIST").split(",")

    SERVER_HOST = "0.0.0.0"
    SERVER_NAME = os.getenv("SERVER_NAME") or None


class DevelopmentConfig(Config):
    DEBUG = True


def get_config():
    return DevelopmentConfig()
