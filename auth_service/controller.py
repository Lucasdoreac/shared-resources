import os
import re
import secrets
from datetime import datetime, timedelta
from hashlib import sha256

from DAL_auth import AuthenticationRepository

# secrets.token_urlsafe(32) is 43 URL-safe characters; anything else (including
# the old 64-hex timestamp hashes) is rejected before touching the database.
TOKEN_PATTERN = re.compile(r'^[A-Za-z0-9_-]{43}$')


def normalize_email(email):
    return (email or '').strip().lower()


def token_ttl():
    try:
        minutes = int(os.getenv('AUTH_TOKEN_TTL_MINUTES', '720'))
    except ValueError:
        minutes = 720
    return timedelta(minutes=max(1, minutes))


def hash_token(token):
    return sha256(token.encode('utf-8')).hexdigest()


class AuthenticationController:
    """
       Controller responsável pela lógica de autenticação e gerenciamento de tokens.

       Implementa o padrão Singleton para garantir que apenas uma instância seja utilizada em toda a aplicação.
       Utiliza o repositório de autenticação para validar, inserir tokens e gerar hashes únicos.
    """

    _authentication_instance = None

    def __new__(cls, *args, **kwargs):
        """
                Garante que apenas uma instância da classe seja criada (padrão Singleton).

                Returns:
                    AuthenticationController: Instância única da classe.
        """

        if cls._authentication_instance is None:
            cls._authentication_instance = super(AuthenticationController, cls).__new__(cls)
        return cls._authentication_instance

    def __init__(self):
        """
                Inicializa o AuthenticationController instanciando o repositório de autenticação.
        """

        self.tokens_repository = AuthenticationRepository()

    def is_token_valid(self, token: str, email: str) -> bool:
        """True when ``token`` is a live token issued to ``email``."""
        if not isinstance(token, str) or not TOKEN_PATTERN.match(token):
            return False
        email = normalize_email(email)
        if not email:
            return False
        return self.tokens_repository.validate_authentication(email, hash_token(token))

    def insert_token(self, email: str, token: str) -> str:
        """Store only the hash of ``token``, bound to ``email``, with a short expiry."""
        expires_at = datetime.now() + token_ttl()
        return self.tokens_repository.insert_authentication(
            normalize_email(email), hash_token(token), expires_at)

    def generate_token(self) -> str:
        """Unpredictable login token (256 bits from the OS CSPRNG)."""
        return secrets.token_urlsafe(32)
