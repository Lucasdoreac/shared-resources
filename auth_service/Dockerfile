# Trazido do PR #25 (24-dockerizar-as-apis-no-shared-resources, aberto,
# nunca mergeado) e adaptado ao código atual da main (sem os renomes que o
# PR fazia em internal_apis/main.py — aqui a variável do app já é
# `auth_app`, que é o que o pyproject.toml e main.py já usam).
FROM python:3.13.3-slim

WORKDIR /auth_service

COPY . .

RUN pip install poetry

ENV PATH="/root/.local/bin:$PATH"

# Roda no próprio container, sem criar outro virtualenv dentro dele.
RUN poetry config virtualenvs.create false

RUN poetry install --no-root

EXPOSE 5050

CMD ["poetry", "run", "gunicorn", "-w", "2", "-b", "0.0.0.0:5050", "main:auth_app"]
