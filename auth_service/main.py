import platform

from SLL_auth import create_app
from configmodule import get_config



# Printed to stdout so the host's log viewer shows the live CPU architecture.
print(f"runtime: machine={platform.machine()} system={platform.system()} python={platform.python_version()}", flush=True)

auth_app = create_app(get_config())


if __name__ == '__main__':
    auth_app.run(host=auth_app.config['SERVER_HOST'], port=auth_app.config['SERVER_PORT'])



