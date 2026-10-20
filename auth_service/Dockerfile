FROM python:3.13.3-slim

WORKDIR /auth_service

COPY . .

RUN pip install poetry

# Adds poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Make poetry not run in other virtual enviroment (run in his own container)
RUN poetry config virtualenvs.create false

RUN poetry install --no-root

EXPOSE 5050

CMD ["poetry", "run", "gunicorn", "-w", "2", "-b", "0.0.0.0:5050", "main:auth_app"]
## Comando que será executado
    # "poetry": Chama o Poetry
    # "run": Executar os comandos dentro do ambiente virtual do poetry
    # "gunicorn": servidor HTTP para aplicações Python WSGI
    # "-w" e "2": Vai definir o número de processos que o Gunicorn vai usar
    # "-b" e "0.0.0.0:5050": Fazer com que Gunicorn funcione em todos os endereções IP
    # "main:internal_api" Qual aplicação rodar - (main-> nome do arquivo python & auth_app-> nome da variável do app)
    