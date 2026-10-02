import platform

from SLL import create_app
from config_module import get_config

# Printed to stdout so the host's log viewer shows the live CPU architecture.
print(f"runtime: machine={platform.machine()} system={platform.system()} python={platform.python_version()}", flush=True)

# Create the app at module level so Gunicorn can import it.
internal_apis = create_app(get_config())

if __name__ == "__main__":
    internal_apis.run(host="0.0.0.0", port=5081, debug=True)

