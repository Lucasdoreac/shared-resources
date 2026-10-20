FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /auth_service

RUN pip install --no-cache-dir "poetry==2.1.2"

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-root --with dev

COPY . .

EXPOSE 5050

CMD ["poetry", "run", "gunicorn", "-w", "2", "-b", "0.0.0.0:5050", "main:auth_app"]
