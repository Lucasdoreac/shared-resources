import os
from functools import wraps
from hashlib import sha256
from urllib.parse import urlencode
import requests
from flasgger import swag_from
from flask import Blueprint, current_app, jsonify, request, render_template
from controller import AuthenticationController
from swagger_docs import get_swagger_specification
from cache import cache
import rate_limit
from email_policy import is_email_allowed, is_email_dry_run


auth_bp = Blueprint('auth', __name__)

def token_required(f):

    """
        Decorator que verifica se o token e o email passados na requisição são válidos.

        Args:
            f (function): Função que será decorada.

        Returns:
            function: Função decorada que executa a verificação antes de chamar a função original.
        """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.args.get('token')
        email = counted_email(request.args.get('email'))

        keys = failure_keys(email)
        if validation_blocked(keys):
            return rate_limited()
        if email is None:
            # Not an address that can hold a token: the usual failure, no per-address counter.
            record_failure(keys)
            return jsonify({"message": "Invalid or missing token"}), 403

        # Only a positive answer is cached, briefly and under a hash of the
        # pair, so a revoked or expired token stops working within a minute and
        # random guesses cannot fill the cache.
        pair = sha256(f"{email}\0{token}".encode('utf-8')).hexdigest()
        cache_key = f"auth_token:{pair}"
        if cache.get(cache_key) is True:
            return f(*args, **kwargs)

        authentication_controller = AuthenticationController()
        if authentication_controller.is_token_valid(token=token, email=email):
            cache.set(cache_key, True, timeout=POSITIVE_CACHE_SECONDS)
            return f(*args, **kwargs)

        record_failure(keys)
        return jsonify({"message": "Invalid or missing token"}), 403
    return decorated_function


# Each limit has two budgets: one per (e-mail, client), so a stranger cannot lock someone
# else out, and a higher ceiling per e-mail against spraying one address from many clients
# or mail-bombing one inbox. "Client" is the person the API forwards (rate_limit.subject_ip).
VALIDATE_FAILURES_PER_EMAIL_AND_CLIENT = 30
VALIDATE_FAILURES_PER_EMAIL = 300
VALIDATE_FAILURES_PER_CLIENT = 300  # one proven client inventing many e-mails (also bounds cache growth)
SEND_LINK_PER_EMAIL_AND_CLIENT = 3
SEND_LINK_PER_EMAIL = 10
# Behind the API every user reaches this service from the API's address, so the
# per-address budget is only a coarse cap for direct calls; the per-client limit
# lives in the API (client_limits.py) and the per-address one here (per e-mail).
SEND_LINK_PER_IP = 300
POSITIVE_CACHE_SECONDS = 60


MAX_EMAIL_LENGTH = 254  # RFC 5321 path limit; anything longer cannot be an address


def counted_email(raw):
    """The normalized e-mail when it may have per-address counters, else None.

    Only an address send-link would accept (same policy) can ever hold a valid
    token, so any other string gets no per-address counters: otherwise a client
    could create one cache entry per invented string.
    """
    email = str(raw or '').strip().lower()
    if len(email) > MAX_EMAIL_LENGTH or not is_email_allowed(email, allowlist_setting()):
        return None
    return email


def failure_keys(email):
    """Counters for failed validations as (key, limit): per (e-mail, client), per e-mail, per proven client.

    ``email`` None (not an acceptable address) leaves only the per-client counter.
    """
    keys = []
    if email is not None:
        keys.append((f"validate:email:{email}:{rate_limit.subject_ip(request)}", VALIDATE_FAILURES_PER_EMAIL_AND_CLIENT))
        keys.append((f"validate:email:{email}", VALIDATE_FAILURES_PER_EMAIL))
    proven = rate_limit.forwarded_client(request)
    if proven:  # without proof every caller shares the API's address, so a per-address cap would block everyone
        keys.append((f"validate:client:{proven}", VALIDATE_FAILURES_PER_CLIENT))
    return keys


def validation_blocked(keys):
    return any(rate_limit.count(key) >= limit for key, limit in keys)


def record_failure(keys):
    for key, _ in keys:
        rate_limit.hit(key)


def rate_limited():
    response = jsonify({"error": "Too many requests; try again later"})
    response.headers["Retry-After"] = str(rate_limit.window_seconds())
    return response, 429


def return_link_in_response():
    """Only in development, and only when asked: the login link comes back in the
    response instead of by e-mail. FLASK_ENV=development alone is not enough, so
    a deploy with a development .env cannot let anyone in as any institutional address."""
    return (os.getenv('FLASK_ENV') == 'development'
            and os.getenv('AUTH_DEV_RETURN_LINK', '').strip().lower() in ('1', 'true', 'yes', 'on'))


def allowlist_setting():
    """Exact addresses allowed besides @udf.edu.br.

    AUTH_EMAIL_ALLOWLIST is the name; AUTH_ALLOWED_EMAILS, the name the
    Production lineage used, is still read when the first is unset.
    """
    value = os.getenv('AUTH_EMAIL_ALLOWLIST')
    return value if value is not None else os.getenv('AUTH_ALLOWED_EMAILS', '')


def email_logo_url():
    """Public URL of the DW Corp logo shown in e-mails, or "" when no host serves it.

    ``EMAIL_ASSETS_URL`` points at a public folder holding ``dw-corp-logo.png`` (the web app
    serves it from ``/labtech/email-icones/``). Without it the template omits the image
    instead of showing a broken one.
    """
    base = (os.getenv("EMAIL_ASSETS_URL") or "").strip().rstrip("/")
    return f"{base}/dw-corp-logo.png" if base else ""


def send_magic_link(email, username, magic_link):
    """
    Sends an email with a magic link for login.

    Args:
        email (str): Recipient's email address.
        username (str): The user’s name.
        magic_link (str): The authentication link.

    Returns:
        Response: HTTP response from the email sending service.
    """
    # Render the HTML template with dynamic data
    html_content = render_template('email/magic_link.html',
                                   username=username,
                                   magic_link=magic_link,
                                   logo_url=email_logo_url())

    brevo_api_key = os.getenv('BREVO_API_KEY')
    if brevo_api_key:
        sender_email = os.getenv('BREVO_SENDER_EMAIL', '').strip()
        if not sender_email:
            raise ValueError('BREVO_SENDER_EMAIL must be configured when Brevo is enabled')
        payload = {
            'sender': {
                'name': os.getenv('BREVO_SENDER_NAME', 'Reservas UDF'),
                'email': sender_email,
            },
            'to': [{'email': email, 'name': username}],
            'subject': 'Autorização de Acesso',
            'htmlContent': html_content,
        }
        return requests.post(
            'https://api.brevo.com/v3/smtp/email',
            json=payload,
            headers={
                'api-key': brevo_api_key,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            timeout=15,
        )

    # Compatibility path while existing deployments still use the legacy sender.
    url = f"{os.getenv('CLOUD_FUNCTION_URL')}/send-email"
    payload = {
        'subject': 'Autorização de Acesso',
        'content': html_content,
        'to': [email],
        'is_html': True,
    }
    headers = {
        'X-API-Key': os.getenv('CLOUD_FUNCTION_API_KEY'),
        'Content-Type': 'application/json',
    }
    return requests.post(url, json=payload, headers=headers, timeout=15)


# API Routes
class AuthRoutes:
    @staticmethod
    @auth_bp.route('/auth/send-link', methods=['POST'])
    @swag_from(get_swagger_specification('auth', 'POST'))
    def auth_mail():
        """
        Endpoint para envio de magic link via email.
        Processa o email recebido como parâmetro, valida o domínio,
        gera o token de autenticação, insere o token na base e envia o email com o link.
        Returns:
            JSON response: Mensagem de sucesso ou erro, com o status HTTP apropriado.
         """

        # inject controller
        authentication_controller = AuthenticationController()
        email = (request.args.get('email') or '').strip().lower()
        if not is_email_allowed(email, allowlist_setting()):
            return jsonify({'error': 'Invalid email domain'}), 400
        client = rate_limit.subject_ip(request)
        if (rate_limit.hit(f"send:email:{email}:{client}") > SEND_LINK_PER_EMAIL_AND_CLIENT
                or rate_limit.hit(f"send:email:{email}") > SEND_LINK_PER_EMAIL
                or rate_limit.hit(f"send:ip:{rate_limit.client_ip(request)}") > SEND_LINK_PER_IP):
            return rate_limited()
        if is_email_dry_run():
            current_app.logger.info('Magic link suppressed because EMAIL_DRY_RUN is enabled')
            return jsonify({'message': 'Email dry-run enabled; no email sent'}), 202
        hash_auth = authentication_controller.generate_token()

        # Save the hash and email in the database
        authentication_controller.insert_token(email, hash_auth)

        # Send the magic link via email
        magic_link = f"{os.getenv('REACT_APP')}/auth/callback?{urlencode({'email': email, 'hash': hash_auth})}"
        if return_link_in_response():
            return jsonify({'magic_link': magic_link}), 201
        try:
            send_response = send_magic_link(email, email.split('@')[0], magic_link)
            if send_response.status_code not in (200, 201, 202):
                return jsonify({'error': 'Email sender service unavailable: failed to send email'}), 503
        except Exception as e:
            current_app.logger.error('Login e-mail delivery failed: %s', type(e).__name__)
            return jsonify({'error': 'Email sender service unavailable'}), 503


        return jsonify({'message': 'Magic link sent successfully'}), 201

    @staticmethod
    @auth_bp.route('/auth/exchange', methods=['POST'])
    def exchange_link():
        """Trade the e-mailed link token (single use) for a session token."""
        body = request.get_json(silent=True)
        body = body if isinstance(body, dict) else {}
        email = counted_email(body.get('email'))
        keys = failure_keys(email)
        if validation_blocked(keys):
            return rate_limited()
        if email is None:
            record_failure(keys)
            return jsonify({"message": "Invalid or expired link"}), 403
        session = AuthenticationController().exchange_link_token(body.get('token'), email)
        if session is None:
            record_failure(keys)
            return jsonify({"message": "Invalid or expired link"}), 403
        return jsonify({"token": session}), 200

    @staticmethod
    @auth_bp.route('/auth/validate', methods=['GET'])
    @token_required
    @swag_from(get_swagger_specification(path='auth', method='GET'))
    def validate_hash():
        """
                Endpoint para validação do token.

                Verifica se o token enviado na requisição é válido.

                Returns:
                    JSON response: Retorna True com status HTTP 200 se o token é válido.
        """

        return jsonify(True), 200
