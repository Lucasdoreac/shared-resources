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