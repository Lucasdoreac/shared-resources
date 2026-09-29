# Serviço de Autenticação compartilhado da cluster

## Subindo em produção

```bash
poetry install

poetry run gunicorn -w 2 -b 0.0.0.0:5050 main:auth_app 
```

## Pré-requisitos
tenha certeza que o redis está rodando na porta 6379
```bash 
docker compose up -d
```
# Staging email allowlist

`AUTH_EMAIL_ALLOWLIST` accepts a comma-separated list of exact recipient
addresses in addition to the standard `@udf.edu.br` domain. Set the developer
address only in the Render Staging service; leave this value empty in
Production. This controls who can request a login link, not which email
provider sends it. Staging must use a separate sender/sink before real email
delivery is enabled.

Set `EMAIL_DRY_RUN=true` in Staging while no isolated sender or test sink is
configured. The Auth endpoint then returns HTTP 202 without storing an
authentication token or calling the email provider. Keep it false in
Production. A dry-run proves that the request is safely suppressed; it does
not prove email delivery or a complete login flow.
