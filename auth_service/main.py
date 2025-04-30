from SLL_auth import create_app
from configmodule import get_config



auth_app = create_app(get_config())


if __name__ == '__main__':
    auth_app.run(host=auth_app.config['SERVER_HOST'], port=auth_app.config['SERVER_PORT'])



