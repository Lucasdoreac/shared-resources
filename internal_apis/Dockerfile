FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONPATH=/internal_apis/src

WORKDIR /internal_apis

RUN pip install --no-cache-dir "poetry==2.1.2"

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-root --only main

FROM base AS test-dependencies
RUN poetry install --no-interaction --no-root --with dev

FROM test-dependencies AS tests
COPY . .
CMD ["poetry", "run", "pytest", "src/Tests", "backpressure"]

FROM base AS runtime
COPY . .
EXPOSE 5081
CMD ["sh", "-c", "PYTHONPATH=src exec poetry run gunicorn -w 2 -b 0.0.0.0:5081 main:internal_api"]
