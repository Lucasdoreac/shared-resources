from SLL import create_app
from config_module import get_config

if __name__ == "__main__":
    app = create_app(get_config())
    app.run()