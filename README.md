# Employee Onboarding Assistant

A centralized, secure, and AI-powered web application that streamlines new-hire
registration, task management, and information retrieval — eliminating the
first-week confusion that comes from information being scattered across emails,
portals, and HR teams.

## Why

New employees struggle to locate the right documents, understand company
policies, and complete onboarding tasks on time. This app brings all of that
into a single, secure workflow:

- **Employee Registration** — a validated form that captures new-hire details.
- **Secure Document Upload** — drag-and-drop uploads straight to Azure Blob
  Storage using short-lived SAS tokens (the "valet key" pattern).
- **Interactive Onboarding Checklist** — a real-time dashboard tracking task
  progress and completion percentages.
- **AI Onboarding Assistant** — a RAG-powered chatbot that answers questions
  like *"What documents do I need to submit?"* and *"Explain the leave policy."*

## Architecture

```
┌──────────────┐      ┌──────────────────┐      ┌────────────────────┐
│  React SPA   │─────▶│  FastAPI backend │─────▶│  Azure SQL Database │
│ (TypeScript) │      │   (Python)       │      │  Employees / Tasks  │
└──────┬───────┘      └────────┬─────────┘      └────────────────────┘
       │                       │
       │ SAS token             │ RAG orchestration
       ▼                       ▼
┌──────────────┐      ┌──────────────────┐      ┌────────────────────┐
│  Azure Blob  │      │   Azure OpenAI   │◀────▶│   Azure AI Search   │
│   Storage    │      │  (chat + embed)  │      │   (vector index)    │
└──────────────┘      └──────────────────┘      └────────────────────┘
```

See [`docs/architecture.md`](docs/architecture.md) for the full breakdown.

## Tech Stack

| Layer          | Technology                                            |
| -------------- | ----------------------------------------------------- |
| Frontend       | React, TypeScript, Vite                               |
| Backend        | Python, FastAPI                                       |
| Database       | Azure SQL Database (T-SQL)                            |
| Storage        | Azure Blob Storage (Hot tier, SAS tokens)             |
| AI             | Azure OpenAI + Azure AI Search (RAG)                  |
| Infrastructure | Terraform (IaC)                                       |
| CI/CD          | GitHub Actions                                        |
| Security       | Microsoft Entra ID + Managed Identities (secretless)  |

## Repository Layout

```
.
├── frontend/    # React + TypeScript single-page application
├── backend/     # FastAPI REST API + RAG orchestration
├── database/    # T-SQL schema, migrations, and seed scripts
├── infra/       # Terraform modules for Azure resources
├── docs/        # Architecture and design documentation
└── .github/     # CI/CD workflows
```

## Getting Started

Each component has its own README with setup instructions:

- [`backend/README.md`](backend/README.md)
- [`frontend/README.md`](frontend/README.md)
- [`database/README.md`](database/README.md)
- [`infra/README.md`](infra/README.md)

## Security Model

This project follows a **secretless security** standard: no static passwords or
connection strings live in code. Services authenticate to Azure SQL, Blob
Storage, and OpenAI using **Microsoft Entra ID** and **Managed Identities**.

## License

[MIT](LICENSE)
