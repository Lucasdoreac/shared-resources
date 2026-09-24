import os

# config_module e utils/auth.py leem API_KEY_LIST na importação; o container
# de teste não tem .env. Vale para todos os testes, qualquer que seja a ordem.
os.environ.setdefault("API_KEY_LIST", "test-key")
