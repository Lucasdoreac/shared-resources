# Trazido do PR #25 (24-dockerizar-as-apis-no-shared-resources, aberto,
# nunca mergeado) e adaptado ao código atual da main: o PR renomeava a
# variável do app em main.py de `internal_apis` para `internal_api`; aqui
# mantemos o nome atual (`internal_apis`) pra não introduzir um rename sem
# necessidade.
FROM python:3.13.15-slim

WORKDIR /internal_apis

COPY . .

RUN pip install poetry

ENV PATH="/root/.local/bin:$PATH"

RUN poetry config virtualenvs.create false

RUN poetry install --no-root

EXPOSE 5081

CMD ["sh", "-c", "PYTHONPATH=src poetry run gunicorn -w 2 -b 0.0.0.0:5081 main:internal_apis"]
