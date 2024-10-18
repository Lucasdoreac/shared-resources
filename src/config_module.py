import os
from dotenv import load_dotenv


class Config:
    load_dotenv()  # Ensure the environment variables are loaded

    # Default configurations
    DEBUG = False
    TESTING = False

    API_KEY = os.getenv('API_KEY')

    # MongoDB configurations
    MONGO_HOST = os.getenv("MONGO_HOST")
    MONGO_DATABASE = os.getenv("MONGO_DATABASE")
    MONGO_USERNAME = os.getenv("MONGO_USERNAME")
    MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")

    # MongoDB URI setup
    MONGO_URI = f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}/"

    SERVER_HOST = "0.0.0.0"
    SERVER_NAME = 'localhost:5081'


class DevelopmentConfig(Config):
    DEBUG = True


def get_config():
    return DevelopmentConfig()
