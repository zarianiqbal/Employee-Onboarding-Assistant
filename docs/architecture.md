# Architecture

The Employee Onboarding Assistant is a full-stack, cloud-native application
composed of four tiers: a React SPA, a FastAPI backend, an Azure SQL data
layer, and an AI (RAG) tier built on Azure OpenAI + Azure AI Search.

## System Overview

```
                         ┌───────────────────────────────┐
                         │        React SPA (Vite)        │
                         │  Registration · Upload         │
                         │  Checklist   · AI Chat         │
                         └───────────────┬───────────────┘
                                         │ REST (JSON) + Entra ID JWT
                                         ▼
                         ┌───────────────────────────────┐
                         │      FastAPI backend (API)     │
                         │  /employees  /tasks            │
                         │  /documents  /chat             │
                         └───┬───────────┬───────────┬────┘
              Managed Identity│           │           │Managed Identity
                              ▼           ▼           ▼
                   ┌────────────┐  ┌────────────┐  ┌────────────────┐
                   │ Azure SQL  │  │ Azure Blob │  │  Azure OpenAI  │
                   │ Employees  │  │  Storage   │  │  chat + embed  │
                   │ Tasks      │  │  (2 conts) │  └───────┬────────┘
                   └────────────┘  └────────────┘          │
                                                            ▼
                                                  ┌────────────────┐
                                                  │ Azure AI Search│
                                                  │  vector index  │
                                                  └────────────────┘
```

## Tiers

### 1. Frontend (React + TypeScript)

A single-page application organized into feature modules:

- **Registration** — accessible, validated new-hire form.
- **Document Upload** — drag-and-drop, direct-to-blob via SAS tokens.
- **Checklist Dashboard** — real-time task tracking with progress bars.
- **AI Chat** — streaming chat drawer with quick-action prompts.

State is managed with React hooks and a lightweight API client. Auth is handled
through Microsoft Entra ID, capturing sessions as JWTs.

### 2. Backend (FastAPI)

An async REST API acting as the secure bridge between the UI, the data layer,
and the AI services.

- `POST /api/v1/employees` — create / register an employee.
- `GET  /api/v1/employees/{id}` — fetch a profile.
- `GET  /api/v1/employees/{id}/tasks` — list assigned tasks + progress.
- `PATCH /api/v1/tasks/{id}` — update a task's status.
- `POST /api/v1/documents/sas` — mint a short-lived write-only SAS token.
- `POST /api/v1/chat` — RAG-orchestrated chat completion (streaming).

### 3. Data Layer (Azure SQL)

Normalized schema across three schemas:

- `Core.Employees` — the central profile (progressive profiling, B2B invite
  state).
- `Onboarding.Tasks` — master catalog of onboarding tasks by phase.
- `Onboarding.EmployeeTasks` — junction table tracking per-employee progress.
- `Storage.EmployeeDocuments` — blob references (URI, version, soft-delete).

See [`database/README.md`](../database/README.md).

### 4. AI Tier (RAG)

1. **Ingest** — policy/handbook PDFs are chunked, embedded, and indexed into
   Azure AI Search.
2. **Retrieve** — a user question is embedded and matched against the index
   (hybrid keyword + vector search).
3. **Augment** — retrieved chunks + the user's SQL profile context are combined
   into a system prompt.
4. **Generate** — Azure OpenAI streams the answer back to the UI.

## Secretless Security

No static credentials live in code. Every service-to-service call authenticates
with **Microsoft Entra ID** and **Managed Identities**:

- App Service → Azure SQL: token-based, via `DefaultAzureCredential`.
- App Service → Blob Storage: RBAC role assignment, SAS minted server-side.
- App Service → Azure OpenAI / AI Search: managed-identity RBAC.

## Blob Container Segregation

Two containers keep PII isolated from AI indexing:

- `company-policies` — handbooks and general documents (AI has **read** access).
- `employee-documents` — sensitive uploads such as IDs (AI has **no** access).

This ensures the RAG pipeline can never index or leak employee PII.

## Deployment

Infrastructure is provisioned with **Terraform** (remote state locked in Azure
Blob Storage). CI/CD runs through **GitHub Actions**: every push lints and
tests; merges to `main` deploy to Azure App Service.
