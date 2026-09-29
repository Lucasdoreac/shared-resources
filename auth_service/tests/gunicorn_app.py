from mongo import MongoDBConnectionFactory
from SLL_auth import create_app


class GunicornTestConfig:
    TESTING = True
    MONGO_URI = "mongodb://localhost:27017/"
    MONGO_DATABASE = "auth_gunicorn_smoke"


# The health route does not use MongoDB; keep this process smoke independent
# from an external database while exercising Gunicorn's real WSGI startup.
MongoDBConnectionFactory.init_app = lambda *_args, **_kwargs: None
app = create_app(GunicornTestConfig)
