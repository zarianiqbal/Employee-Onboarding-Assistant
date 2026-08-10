# Contributing

This project follows a lightweight but disciplined workflow modeled on the
team's engineering standards.

## Branching strategy

- All work happens on **feature branches** named `feature/<short-description>`
  (or `fix/…`, `chore/…`). Never commit directly to `main`.
- Open a **pull request** into `main` when your branch is ready.
- Every PR requires a **"two-eyes" review** — at least one approval from another
  engineer before merge.
- `main` is a **protected branch**: CI must be green and reviews must be
  approved before merging.

## Before you push

Run the relevant checks locally so CI passes on the first try:

```bash
# Backend
cd backend && ruff check app tests scripts && pytest -q

# Frontend
cd frontend && npm run lint && npm run build

# Infra
cd infra && terraform fmt -check && terraform validate
```

## Continuous integration

Every push and PR runs automated workflows (see `.github/workflows/`):

- **Backend CI** — ruff, mypy, pytest
- **Frontend CI** — ESLint, type-check, Vite build
- **Database CI** — applies schema/migrations/seed to a fresh SQL Server
- **Infra CI** — `terraform fmt -check` + `validate`
- **Security Scan** — gitleaks, pip-audit, npm audit, CodeQL

## Commit messages

Write a concise summary line (imperative mood), then a body explaining the
*why* when it isn't obvious. Group related changes into a single commit.

## Secretless security

Never commit secrets, connection strings, account keys, or `*.tfvars` with real
values. All Azure access uses Managed Identities / Entra ID. The gitleaks scan
will fail the build if a secret is detected.
