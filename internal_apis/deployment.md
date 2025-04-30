# Apis Internas da cluster (GraphQL e RestAPI)

## Subindo em produção

```bash
poetry install

poetry run gunicorn -w 2 -b 0.0.0.0:5081 main:internal_api 
```

## Pré-requisitos
tenha certeza que o redis está rodando na porta 6379
```bash 
docker compose up -d
```