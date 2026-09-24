# Apis Internas da cluster (GraphQL e RestAPI)

## Subindo em produção

```bash
poetry install

poetry run gunicorn -w 2 -b 0.0.0.0:5081 main:internal_apis
```

## Pré-requisitos
tenha certeza que o redis está rodando na porta 6379
```bash 
docker compose up -d
```

## Com Docker

```bash
docker build -t labtech-internal-apis .
docker run --rm -p 5081:5081 -e MONGO_URI=... -e MONGO_DATABASE=... -e REDIS_URL=... labtech-internal-apis
```
