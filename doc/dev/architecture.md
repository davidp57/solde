# Architecture — Solde ⚖️

## Overview

Solde is a modular monolithic web application deployed in a single Docker container, targeting a Synology NAS with a **≤ 384 MB RAM** budget.

The Vue.js 3 frontend is compiled at build time and served as static files directly by FastAPI, removing the need for a separate reverse proxy.

```
Browser
    │
    ▼
Docker container (port 8000)
    │
    ├── Uvicorn (1 worker)
    │       │
    │       └── FastAPI
    │               ├── /api/**  →  Python routers
    │               └── /*       →  StaticFiles (frontend/dist/) + SPA fallback
    │
    └── Volume ./data/
            ├── solde.db          (SQLite WAL)
            ├── solde.db-wal      (WAL journal — backup together with solde.db)
            ├── pdfs/             (generated client invoices)
            ├── uploads/          (supplier invoice attachments)
            ├── logs/             (rotating application log)
            └── backups/          (snapshots created via the admin UI)
```

### RAM budget

| Component | Estimated RAM |
|---|---|
| Uvicorn + FastAPI (idle) | ~50–80 MB |
| SQLite (file-based) | ~0 MB |
| Vue.js static assets | 0 MB server-side |
| WeasyPrint at PDF generation peak | ~30–50 MB |
| **Idle total** | **~80–130 MB** |
| **Peak total** | **~180 MB** |

WeasyPrint is imported on demand (not at startup) to respect this budget.

---

## Technical stack

| Layer | Technology | Notes |
|---|---|---|
| API server | FastAPI + Uvicorn | Native async, OpenAPI docs |
| Database | SQLite (WAL mode) | Zero config, single-instance NAS |
| ORM | SQLAlchemy 2 async | Async sessions, type safety |
| Migrations | Alembic | Schema version control |
| Authentication | python-jose (JWT) + bcrypt | Stateless JWTs; bcrypt direct (passlib incompatible with Python 3.13+) |
| Validation | Pydantic v2 | Input/output schemas, settings |
| PDF generation | WeasyPrint | Imported on demand |
| Email | smtplib (stdlib) | No external dependency |
| Frontend | Vue.js 3 + Vite | Composition API + `<script setup>` |
| UI components | PrimeVue 4 | Aura CSS-only theme |
| State management | Pinia | Composition API friendly |
| Router | Vue Router 5 | Role-based navigation guards, lazy loading |
| i18n | vue-i18n 11 | All UI strings externalized in `fr.ts` |
| HTTP client | axios | JWT interceptors, automatic 401 token refresh |
| Backend tests | pytest + pytest-asyncio + httpx | Async tests, in-memory ASGI client |
| Frontend tests | Vitest | Native Vite integration |
| Linting | ruff (Python) + ESLint + Prettier | Enforced in CI and pre-push |

---

## Project structure

```
solde/
├── backend/
│   ├── main.py              # create_app(), lifespan, middleware, StaticFiles
│   ├── config.py            # Pydantic Settings (env vars, JWT, SMTP, fiscal year)
│   ├── database.py          # Async engine, WAL pragma, get_db(), init_db()
│   ├── models/              # SQLAlchemy ORM models (one file per table)
│   ├── routers/             # FastAPI route handlers, one file per business domain
│   ├── services/            # Business logic, independent from HTTP layer
│   ├── schemas/             # Pydantic input/output schemas
│   ├── templates/           # Jinja2 templates for WeasyPrint PDF rendering
│   └── alembic/             # Database migrations
│       └── versions/        # One script per schema change
├── frontend/
│   └── src/
│       ├── api/             # Axios call functions and TypeScript types
│       ├── composables/     # Reusable Vue 3 composables
│       ├── components/      # Shared UI components
│       ├── layouts/         # App shell layout (AppLayout.vue)
│       ├── router/          # Vue Router with role-based guards
│       ├── stores/          # Pinia stores (auth, settings)
│       ├── views/           # Page-level components (one per route)
│       ├── i18n/            # Translation files (fr.ts)
│       └── utils/           # Pure utility functions
├── tests/
│   ├── unit/                # Unit tests for services and utilities
│   ├── integration/         # Integration tests against the full ASGI stack
│   └── conftest.py          # pytest fixtures (async DB, test client)
├── scripts/                 # One-off operational scripts
├── doc/                     # Project documentation (this directory)
├── data/                    # Runtime data (gitignored; mounted as Docker volume)
├── Dockerfile               # Multi-stage: frontend builder + Python runtime
├── docker-compose.yml       # Local and production compose configuration
├── dev.ps1                  # Development helper script (Windows PowerShell)
└── pyproject.toml           # Python project metadata, dependencies, tooling config
```

---

## Backend layer architecture

The backend follows a strict layered architecture. Each layer has a single responsibility and calls only the layer below it.

```
HTTP request
    │
    ▼
Router  (routers/)     — HTTP parsing, auth dependency, error mapping → HTTPException
    │
    ▼
Service (services/)    — Business logic, domain rules, DB writes
    │
    ▼
Model   (models/)      — SQLAlchemy ORM, table definitions
    │
    ▼
Database (database.py) — Async SQLite session, WAL mode
```

**Rules:**
- Routers never contain business logic. They validate input via Pydantic schemas, call services, and convert exceptions to HTTP responses.
- Services never import from routers. They receive a database session and call ORM models directly.
- All monetary values use Python `Decimal`, never `float`.
- Public functions and methods always carry type annotations.

### Exception handling

Typed exceptions are raised in services and caught in routers, which map them to structured `HTTPException` responses. Any unhandled exception bubbles up to `UnhandledExceptionMiddleware` in `main.py`, which logs it and returns a generic JSON `500 {detail, code}`.

---

## Authentication and authorization

Authentication uses stateless JWTs stored in **HttpOnly cookies** (access + refresh tokens). The frontend cannot access the tokens from JavaScript, preventing XSS token theft.

Role-based authorization is implemented at the router level via FastAPI dependencies:

| Technical role | Product label | Permissions |
|---|---|---|
| `secretaire` | Manager | Full read/write access to Management area |
| `tresorier` | Accountant | Management + Accounting areas |
| `admin` | Administrator | Everything + users + settings |
| `readonly` | Read-only | Legacy transitional role |

Navigation sections:
- **Management**: Dashboard, Contacts, Client invoices, Supplier invoices, Payments, Bank, Cash, Employees, Salaries
- **Accounting**: Fiscal years, Chart of accounts, Accounting rules, Balance sheet, Income statement, Journal, Trial balance, General ledger
- **Administration** (admin only): Settings, System supervision, Excel import

---

## Database

SQLite runs in **WAL mode** (`PRAGMA journal_mode=WAL`). This enables concurrent readers alongside a single writer, suitable for the single-instance deployment model.

**Important for backups**: always copy `solde.db`, `solde.db-wal`, and `solde.db-shm` together. Restoring only `solde.db` while WAL files remain from a different state can produce inconsistencies.

### Schema management

All schema changes go through Alembic migrations (`backend/alembic/versions/`). Never modify the database schema directly.

Migration naming convention: `NNNN_short_description.py` where `NNNN` is a zero-padded sequence number.

---

## Key data model entities

| Entity | Table | Description |
|---|---|---|
| `Contact` | `contacts` | Client, supplier, or employee |
| `Invoice` | `invoices` | Client or supplier invoice |
| `Payment` | `payments` | Payment linked to an invoice |
| `BankTransaction` | `bank_transactions` | Bank statement line |
| `CashEntry` | `cash_entries` | Cash movement |
| `AccountingEntry` | `accounting_entries` | Double-entry accounting line |
| `AccountingAccount` | `accounting_accounts` | Chart of accounts entry |
| `AccountingRule` | `accounting_rules` | Automatic journal generation rule |
| `FiscalYear` | `fiscal_years` | Fiscal year definition and state |
| `Salary` | `salaries` | Salary record linked to a contact |
| `AppSettings` | `app_settings` | Single-row association settings |
| `User` | `users` | Application user account |
| `AuditLog` | `audit_logs` | Immutable action log |
| `ImportRun` | `import_runs` | Excel import execution record |

### Accounting entry group key

Every `AccountingEntry` has a runtime group key used to cluster related lines in the journal view:

- `group_key` column value if set;
- otherwise `"{source_type}:{source_id}"` if both are present;
- otherwise `"entry:{id}"`.

This convention is used in journal pagination, import state comparison, and deduplication signatures.

---

## Security considerations

- HTTP security headers (CSP, HSTS, X-Frame-Options, etc.) set by `SecurityHeadersMiddleware`.
- CORS: `cors_allowed_origins` from settings; defaults to empty in production.
- Swagger UI and ReDoc: exposed only when `DEBUG=true` or `SWAGGER_ENABLED=true`.
- File uploads: validated by magic bytes (PDF, JPEG, PNG, WebP), not solely by `Content-Type` header.
- All text inputs have `max_length` constraints in Pydantic schemas.
- Parameterized queries only — no raw SQL string concatenation.
- Rate limiting on authentication endpoints.
