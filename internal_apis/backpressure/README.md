# Backpressure API (Leaky Bucket)

## O que é o sistema de Leaky Bucket?

O algoritmo de Leaky Bucket é uma estratégia de controle de fluxo e limitação de requisições (rate limiting). Ele funciona como um balde com um furo: as requisições entram no balde (bucket) e "vazam" em uma taxa constante. Se o balde enche (ultrapassa a capacidade), as requisições excedentes são descartadas ou bloqueadas. Isso garante que o sistema não seja sobrecarregado por picos de tráfego.

Neste projeto, existem dois tipos de buckets:

### 1. Leaky Bucket Global (RabbitMQ)
- **Finalidade:** Limita o número total de requisições aceitas por todos os usuários em um determinado endpoint ou aplicação.
- **Implementação:** Arquivo `leaky_bucket_rabbitmq.py`.
- **Backend:** RabbitMQ (fila com tamanho máximo).
- **Como usar:**
  - Para aplicar globalmente a todos os endpoints Flask:
    ```python
    from backpressure.leaky_bucket_rabbitmq import LeakyBucketRabbitMQ
    LeakyBucketRabbitMQ.register_global_leaky_bucket(app, bucketcapacity=10)
    ```
  - Para aplicar em um endpoint específico:
    ```python
    from backpressure.leaky_bucket_rabbitmq import LeakyBucketRabbitMQ
    @LeakyBucketRabbitMQ.rate_limit_by_leaky_bucket(bucketcapacity=10)
    def meu_endpoint():
        ...
    ```
- **Configuração:** O parâmetro `bucketcapacity` define o número máximo de requisições simultâneas permitidas. O nome da fila pode ser customizado via `queue_name`.

### 2. Leaky Bucket Individual (Redis)
- **Finalidade:** Limita o número de requisições por usuário (identificado por IP ou outro identificador).
- **Implementação:** Arquivo `individual_leaky_bucket.py`.
- **Backend:** Redis (armazenamento de tokens por IP).
- **Como usar:**
    ```python
    from backpressure.individual_leaky_bucket import LeakyBucket
    @LeakyBucket.individual_leaky_bucket(bucketcapacity=5, leakrate=1, keytimeout=60)
    def meu_endpoint():
        ...
    ```
  - `bucketcapacity`: número máximo de requisições permitidas por usuário.
  - `leakrate`: intervalo (em segundos) para "vazamento" de cada token.
  - `keytimeout`: tempo de expiração do registro no Redis (em segundos).

## Como adicionar um bucket individual a uma requisição
Basta adicionar o decorator `@LeakyBucket.individual_leaky_bucket(...)` ao endpoint desejado, conforme exemplo acima. O controle é feito por IP do cliente (ou pelo header `X-Forwarded-For`).

## Como mudar o bucket global
Para alterar o bucket global, basta mudar o valor de `bucketcapacity` na chamada de `register_global_leaky_bucket` ou no decorator `@LeakyBucketRabbitMQ.rate_limit_by_leaky_bucket`.

Você também pode mudar o nome da fila (`queue_name`). **Atenção:**
- O RabbitMQ não permite alterar os argumentos de uma fila já existente (por exemplo, mudar o `bucketcapacity` ou o argumento `x-max-length` de uma fila que já foi criada). Se tentar mudar o `bucketcapacity` para um valor diferente usando o mesmo `queue_name`, ocorrerá um erro do tipo `PRECONDITION_FAILED`.
- Se você mudar o `queue_name` para um nome novo, uma nova fila será criada normalmente. Se usar um nome já existente, os argumentos devem ser compatíveis.

### Erros comuns ao mudar bucketcapacity ou queue_name
- **PRECONDITION_FAILED:**
  - Ocorre quando tenta-se declarar uma fila RabbitMQ com o mesmo nome (`queue_name`) mas com argumentos diferentes (ex: mudou o `bucketcapacity`).
  - Solução: Use um novo nome de fila (`queue_name`) ou exclua a fila antiga manualmente no RabbitMQ antes de mudar o argumento.
    - Para excluir uma fila manualmente pelo terminal, execute:
      ```sh
      docker exec -it <nome_do_container_rabbitmq> rabbitmqctl delete_queue <nome_da_fila>
      ```
      Substitua `<nome_do_container_rabbitmq>` pelo nome do seu container RabbitMQ (ex: `rabbitmq`) e `<nome_da_fila>` pelo nome da fila que deseja remover.
- **Fila "presa" com configuração antiga:**
  - Se você rodou testes ou subiu o sistema com um `bucketcapacity` e depois mudou o valor, a fila antiga pode continuar existindo com a configuração anterior, causando erros.
  - Solução: Limpe as filas antigas no RabbitMQ ou sempre use nomes de fila únicos para cada configuração.
- **Erros de conexão:**
  - Certifique-se de que o RabbitMQ está rodando e acessível. Erros de conexão podem aparecer como `ConnectionRefusedError` ou similares.

#### Recomendações
- Sempre que mudar o `bucketcapacity`, prefira mudar também o `queue_name` para evitar conflitos.
- Para ambientes de teste, use nomes de fila exclusivos ou limpe as filas antigas antes de rodar novamente.
- Consulte os logs do sistema para mensagens de erro detalhadas.

## Onde cada bucket está implementado
- **Leaky Bucket Global:** `backpressure/leaky_bucket_rabbitmq.py`
- **Leaky Bucket Individual:** `backpressure/individual_leaky_bucket.py`

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
   docker compose run --rm tests poetry run pytest backpressure/test_global_leaky_bucket.py::test_requests_leaks
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
  docker compose run --rm tests poetry run pytest backpressure/test_global_leaky_bucket.py::test_requests_above_limit
  ```
- Rodar outro arquivo de teste:
  ```sh
  docker compose run --rm tests poetry run pytest backpressure/test_individual_leaky_bucket.py
  ```

---

## Como testar o Individual Leaky Bucket

Para testar o bucket individual (Redis), utilize os testes automatizados já presentes no projeto:

```sh
docker compose run --rm tests poetry run pytest backpressure/test_individual_leaky_bucket.py
```

Você também pode criar requisições manuais para o endpoint protegido pelo decorator `@LeakyBucket.individual_leaky_bucket` e observar o bloqueio após exceder o limite configurado.

Se tiver qualquer problema, confira se o Docker está rodando e se você está na pasta correta. Para dúvidas ou erros, consulte este README ou peça ajuda ao time!
