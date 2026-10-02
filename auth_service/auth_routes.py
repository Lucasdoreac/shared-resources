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
        email = (request.args.get('email') or '').strip().lower()

        failures_key = f"validate:email:{email}"
        if rate_limit.count(failures_key) >= VALIDATE_FAILURES_PER_EMAIL:
            return rate_limited()

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

        rate_limit.hit(failures_key)
        return jsonify({"message": "Invalid or missing token"}), 403
    return decorated_function


VALIDATE_FAILURES_PER_EMAIL = 30
SEND_LINK_PER_EMAIL = 3
# Behind the API every user reaches this service from the API's address, so the
# per-address budget is only a coarse cap for direct calls; the per-client limit
# lives in the API (client_limits.py) and the per-address one here (per e-mail).
SEND_LINK_PER_IP = 300
POSITIVE_CACHE_SECONDS = 60


def rate_limited():
    response = jsonify({"error": "Too many requests; try again later"})
    response.headers["Retry-After"] = str(rate_limit.window_seconds())
    return response, 429


def return_link_in_response():
    """
    Só em desenvolvimento, e só se pedido: o link de login volta na resposta
    em vez de ir por e-mail. Antes bastava FLASK_ENV=development, e um deploy
    com o .env de dev deixava qualquer um entrar como qualquer @udf.edu.br.
    """
    return (os.getenv('FLASK_ENV') == 'development'
            and os.getenv('AUTH_DEV_RETURN_LINK', '').strip().lower() in ('1', 'true', 'yes', 'on'))


def is_allowed_login_email(email):
    """Allow UDF addresses and explicitly configured one-off exceptions."""
    normalized = (email or '').strip().lower()
    if normalized.count('@') != 1:
        return False
    if normalized.endswith('@udf.edu.br'):
        return True
    allowed = {
        item.strip().lower()
        for item in os.getenv('AUTH_ALLOWED_EMAILS', '').split(',')
        if item.strip()
    }
    return normalized in allowed


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
    minio_url = (os.getenv('MINIO_URL') or '').strip().rstrip('/')
    minio_icon_url = f"{minio_url}/labtech/email-icones/magic-link.png" if minio_url else ""
    html_content = render_template('email/magic_link.html',
                                   username=username,
                                   magic_link=magic_link,
                                   minio_icon_url=minio_icon_url)

    url = f"{os.getenv('CLOUD_FUNCTION_URL')}/send-email"
    payload = {
        'subject': 'Autorização de Acesso',
        'content': html_content,
        'to': [email],
        'is_html': True
    }
    headers = {
        'X-API-Key': os.getenv('CLOUD_FUNCTION_API_KEY'),
        'Content-Type': 'application/json'
    }
    response = requests.post(url, json=payload, headers=headers)
    return response


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
        if not is_allowed_login_email(email):
            return jsonify({'error': 'Invalid email domain'}), 400
        if (rate_limit.hit(f"send:email:{email}") > SEND_LINK_PER_EMAIL
                or rate_limit.hit(f"send:ip:{rate_limit.client_ip(request)}") > SEND_LINK_PER_IP):
            return rate_limited()
        hash_auth = authentication_controller.generate_token()

        # Save the hash and email in the database
        authentication_controller.insert_token(email, hash_auth)

        # Send the magic link via email
        magic_link = f"{os.getenv('REACT_APP')}/auth/callback?{urlencode({'email': email, 'hash': hash_auth})}"
        if return_link_in_response():
            return jsonify({'magic_link': magic_link}), 201
        try:
            send_response = send_magic_link(email, email.split('@')[0], magic_link)
            if send_response.status_code != 200:
                return jsonify({'error': 'Email sender service unavailable: failed to send email'}), 503
        except Exception as e:
            current_app.logger.error('Login e-mail delivery failed: %s', type(e).__name__)
            return jsonify({'error': 'Email sender service unavailable'}), 503


        return jsonify({'message': 'Magic link sent successfully'}), 201

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
