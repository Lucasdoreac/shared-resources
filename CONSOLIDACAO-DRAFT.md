# Consolidação shared-resources — inventário de trabalho (draft)

Esta PR é parcial. Não é uma consolidação pronta para merge ou deploy. Não foram integrados os históricos das branches de origem. A única mudança funcional aqui é o limite de carga horária no modelo de disciplinas, adaptado de `542965762a1133b3ab2d79f6b4abbd2b1cacc223` (integration/catalog); seu histórico original continua disponível na branch de origem. Os testes novos validam 9, 10, 20 e 60 horas sem banco de dados.

## Bases verificadas

- `main` e `consolidate/2026-10-19`: `1707c8ea6d9f76e27378f693bbb2e5e37585ac47`.
- `integration/auth`: `3911f7bc314c16425c4e8323a8b207a556533fa7`.
- `integration/catalog`: `5ae6e46f6bde9704d8f8925788594e960dc52eb5`.
- `promote/catalog` e `candidate/catalog-2026-10-03`: `9539c752489d98b90ee1d32acccae4c0e6f4c2bb`. Comparadas a `integration/catalog`, diferem apenas em `internal_apis/poetry.lock`; os sete commits exclusivos de promote foram identificados como patch-equivalentes por `git cherry`. Não reaplicar ambos cegamente.
- Base comum de main com ambas integration: `8d89e7176162654a4e870ceea13bf3e844b25faa`. Main tem 22 commits e auth 21, ou catálogo 18, de cada lado desde essa base (incluindo merges).
- `pr/SR-5` (`81b049c`) contém a cadeia `pr/SR-3`/`pr/SR-4`, incluindo weekdays e seu PATCH, consulta GraphQL e busca por nome. Não presumir que esteja contida nas branches integration: comparar semanticamente as variantes antes de aplicar.
- `test/repair-internal-api-tests` (`6578951`), branches individuais de auth/catálogo, `8-backpressure` e `31-aplicando-o-graphql` requerem comparação de conteúdo e ancestralidade; nomes de commits semelhantes não provam equivalência. `git cherry` também não detectou equivalência de patch de SR-5 contra integration/catalog; isso não prova ausência de equivalência semântica.

## Conflitos detectados, sem merge

`git merge-tree --write-tree main integration/auth`: quatro arquivos: `auth_service/.dockerignore`, `Dockerfile`, `poetry.lock`, `pyproject.toml`.

`git merge-tree --write-tree main integration/catalog`: treze arquivos: `internal_apis/.dockerignore`, `.env.example`, `Dockerfile`, `main.py`, `poetry.lock`, `pyproject.toml`, `src/BLL/schema.py`, `src/SLL/__init__.py`, `src/SLL/graphql.py`, `src/Tests/test_models.py`, `src/config_module.py`, `src/utils/auth.py`, `src/utils/log_functions.py`.

Conflitos textuais são apenas parte da revisão: uma mesclagem limpa não garante preservação de comportamento, contratos ou segurança. Não foram resolvidos aqui.

## Decisões e preservações necessárias

1. Preservar as correções já em main: autorização e regra única para desativação de professor e leituras coerentes (`c505928`), inicialização tolerante a variáveis opcionais e exposição de `internal_apis` (`ecb18b6`), `REDIS_URL` no limitador individual (`366e53c`), worker global isolado (`6afc663`), defaults 125/0.3 (`d254dd2`), coleta de testes e requisito Python da raiz. Conferir a compatibilidade com os Dockerfiles e locks novos, sem sobrescrever uma versão inteira.
2. Revisar Auth como conjunto: login de uso único e sessão, logout, allowlist, retorno de link somente em desenvolvimento, política CORS, cabeçalhos, envio Brevo/logo, proteção de tokens e limites por cliente/e-mail. Verificar explicitamente o limite de confiança em `True-Client-IP` e o comportamento do cache compartilhado e fallback local em múltiplos processos. Não incorporar só uma parte de uma sequência de segurança interdependente.
3. Revisar Catálogo como conjunto: API key obrigatória e sem log de segredo, mínimo de 24 caracteres da chave, erro JSON e headers permitidos, `/health`, logs sem dados pessoais, cache e namespace, GraphQL e dependências, 10 horas. A branch de catálogo torna o catálogo público read-only; isso pode conflitar com `PATCH /restapi/offers/<id>/weekdays` de SR-5 e com operações de escrita/desativação existentes em main. Definir separação de rotas públicas e internas e contratos com consumidores antes de remover ou expor escrita; não escolher unilateralmente.
4. Conferir semanticamente SR-3/4/5, busca, weekdays, relação campus no GraphQL e contratos com python-services; verificar também alterações específicas de `31-aplicando-o-graphql` e `8-backpressure` antes de descartá-las. Não aplicar commits equivalentes duas vezes. A regra de 10 horas foi reportada como oficial no commit de origem; confirmar com responsável/fonte de dados antes do merge.
5. Resolver locks e versões Python/Docker/CI de cada serviço com ferramentas e restrições consistentes. O teste local abaixo não usa o lock: não substitui CI nem garante compatibilidade de dependências ou de imagens.
6. Integrar em etapas revisáveis, preferencialmente preservando pais/histórico das origens quando viável; esta PR não registra seus commits como ancestrais. Acrescentar testes de contratos, autorização, regressão da desativação e backpressure, concorrência/cache, GraphQL e read-only. Validar tudo com credenciais e serviços simulados, sem dados reais, restore destrutivo, merge ou deploy.

## Verificação realizada

Em Python 3.14.4, venv isolada com pytest 9.2.0, mongoengine 0.29.3, mongomock 4.3.0 e pymongo 4.20.1, sem instalar o lock do projeto:

```sh
cd internal_apis
env -i PATH=/tmp/shared-consolidation-testenv/bin:/usr/bin:/bin PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /tmp/shared-consolidation-testenv/bin/python -m pytest -p no:cacheprovider -q src/Tests/test_discipline_workload.py src/Tests/test_models.py
```

Resultado: 8 passaram, um aviso de depreciação de `uuidRepresentation`. Os testes de `test_models.py` usam mongomock; os novos usam apenas validação do modelo. Antes da alteração, o teste de 10 horas falhou como esperado. Não foram executados testes completos, build de imagem ou integração com serviços.
