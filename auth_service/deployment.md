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

# Limites de login por pessoa

Falhas de validação e pedidos de link são contados por (e-mail, cliente) e por e-mail
(`auth_routes.py`). Atrás do API todo pedido chega do endereço do próprio API, então o API
repassa o cliente em `X-Client-IP` junto de `X-Forward-Key`, e o Auth só confia no cabeçalho
quando a chave confere (`AUTH_FORWARD_KEY`, igual nos dois serviços, comparada em tempo
constante). Sem a variável, ou com chave errada, o cabeçalho é ignorado e vale o endereço de
conexão. Configure primeiro em Staging; o limite grosso por endereço de conexão dos pedidos de
link (`send:ip`) continua no endereço de conexão. `TRUSTED_PROXY_HOPS` (padrão 1, correto no
Render) diz quantos proxies acrescentam ao `X-Forwarded-For`.
