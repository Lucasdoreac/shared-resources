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

    # Sem chaves configuradas a lista fica vazia e check_api_key recusa todas as requisições.
    API_KEY_LIST = [key for key in os.getenv("API_KEY_LIST", "").split(",") if key]

    SERVER_HOST = "0.0.0.0"
    SERVER_NAME = os.getenv("SERVER_NAME", "localhost:5081")


class DevelopmentConfig(Config):
    DEBUG = True


def get_config():
    return DevelopmentConfig()
