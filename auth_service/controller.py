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


def _ttl(name, default):
    try:
        minutes = int(os.getenv(name, str(default)))
    except ValueError:
        minutes = default
    return timedelta(minutes=max(1, minutes))


def link_ttl():
    """The e-mailed link is short-lived and single use (AUTH_LINK_TTL_MINUTES, default 30)."""
    return _ttl('AUTH_LINK_TTL_MINUTES', 30)


def session_ttl():
    """The session token the link is exchanged for (AUTH_SESSION_TTL_MINUTES, default 720)."""
    return _ttl('AUTH_SESSION_TTL_MINUTES', 720)


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
        """True when ``token`` is a live session token issued to ``email``."""
        if not isinstance(token, str) or not TOKEN_PATTERN.fullmatch(token):
            return False
        email = normalize_email(email)
        if not email:
            return False
        return self.tokens_repository.validate_authentication(email, hash_token(token), 'session')

    def revoke_session(self, token: str, email: str) -> bool:
        """Delete the caller's session record (logout); True only when this call removed it.

        The delete is the claim, as for the link exchange, so a second logout with the same
        token (or a concurrent one) finds nothing and reports False.
        """
        if not isinstance(token, str) or not TOKEN_PATTERN.fullmatch(token):
            return False
        email = normalize_email(email)
        if not email:
            return False
        return self.tokens_repository.consume_authentication(email, hash_token(token), 'session')

    def insert_token(self, email: str, token: str) -> str:
        """Store only the hash of an e-mailed link token, bound to ``email``, short-lived."""
        expires_at = datetime.now() + link_ttl()
        return self.tokens_repository.insert_authentication(
            normalize_email(email), hash_token(token), expires_at, 'link')

    def exchange_link_token(self, token: str, email: str):
        """Trade a link token for a session token; the link is consumed (single use).

        Returns the new session token, or None when the link is unknown,
        expired, already used or issued to another address.
        """
        if not isinstance(token, str) or not TOKEN_PATTERN.fullmatch(token):
            return None
        email = normalize_email(email)
        if not email:
            return None
        if not self.tokens_repository.consume_authentication(email, hash_token(token), 'link'):
            return None
        session = self.generate_token()
        self.tokens_repository.insert_authentication(
            email, hash_token(session), datetime.now() + session_ttl(), 'session')
        return session

    def generate_token(self) -> str:
        """Unpredictable login token (256 bits from the OS CSPRNG)."""
        return secrets.token_urlsafe(32)
