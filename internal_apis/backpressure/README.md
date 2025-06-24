# Backpressure API (Leaky Bucket)

## Como rodar os testes do backpressure no Docker

Este projeto já está pronto para rodar os testes automatizados usando Docker, sem necessidade de instalar dependências Python, RabbitMQ ou Redis manualmente.

### Passos rápidos:

1. **Tenha o Docker e Docker Compose instalados**
   - [Download Docker Desktop](https://www.docker.com/products/docker-desktop)

2. **Abra o terminal na raiz do projeto** (onde está o arquivo `docker-compose.yml`).

3. **Construa a imagem de testes (apenas na primeira vez ou quando mudar dependências):**
   ```sh
   docker compose build tests
   ```

4. **Execute todos os testes do backpressure:**
   ```sh
   docker compose run --rm tests poetry run pytest backpressure/
   ```

5. **Para rodar um teste específico:**
   ```sh
   docker compose run --rm tests poetry run pytest backpressure/backpressure_leaky_bucket_test.py::test_requests_leaks
   ```
   > Substitua pelo nome do arquivo e da função de teste desejada.

---

## Dicas e observações
- Não é necessário instalar Python, Poetry, RabbitMQ ou Redis localmente.
- O comando de build pode demorar na primeira vez, pois instala todas as dependências.
- Para rodar novamente os testes, basta repetir o comando do passo 4 ou 5 (sem precisar rebuildar, a não ser que mude dependências).
- Se adicionar novas dependências Python, rode novamente o passo 3.
- Se quiser rodar outros arquivos de teste, basta trocar o caminho no comando do passo 5.

---

## Exemplo de comandos úteis

- Rodar todos os testes:
  ```sh
  docker compose run --rm tests poetry run pytest backpressure/
  ```
- Rodar um teste específico:
  ```sh
  docker compose run --rm tests poetry run pytest backpressure/backpressure_leaky_bucket_test.py::test_requests_above_limit
  ```
- Rodar outro arquivo de teste:
  ```sh
  docker compose run --rm tests poetry run pytest backpressure/backpressure_test_tokenbucket.py
  ```

---

Se tiver qualquer problema, confira se o Docker está rodando e se você está na pasta correta. Para dúvidas ou erros, consulte este README ou peça ajuda ao time!
