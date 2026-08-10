# Frontend (React + TypeScript)

Single-page application for the Employee Onboarding Assistant, built with Vite.

## Features

- **Registration** — accessible, validated new-hire form.
- **Dashboard** — onboarding checklist grouped by phase with a live progress
  bar and optimistic task toggling.
- **Document upload** — drag-and-drop direct-to-blob upload via SAS tokens.
- **AI chat drawer** — streaming answers, quick-action prompts, and citations.

## Getting started

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

The dev server proxies `/api` to the backend at `http://localhost:8000`, so run
the backend (in local mode is fine) alongside it. With the backend in local
mode you get a fully working UI end-to-end without any Azure resources.

## Scripts

| Script            | Purpose                          |
| ----------------- | -------------------------------- |
| `npm run dev`     | Start the Vite dev server        |
| `npm run build`   | Type-check + production build    |
| `npm run preview` | Preview the production build     |
| `npm run lint`    | ESLint (incl. jsx-a11y)          |
| `npm run format`  | Prettier                         |

## Configuration

`VITE_API_BASE_URL` sets the backend origin. Leave it blank to use the dev proxy
or when the SPA is served from the same origin as the API in production.

## Design system

A small set of semantic CSS custom properties in `src/styles/tokens.css` drives
the UI and adapts to the viewer's light/dark preference. Components consume the
tokens rather than hardcoding colors, so theming stays consistent.

## Accessibility

- Semantic landmarks, a skip-link, and visible focus rings.
- Form fields use `aria-invalid` + `aria-describedby` for errors.
- The chat log is an `aria-live` region; the progress bar exposes ARIA values.
- Linted with `eslint-plugin-jsx-a11y`.
