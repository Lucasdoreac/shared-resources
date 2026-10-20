import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


CONFIG_MODULE = Path(__file__).resolve().parents[1] / "configmodule.py"


def load_config_module():
    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda: None
    spec = importlib.util.spec_from_file_location("auth_configmodule_under_test", CONFIG_MODULE)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"dotenv": dotenv_stub}):
        spec.loader.exec_module(module)
    return module


class ConfigModuleTests(unittest.TestCase):
    def test_explicit_mongo_uri_supports_local_compose(self):
        local_uri = "mongodb://mongo:27017/"
        env = {
            "MONGO_DATABASE": "rooms-reservation-app",
            "MONGO_URI": local_uri,
            "MONGO_HOST": "unused.example.net",
            "MONGO_USERNAME": "unused",
            "MONGO_PASSWORD": "unused",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_config_module().Config

        self.assertEqual(config.MONGO_URI, local_uri)

    def test_atlas_uri_is_built_when_no_explicit_uri_is_set(self):
        env = {
            "MONGO_DATABASE": "rooms-reservation-app",
            "MONGO_HOST": "cluster.example.net",
            "MONGO_USERNAME": "user",
            "MONGO_PASSWORD": "pw",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_config_module().Config

        self.assertEqual(config.MONGO_URI, "mongodb+srv://user:pw@cluster.example.net/")


if __name__ == "__main__":
    unittest.main()
