# Backpressure API (Leaky Bucket)

## Instalação e Execução com Docker

Todo o ambiente (RabbitMQ, Redis e dependências Python) é orquestrado via Docker Compose. Não é necessário instalar nada manualmente.

### Passos para subir o ambiente

1. **Pré-requisitos:**
   - [Docker Desktop](https://www.docker.com/products/docker-desktop) instalado

2. **Suba os serviços necessários:**
   ```sh
   docker compose up -d rabbitmq redis-local
   ```

3. **Rode os testes:**
   ```sh
   docker compose up --build tests
   ```
   Ou siga as instruções abaixo para rodar testes específicos.

> **Obs:** Todo o ambiente é isolado e gerenciado via Docker. Não é necessário instalar RabbitMQ, Redis ou dependências Python manualmente.

---

## Como aplicar o leaky bucket em um endpoint Flask

```python
from leaky_bucket import leaky_bucket
from flask import Flask, jsonify

app = Flask(__name__)

@leaky_bucket(capacity=10, leak_rate=1)
@app.route('/meu-endpoint')
def meu_endpoint():
    return jsonify({"mensagem": "Requisição aceita!"})

if __name__ == '__main__':
    app.run(debug=True)
```

Neste exemplo, o decorator `@leaky_bucket` limita o número de requisições ao endpoint `/meu-endpoint` a 10, vazando 1 requisição por segundo. Caso o limite seja excedido, as requisições adicionais serão rejeitadas até que haja espaço disponível no bucket.

- `capacity`: número máximo de requisições no bucket (capacidade da fila)
- `leak_rate`: quantas requisições são liberadas por segundo

---

## Como rodar testes individuais com Docker

Utilize o serviço `tests` do docker-compose. Você pode especificar o arquivo ou função de teste desejada:

- Rodar um arquivo de teste específico:
  ```sh
  docker compose run --rm tests poetry run pytest backpressure/backpressure_leaky_bucket_test.py
  ```
- Rodar uma função de teste específica:
  ```sh
  docker compose run --rm tests poetry run pytest backpressure/backpressure_leaky_bucket_test.py::test_requests_leaks
  ```
- Rodar outro arquivo de teste:
  ```sh
  docker compose run --rm tests poetry run pytest backpressure/backpressure_test_tokenbucket.py
  ```
- Rodar todos os testes do backpressure:
  ```sh
  docker compose run --rm tests poetry run pytest backpressure/
  ```

> **Dica:** Substitua o caminho e o nome da função conforme o teste que deseja executar.

---

## Rodando cada teste do arquivo backpressure_leaky_bucket_test.py

| Função de Teste            | Comando para rodar no Docker                                                                                 |
|---------------------------|-------------------------------------------------------------------------------------------------------------|
| test_requests_above_limit | `docker compose run --rm tests poetry run pytest backpressure/backpressure_leaky_bucket_test.py::test_requests_above_limit` |
| test_requests_leaks       | `docker compose run --rm tests poetry run pytest backpressure/backpressure_leaky_bucket_test.py::test_requests_leaks`       |

---

## Observações
- Certifique-se de que o módulo `leaky_bucket` está corretamente implementado e importado.
- Ajuste os parâmetros `capacity` e `leak_rate` conforme a necessidade do seu endpoint.
- Você pode adicionar novos testes no arquivo e rodá-los individualmente seguindo o mesmo padrão de comando.
