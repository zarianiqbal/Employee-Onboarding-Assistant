# Backend (FastAPI)

Async REST API and RAG orchestration for the Employee Onboarding Assistant.

## Endpoints

| Method + Path                              | Purpose                                  |
| ------------------------------------------ | ---------------------------------------- |
| `GET  /health`                             | Liveness probe                           |
| `GET  /ready`                              | Readiness + integration status           |
| `POST /api/v1/employees`                   | Register / invite a new hire             |
| `GET  /api/v1/employees`                   | List employees (paginated)               |
| `GET  /api/v1/employees/{id}`              | Get a profile                            |
| `PATCH /api/v1/employees/{id}`             | Progressive-profiling update             |
| `GET  /api/v1/employees/{id}/tasks`        | Checklist + completion %                 |
| `PATCH /api/v1/tasks/{id}`                 | Update a task's status                   |
| `POST /api/v1/employees/{id}/documents/sas`| Mint a write-only SAS upload token       |
| `POST /api/v1/employees/{id}/documents`    | Commit a blob reference after upload     |
| `GET  /api/v1/employees/{id}/documents`    | List an employee's documents             |
| `POST /api/v1/chat`                        | Grounded AI answer with citations        |
| `POST /api/v1/chat/stream`                 | Streamed answer (Server-Sent Events)     |

## Local development

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # endpoints blank => local/stub mode
uvicorn app.main:app --reload
```

With no Azure endpoints configured the API runs in **local mode**: an in-memory
data store seeded with the task catalog, stubbed SAS tokens, and a keyword-based
chatbot over the local policy corpus. This lets the frontend and tests run with
zero cloud dependencies. Interactive API docs are at `/docs`.

## Configuration

All settings are environment variables (see `.env.example`). There are **no
secrets** — only resource endpoints. Azure access uses `DefaultAzureCredential`
(managed identity in the cloud, `az login` locally). Setting an endpoint enables
the corresponding real integration:

| Variable                     | Enables                             |
| ---------------------------- | ----------------------------------- |
| `AZURE_SQL_SERVER/DATABASE`  | Azure SQL repository (else in-memory) |
| `AZURE_STORAGE_ACCOUNT_URL`  | Real SAS tokens (else stub)          |
| `AZURE_OPENAI_ENDPOINT`      | Azure OpenAI generation (else stub)  |
| `AZURE_SEARCH_ENDPOINT`      | AI Search retrieval (else keyword)   |

## Tests & linting

```bash
pytest            # 21 tests, runs fully in local mode
ruff check app tests scripts
mypy app
```

## Policy ingestion

```bash
python scripts/ingest_policies.py --recreate-index
```

Chunks the markdown policy corpus, embeds it with Azure OpenAI, and indexes it
into Azure AI Search. Reads only the policy corpus — never employee PII.

## Container

```bash
docker build -t onboarding-backend .
docker run -p 8000:8000 onboarding-backend
```

The image bundles the Microsoft ODBC Driver 18 for Azure SQL connectivity.
