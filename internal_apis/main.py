from SLL import create_app
from config_module import get_config

# Create the app at module level so Gunicorn can import it.
internal_apis = create_app(get_config())

if __name__ == "__main__":
    internal_apis.run(host="0.0.0.0", port=5081, debug=False)


