# Architecture — Solde ⚖️

## Overview

Solde is a modular monolithic web application deployed in a single Docker container on a Synology NAS. The Vue.js 3 frontend is served as static files directly by FastAPI, which removes the need for a separate reverse proxy or web server.

```
Browser
    │
    ▼
Docker container (port 8080)
    │
    ├── Uvicorn (1 worker)
    │       │
    │       └── FastAPI
    │               ├── /api/**  →  Python routers
    │               └── /*       →  StaticFiles (frontend/dist/)
    │
    └── Volume ./data/
            ├── solde.db          (SQLite WAL)
            ├── uploads/          (supplier invoices)
            └── pdfs/             (generated client invoices)
```

**Target RAM budget: ≤ 384 MB on Synology NAS**

| Component | Estimated RAM |
|---|---|
| Uvicorn + FastAPI (idle) | ~50–80 MB |
| SQLite (file-based, not in memory) | ~0 MB |
| Vue.js static assets | 0 MB on the server side |
| WeasyPrint (PDF generation peak) | ~30–50 MB |
| **Idle total** | **~80–130 MB** |
| **Peak total** | **~180 MB** |

---

## Technical stack

| Layer | Technology | Version | Rationale |
|---|---|---|---|
| API server | FastAPI + Uvicorn | 0.115+ | Native async, good performance, automatic OpenAPI docs |
| Database | SQLite (WAL mode) | — | Zero configuration, fits a single-instance NAS deployment |
| ORM | SQLAlchemy 2 async | 2.0+ | Async sessions, type safety, Alembic migrations |
| Migrations | Alembic | — | Schema version control |
| Authentication | python-jose (JWT) + bcrypt | — | Stateless JWTs; direct bcrypt because passlib is incompatible with Python 3.13 |
| Validation | Pydantic v2 | 2.0+ | Input/output schemas, settings management |
| PDF generation | WeasyPrint | — | Imported on demand to save RAM |
| E-mail sending | smtplib (stdlib) | — | No external dependency |
| Frontend | Vue.js 3 + Vite | 3.x | Composition API, native TypeScript support |
| UI | PrimeVue 4 | 4.x | Rich components, Aura CSS-only theme |
| State management | Pinia | 2.x | Lightweight, Composition API friendly |
| Router | Vue Router | 4.x | Navigation guards, lazy loading |
| i18n | vue-i18n | 11.x | All UI strings are externalized in French |
| HTTP client | axios | — | JWT interceptors + automatic 401 refresh |
| Backend tests | pytest + pytest-asyncio + httpx | — | Async tests, in-memory ASGI client |
| Frontend tests | Vitest | — | Native Vite integration, jsdom-compatible |
| Linting/formatting | ruff (Python) + ESLint + Prettier (JS) | — | Consistent quality tooling |

---

## Project structure

```
solde/
├── backend/
│   ├── __init__.py
│   ├── main.py              # create_app(), lifespan, CORS, StaticFiles mounting
│   ├── config.py            # Pydantic settings (JWT, SMTP, fiscal year)
│   ├── database.py          # Async engine, WAL, get_db(), init_db()
│   ├── models/              # SQLAlchemy models (one table per file)
│   ├── routers/             # FastAPI routes by business domain
│   ├── services/            # Business logic (independent from HTTP)
│   ├── schemas/             # Pydantic input validation and output serialization
│   ├── templates/           # Jinja2 templates for WeasyPrint PDFs
│   └── alembic/             # Alembic migrations
├── frontend/
│   ├── src/
│   │   ├── api/             # API calls, axios client, TypeScript types
│   │   ├── layouts/         # Application layouts (responsive AppLayout)
│   │   ├── views/           # Vue pages (one route = one view)
│   │   ├── components/      # Reusable components
│   │   ├── stores/          # Pinia stores (auth, ...)
│   │   ├── router/          # Route definitions and guards
│   │   └── i18n/            # Translation files (fr.ts)
│   ├── vite.config.ts       # /api → backend proxy in dev mode
│   └── vitest.config.ts
├── tests/
│   ├── unit/                # Unit tests (services, config)
│   ├── integration/         # API tests (httpx AsyncClient)
│   └── conftest.py          # Shared fixtures (in-memory DB, client, admin_user)
├── data/                    # Docker volume (gitignored)
├── doc/
│   ├── plan.md              # Functional specifications and data model
│   ├── roadmap.md           # Progress by phase and next steps
│   └── architecture.md      # This document
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

---

## Architecture decisions

### SQLite over PostgreSQL

The target deployment is a single-instance application on a home NAS, with at most a few dozen users. SQLite in WAL mode provides sufficient read/write concurrency, avoids a second container and roughly 50 MB of additional RAM, and keeps backups simple because there is only one main file to copy.

### Single-container Docker deployment

A single container simplifies deployment through Portainer on Synology NAS. The multi-stage build (`node:22-alpine` → `python:3.13-slim`) produces one image that serves both the API and the static frontend assets.

### Frontend served by FastAPI

This removes the need for Nginx or another reverse proxy. FastAPI mounts `frontend/dist/` through `StaticFiles` with `html=True` so SPA routes resolve back to `index.html`.

### Direct bcrypt usage without passlib

`passlib` is incompatible with `bcrypt >= 4.0` on Python 3.13 because of the missing `__about__` attribute. The project therefore uses direct calls to `bcrypt.hashpw()` and `bcrypt.checkpw()`.

### On-demand WeasyPrint import

WeasyPrint loads roughly 30–50 MB of libraries when imported. Delaying the import inside the PDF generation service avoids penalizing application startup and idle memory usage.

### Stateless JWT tokens

There is no session table in the database. The long-lived refresh token renews the short-lived access token without forcing a new login. Token revocation was not implemented in Phase 1 and was considered acceptable for a small internal application.

### Application roles

| Role | Scope |
|---|---|
| `ADMIN` | Full access, including user management and settings |
| `TRESORIER` | Full management + accounting, excluding user management |
| `SECRETAIRE` | Invoices and payments only |
| `READONLY` | Read-only access, no modifications |

---

## Authentication flow

```
Browser                           API
    │                               │
    │  POST /api/auth/login         │
    │  (username + password)        │
    │ ─────────────────────────►   │
    │                               │  Verifies bcrypt
    │  { access_token,              │  Generates JWT (15 min)
    │    refresh_token }            │  Generates refresh token (7 days)
    │ ◄─────────────────────────   │
    │                               │
    │  GET /api/...                 │
    │  Authorization: Bearer <jwt>  │
    │ ─────────────────────────►   │
    │                               │  Decodes JWT
    │  Data                         │  Checks expiration + role
    │ ◄─────────────────────────   │
    │                               │
    │  (JWT expired → 401)          │
    │  POST /api/auth/refresh       │
    │  { refresh_token }            │
    │ ─────────────────────────►   │
    │  { access_token, ... }        │
    │ ◄─────────────────────────   │
```

The axios interceptor in `api/client.ts` automatically handles refresh and queues concurrent requests while the token is being renewed.

---

## Code conventions

- **Python**: type annotations are required on all public functions; use Pydantic v2 for schemas; follow SQLAlchemy 2 async style.
- **Vue.js**: use the Composition API with `<script setup>`; Pinia is the shared state solution; the Options API is not used.
- **SQL**: every schema change must go through Alembic migrations; never modify the database directly.
- **Security**: validate all inputs at the API boundary; keep secrets out of the codebase and in environment variables; use parameterized queries only through the ORM.
- **Money**: always use Python `Decimal`, never `float`, for monetary amounts.
