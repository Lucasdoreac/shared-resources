import os
from functools import wraps
import requests
from flasgger import swag_from
from flask import Blueprint, current_app, jsonify, request, render_template
from controller import AuthenticationController
from swagger_docs import get_swagger_specification
from cache import cache
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
        email = request.args.get('email')

        cache_key = f"auth_token:{token}:{email}"
        cached_valid = cache.get(cache_key)
        if cached_valid is not None:
            if cached_valid is True:
                return f(*args, **kwargs)
            else:
                return jsonify({"message": "Invalid or missing token"}), 403

        authentication_controller = AuthenticationController()
        valid_hash = authentication_controller.is_token_valid(token=token,
                                                              email=email)

        cache.set(cache_key, valid_hash, timeout=86400)  # Cache for 24 hours
        if valid_hash:
            return f(*args, **kwargs)
        else:
            return jsonify({"message": "Invalid or missing token"}), 403
    return decorated_function


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
        email = request.args.get('email', '').strip()
        if not is_email_allowed(email, os.getenv('AUTH_EMAIL_ALLOWLIST', '')):
            return jsonify({'error': 'Invalid email domain'}), 400
        if is_email_dry_run():
            current_app.logger.info('Magic link suppressed because EMAIL_DRY_RUN is enabled')
            return jsonify({'message': 'Email dry-run enabled; no email sent'}), 202
        # Generate hash via the controller
        hash_auth = authentication_controller.generate_hash

        # Save the hash and email in the database
        authentication_controller.insert_token(email, hash_auth)

        # Send the magic link via email
        magic_link = f"{os.getenv('REACT_APP')}/auth/callback?email={email}&hash={hash_auth}"
        if os.getenv('FLASK_ENV') == 'development':
            return jsonify({'magic_link': magic_link}), 201
        try:
            send_response = send_magic_link(email, email.split('@')[0], magic_link)
            if send_response.status_code not in (200, 201, 202):
                return jsonify({'error': 'Email sender service unavailable: failed to send email'}), 503
        except Exception as e:
            return jsonify({'error': str(e)}), 503


        return jsonify({'message': 'Magic link sent successfully'}), 201

    @staticmethod
    @auth_bp.route('/auth/validate', methods=['GET'])
    @cache.cached(timeout=43200,query_string=True)  # Cache for 12 hours
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
