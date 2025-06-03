FROM python:3.13.3-slim

WORKDIR /internal_apis

COPY . . 

RUN pip install poetry

ENV PATH="/root/.local/bin:$PATH"

RUN poetry config virtualenvs.create false

RUN poetry install --no-root

EXPOSE 5081


CMD ["sh", "-c", "PYTHONPATH=src poetry run gunicorn -w 2 -b 0.0.0.0:5081 main:internal_api"]
