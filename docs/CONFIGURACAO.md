# Configuração do shared-resources (auth_service e internal_apis)

Cada serviço tem seu `.env.example` com exatamente as variáveis que o código lê.
Garantido por teste nos dois: `internal_apis/src/Tests/test_env_example.py` e
`auth_service/tests/test_env_example.py` (`dev-local/run-tests.sh internal|auth`).

Coluna **Prod**: ✅ obrigatória em produção · ⚠️ tem padrão que não serve em produção · — opcional.

## auth_service (login por link mágico)

| Variável | Prod | Exemplo | Para que serve | Se faltar |
|---|---|---|---|---|
| `FLASK_ENV` | — | `production` | `development` é pré-requisito para `AUTH_DEV_RETURN_LINK`. | Vale `production`. |
| `AUTH_DEV_RETURN_LINK` | ⚠️ **nunca `true`** | `false` | Com `true` **e** `FLASK_ENV=development`, `POST /auth/send-link` devolve o link de login na resposta, sem e-mail (usado no dev-local e nos testes de tela). | Vale `false`: o link vai por e-mail. |
| `REACT_APP` | ✅ | `https://reservas.exemplo` | Endereço público do frontend: base do link de login. | Link vira `None/auth/callback?...` e não abre. |
| `MONGO_URI` ou `MONGO_HOST`/`MONGO_USERNAME`/`MONGO_PASSWORD` | ✅ | — | MongoDB (tokens de login). | Não conecta. |
| `MONGO_DATABASE` | ✅ | `rooms-reservation-app` | Banco. | Falha ao gravar o token. |
| `REDIS_URL` | ✅ | `redis://redis:6379/0` | Cache dos tokens de login. | Tenta `redis://localhost:6379/0`. |
| `CLOUD_FUNCTION_URL` / `CLOUD_FUNCTION_API_KEY` | ✅ | — | Função que entrega o e-mail com o link. | Login responde 503 (e-mail não sai). |
| `MINIO_URL` | — | `https://arquivos.exemplo:9000` | Endereço público do MinIO, com esquema: ícone do e-mail de login. | E-mail sem ícone. |

## internal_apis (catálogo: cursos, salas, professores, ofertas)

| Variável | Prod | Exemplo | Para que serve | Se faltar |
|---|---|---|---|---|
| `MONGO_URI` | ✅ | — | MongoDB do catálogo. | Não conecta. |
| `MONGO_DATABASE` | ✅ | `rooms-reservation-app` | Banco. | Falha ao consultar. |
| `API_KEY_LIST` | ✅ | `chave1,chave2` | Chaves aceitas no header `x-api-key`. Hoje só o `POST /offers` exige. | O serviço **não sobe** (lida na importação). |
| `REDIS_URL` | ✅ | `redis://redis:6379/0` | Cache (Flask-Caching). | Tenta `redis://localhost:6379/0`. |
| `SERVER_NAME` | — | `catalogo.exemplo` | Host público do Flask. | Aceita qualquer `Host`. |

## Problemas conhecidos
- ~~Login aberto em modo development~~ **resolvido:** antes bastava `FLASK_ENV=development`
  para o link de login voltar na resposta; agora exige também `AUTH_DEV_RETURN_LINK=true`,
  desligada por padrão e ligada só no dev-local.
- **Catálogo aberto:** só o `POST /offers` pede `x-api-key`; todos os GET (inclui professores)
  respondem a quem alcança a porta. PR #26 (backpressure/API key) trata parte disso.
