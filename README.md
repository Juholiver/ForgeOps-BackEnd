# ForgeOps Backend

API do ForgeOps — plataforma de monitoramento e observabilidade de APIs HTTP.
FastAPI + SQLAlchemy 2 (async) + Alembic + PostgreSQL, com workers Celery/RabbitMQ,
cache Redis, métricas Prometheus e dashboards Grafana.

> Este repositório é a metade backend do projeto ForgeOps. O frontend (React) vive em
> [`forgeops-frontend`](https://github.com/OWNER/forgeops-frontend) e os dois stacks se
> encontram na rede Docker compartilhada `forgeops`.

## Stack

| Camada | Tecnologia |
|--------|-----------|
| API | Python 3.12+, FastAPI, Pydantic |
| Banco | PostgreSQL 16 (fallback SQLite para dev local) |
| Cache / locks | Redis 7 |
| Filas | RabbitMQ + Celery worker/beat |
| Migrações | Alembic |
| Observabilidade | Prometheus, Grafana, Structured Logging (structlog) |
| Testes | Pytest + pytest-asyncio + coverage |
| Qualidade | Ruff (lint/format), MyPy strict |
| Deploy | Docker, Docker Compose, GitHub Actions |

## Requisitos

- Python 3.12+
- (opcional) Docker + Docker Compose v2.24.4+ para subir a stack completa

## Executar localmente

### Opção A — desenvolvimento leve (sem Docker, SQLite)

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -e ".[dev]"

cp .env.example .env
# edite .env e deixe DB_BACKEND=sqlite para rodar sem PostgreSQL

uvicorn app.main:app --reload
```

A API sobe em `http://localhost:8000` (docs em `/docs`).

### Opção B — stack completa (Docker Compose)

```bash
# uma única vez por máquina: rede compartilhada com o frontend
docker network inspect forgeops >/dev/null 2>&1 || docker network create forgeops

cp .env.example .env
docker compose up -d --build
```

Serviços: `backend` (:8000), `worker`, `scheduler`, `postgres` (:5432), `redis` (:6379),
`rabbitmq` (:5672/:15672), `prometheus` (:9090), `grafana` (:3000).

Para o frontend, repositório [`forgeops-frontend`](https://github.com/OWNER/forgeops-frontend).

## Variáveis de ambiente

O arquivo [`.env.example`](.env.example) documenta todas as variáveis. Principais:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `APP_ENV` | `development` | Ambiente (`production` ativa validação fail-fast de secrets) |
| `APP_SECRET_KEY` | `change-me-in-production` | Chave JWT (**obrigatória em produção**) |
| `DB_BACKEND` | `postgres` | `postgres` ou `sqlite` (dev sem Docker) |
| `POSTGRES_*` | `forgeops` | Credenciais/host do banco |
| `RABBITMQ_*` | `forgeops` | Credenciais/host da fila |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Origens permitidas (use o domínio do frontend em produção) |
| `RUN_MIGRATIONS` | `0` | `1` executa `alembic upgrade head` na subida do container |
| `BACKEND_IMAGE` | `forgeops-backend:local` | Imagem usada pelo compose (definida pelo CD) |

Produção: copie `.env.example` para `.env.prod`, preencha os secrets
(`APP_SECRET_KEY`, `POSTGRES_PASSWORD`, `RABBITMQ_PASSWORD` com `openssl rand -hex 32/16`)
e rode com o overlay:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d
```

O overlay remove todas as portas públicas (serviços ficam só na rede interna) e fixa
`restart: unless-stopped` — o TLS/HTTPS é terminado pelo stack do `forgeops-frontend`.

## Testes e qualidade

```bash
# lint
ruff check .
ruff format --check .

# tipagem
mypy app/

# testes (114 testes)
pytest tests/ --cov=app --cov-report=term-missing
```

Todos os comandos rodam na raiz do repositório.

## CI (GitHub Actions)

Workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml), em cada push/PR para `main`:

| Job | O que faz |
|-----|-----------|
| `lint` | `ruff check` + `ruff format --check` |
| `typecheck` | `mypy app/` (strict) |
| `test` | `pytest` com cobertura |
| `compose-validate` | `docker compose config` (base + overlay de produção) |
| `docker-build` | Build da imagem backend (sem push) |

## CD (GitHub Actions)

Workflow [`.github/workflows/cd.yml`](.github/workflows/cd.yml):

1. **Publish** (sempre, em push para `main` ou tag `v*.*.*`):
   build e push da imagem para `ghcr.io/<owner>/forgeops-backend`
   com tags `sha-<commit>`, `latest` e `<versão>` (semver em tags).
2. **Deploy** (somente quando a repo variable `DEPLOY_ENABLED=true`):
   sincroniza `docker-compose.yml`, `docker-compose.prod.yml` e `monitoring/`
   via SSH, garante a rede `forgeops`, baixa a imagem publicada exata
   (`sha-<commit>`) e derruba/religa os serviços.

### Configuração (secrets e variables)

| Nome | Tipo | Conteúdo |
|------|------|----------|
| `DEPLOY_ENABLED` | repository **variable** | `true` para ativar o deploy |
| `DEPLOY_HOST` | secret | Host/IP do servidor |
| `DEPLOY_USER` | secret | Usuário SSH |
| `DEPLOY_SSH_KEY` | secret | Chave SSH privada (sem passphrase) |
| `DEPLOY_PATH` | secret | Diretório do stack no servidor (ex.: `/opt/forgeops`) |
| `DEPLOY_PORT` | secret (opcional) | Porta SSH (padrão `22`) |

### Provisionamento único do servidor

```bash
# rede compartilhada com o frontend
docker network inspect forgeops >/dev/null 2>&1 || docker network create forgeops

# diretório do stack + secrets do ambiente (fora do git)
mkdir -p /opt/forgeops
$EDITOR /opt/forgeops/.env.prod   # APP_ENV, APP_SECRET_KEY, POSTGRES_PASSWORD,
                                  # RABBITMQ_PASSWORD, BACKEND_IMAGE, CORS_ORIGINS...
```

## API (resumo)

| Grupo | Endpoints |
|-------|-----------|
| Auth | `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me` |
| Monitores | `POST/GET /monitors`, `GET/PATCH/DELETE /monitors/{id}`, `POST /monitors/{id}/toggle` |
| Health checks | `POST /health-check/{id}`, `POST /health-check/run-all` |
| Dashboard | `GET /dashboard/summary`, `/uptime/{id}`, `/latency/{id}`, `/incidents`, `/availability/{id}`, `/history/{id}` |
| Incidentes | `GET /incidents`, `GET /incidents/{id}`, `PATCH /incidents/{id}` |
| Observabilidade | `GET /health`, `/health/db`, `/ready`, `/metrics` |

Documentação interativa: `GET /docs` (Swagger).

## Estrutura do repositório

```
.
├── app/                  # aplicação (api / application / domain / infrastructure / workers)
├── alembic/              # migrações do banco
├── tests/                # suíte pytest
├── monitoring/           # provisioning do Prometheus e Grafana
├── .github/workflows/    # ci.yml e cd.yml
├── docker-compose.yml    # stack local
├── docker-compose.prod.yml  # overlay de produção (portas internas, restarts)
├── Dockerfile
├── docker-entrypoint.sh  # espera o Postgres + alembic upgrade (RUN_MIGRATIONS=1)
└── pyproject.toml        # dependências, ruff, mypy, pytest
```

## Licença

MIT
