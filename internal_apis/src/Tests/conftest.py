import os

# config_module reads API_KEY_LIST when it is imported; the Catalog refuses to
# start without a key, so the tests hold a fake one before anything is imported.
os.environ.setdefault("API_KEY_LIST", "test-api-key-0123456789-abcdef")
