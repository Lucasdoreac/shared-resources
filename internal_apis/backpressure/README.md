# Backpressure API (Leaky Bucket)

## O que é o sistema de Leaky Bucket?

O algoritmo de Leaky Bucket é uma estratégia de controle de fluxo e limitação de requisições (rate limiting). Ele funciona como um balde com um furo: as requisições entram no balde (bucket) e "vazam" em uma taxa constante. Se o balde enche (ultrapassa a capacidade), as requisições excedentes são descartadas ou bloqueadas. Isso garante que o sistema não seja sobrecarregado por picos de tráfego.

Neste projeto, existem dois tipos de buckets:

## 1. Leaky Bucket Global (RabbitMQ)
- **Finalidade:** Limita o número total de requisições aceitas por todos os usuários em um determinado endpoint ou aplicação.
- **Implementação:** Arquivo `leaky_bucket_rabbitmq.py`.
- **Backend:** RabbitMQ (fila com tamanho máximo).
- **Como usar:**
  - O uso automático via `@request.before_request` foi removido por questões de segurança. Agora, o controle global deve ser adicionado **manualmente** em cada endpoint desejado, usando o decorator:
    ```python
    from backpressure.leaky_bucket_rabbitmq import LeakyBucketRabbitMQ
    @LeakyBucketRabbitMQ.add_to_global_leaky_bucket()
    def meu_endpoint():
        ...
    ```
  - Os parâmetros do bucket global (capacidade, nome da fila, taxa de vazamento) **são definidos via variáveis de ambiente** no arquivo `.env`:
    - `GLOBAL_BUCKET_SIZE`: capacidade máxima do bucket global (ex: 125)
    - `GLOBAL_QUEUE_NAME`: nome da fila no RabbitMQ (ex: global)
    - `GLOBAL_LEAK_RATE`: taxa de vazamento do bucket global (ex: 0.3)
  - **Não é necessário passar parâmetros no decorator**. O sistema buscará as configurações automaticamente do `.env`.

---

## 2. Leaky Bucket Individual (Redis)
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

---

## Como adicionar os buckets aos endpoints
- Para controle individual, adicione o decorator `@LeakyBucket.individual_leaky_bucket(...)` ao endpoint desejado.
- Para controle global, adicione o decorator `@LeakyBucketRabbitMQ.add_to_global_leaky_bucket()` ao endpoint.
- **Ordem recomendada:**
  ```python
  @LeakyBucketRabbitMQ.add_to_global_leaky_bucket()
  @LeakyBucket.individual_leaky_bucket(...)
  def meu_endpoint():
      ...
  ```

## ATENÇÃO CRÍTICA SOBRE ORDEM DOS DECORATORS
> **IMPORTANTE:** Caso você utilize **os dois sistemas de leaky bucket juntos** (global e individual) em um mesmo endpoint, **O DECORATOR DO INDIVIDUAL LEAKY BUCKET DEVE SER SEMPRE O PRIMEIRO** (ou seja, deve estar mais "próximo" da função do endpoint) e o decorator do global leaky bucket deve vir depois.
>
> **Exemplo correto:**
> ```python
> @LeakyBucketRabbitMQ.add_to_global_leaky_bucket()
> @LeakyBucket.individual_leaky_bucket(...)
> def meu_endpoint():
>     ...
> ```
>
> **Se a ordem for invertida, podem ocorrer graves vulnerabilidades de rate limiting, permitindo que usuários burlem o controle global!**
>
> **NUNCA inverta essa ordem!**

---

## Configuração do sistema global via .env
- As informações da fila global do leaky bucket são definidas no arquivo `.env` na raiz do projeto:
  ```env
  GLOBAL_BUCKET_SIZE=125
  GLOBAL_QUEUE_NAME=global
  GLOBAL_LEAK_RATE=0.3
  ```
- Para alterar a capacidade, nome da fila ou taxa de vazamento, basta editar o `.env` e reiniciar o serviço.
- **Atenção:** O RabbitMQ não permite alterar argumentos de uma fila já existente. Se mudar o `GLOBAL_BUCKET_SIZE` ou outros argumentos, altere também o `GLOBAL_QUEUE_NAME` para evitar conflitos, ou exclua a fila antiga manualmente.

---

# Testes automatizados

## Estrutura dos testes
Os testes automatizados do sistema de backpressure estão localizados em:
- `backpressure/test_global_leaky_bucket.py` (testes do bucket global)
- `backpressure/test_individual_leaky_bucket.py` (testes do bucket individual)

Os testes cobrem cenários de limite, vazamento, bloqueio e funcionamento dos buckets.

## Como rodar os testes

### Pré-requisitos
- Python 3.11+ instalado localmente.
- Instale as dependências do projeto com Poetry:
  ```sh
  poetry install
  ```
- O serviço do RabbitMQ deve estar rodando em um container Docker (ou localmente) e acessível conforme as configurações do `.env`.
- O Redis **não é necessário**: os testes usam `fakeredis` (mock em memória).

### Rodando testes pelo PyCharm (recomendado)
- Você pode rodar qualquer teste individualmente pelo próprio PyCharm, clicando no ícone de execução (▶️) que aparece ao lado da função de teste ou do nome do arquivo de teste.
- Certifique-se de que o interpretador Python do PyCharm está configurado para usar o ambiente virtual criado pelo Poetry (ou o Python correto).
- O RabbitMQ deve estar rodando normalmente em Docker.

### Rodando os testes com o poetry via terminal
1. Certifique-se de que o RabbitMQ está rodando (exemplo usando Docker Compose):
   ```sh
   docker compose up -d rabbitmq
   ```
2. Execute os testes (com Poetry):
   ```sh
   poetry run pytest backpressure/
   ```
3. Para rodar um teste específico:
   ```sh
   poetry run pytest backpressure/test_global_leaky_bucket.py::test_nome_do_teste
   ```
   Substitua pelo nome do arquivo e da função de teste desejada.


### Dicas
- Não é necessário rodar nenhum container de testes, apenas o RabbitMQ.
- Se mudar as configurações do `.env`, reinicie o RabbitMQ e os testes.
- Consulte os logs do sistema para mensagens de erro detalhadas.


## Observações finais
- O sistema de backpressure é fundamental para garantir a resiliência da API.
- Sempre respeite a ordem dos decorators para evitar vulnerabilidades.
- Mantenha o `.env` atualizado conforme a configuração desejada do bucket global.
- Para dúvidas ou problemas, consulte este README ou peça suporte ao time.
