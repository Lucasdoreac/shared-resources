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

`AUTH_EMAIL_ALLOWLIST` accepts exact recipient addresses in addition to the
standard `@udf.edu.br` domain. Keep developer-only addresses in Staging and
leave the value empty in Production.

For direct Brevo delivery, configure `BREVO_API_KEY` and a sender address
already verified in Brevo using `BREVO_SENDER_EMAIL`; `BREVO_SENDER_NAME` is
optional. When `BREVO_API_KEY` is present, Auth uses the Brevo transactional
email API. Otherwise it retains the legacy `CLOUD_FUNCTION_URL` sender.

Keep `EMAIL_DRY_RUN=true` in Staging until the provider and sender are
verified. Dry-run returns HTTP 202 without storing a token or calling a
provider; it does not prove email delivery or a complete login flow.
