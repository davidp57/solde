# Solde ⚖️ — LLM Reference

## Document purpose

This document is a dense, machine-readable reference for an LLM assistant working on or with the Solde application. It covers the complete data model, roles, workflows, business rules, API shape, and technology stack. No decorative formatting — facts only.

---

## Application overview

**Solde** is a web application for managing the accounting of a French *loi 1901* non-profit association (tutoring — *soutien scolaire*). It handles client invoicing, supplier invoices, payments, cash, bank transactions, payroll, and double-entry bookkeeping.

Single-container Docker application. Target: Synology NAS, ≤ 384 MB RAM. One uvicorn worker.

---

## Technology stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2 async, Alembic, Pydantic v2 |
| Database | SQLite in WAL mode (`sqlite+aiosqlite:///data/solde.db`) |
| PDF generation | WeasyPrint (lazy-loaded at generation time) |
| Email | SMTP via aiosmtplib or smtplib |
| Frontend | Vue.js 3, Composition API + `<script setup>`, PrimeVue 4, Pinia, vue-i18n |
| Build | Vite 5 |
| Auth | JWT in HttpOnly cookies (24h expiry), bcrypt password hashing |
| Migrations | Alembic (auto-applied at startup) |
| Container | Single Docker container, serves static frontend + FastAPI backend |

---

## Authentication and roles

JWT stored in HttpOnly cookie. All API routes except `/api/auth/login` and `/api/health` require a valid JWT.

### Roles (ascending privilege)

| Role value | Product label | Access |
|---|---|---|
| `readonly` | Read-only | Transitional/legacy — view only |
| `secretaire` | Manager | Full Management area |
| `tresorier` | Accountant | Management + Accounting |
| `admin` | Administrator | Everything + settings + users + system + Excel import |

### Password policy

Enforced in Pydantic `backend/schemas/auth.py`: minimum 8 characters, at least one uppercase ASCII letter (`A-Z`), at least one ASCII digit (`0-9`).

### Forced password change

A user with `must_change_password=True` on their model is redirected to the password change page on every login. Flag is set on account creation and after admin password reset.

---

## Data model

All monetary amounts use Python `Decimal`. Primary keys are integer auto-increment. Timestamps are UTC.

### User

Fields: `id`, `username`, `email`, `hashed_password`, `role` (enum), `is_active`, `must_change_password`, `created_at`.

### Contact

Fields: `id`, `name`, `first_name`, `email`, `phone`, `address`, `notes`, `is_active`, `created_at`. Normalized name used for duplicate detection during Excel import.

### FiscalYear

Fields: `id`, `name`, `start_date`, `end_date`, `status` (`open` / `closed`). Only one fiscal year can be active at a time. Closing is irreversible.

### Invoice (client invoice)

Fields: `id`, `number` (auto-generated on validation), `contact_id`, `date`, `due_date`, `status` (enum), `total_amount` (Decimal), `paid_amount` (Decimal), `is_bad_debt`, `notes`, `fiscal_year_id`, `created_at`, `updated_at`.

Invoice line: `id`, `invoice_id`, `description`, `line_type` (`cours` / `adhesion` / `autre`), `quantity`, `unit_price`, `total`.

Status transitions: `draft` → `validated` → (`paid` | `partially_paid` | `overdue` | `bad_debt`). Validated invoices cannot have their lines edited.

### SupplierInvoice

Fields: `id`, `number`, `contact_id` (nullable), `supplier_name` (free text fallback), `date`, `due_date`, `status`, `total_amount`, `paid_amount`, `notes`, `fiscal_year_id`.

### Payment

Fields: `id`, `contact_id`, `amount`, `date`, `reference`, `payment_method`, `notes`, `fiscal_year_id`, `bank_deposit_id` (nullable), `invoice_id` (nullable — linked invoice).

### CashMovement

Fields: `id`, `date`, `amount` (positive = in, negative = out), `description`, `contact_id` (nullable), `fiscal_year_id`.

### BankTransaction

Fields: `id`, `date`, `amount`, `description`, `reference`, `reconciled`, `fiscal_year_id`, `import_run_id` (nullable).

### BankDeposit

Fields: `id`, `date`, `reference`, `total_amount`, `fiscal_year_id`. Groups multiple payments remitted to the bank together.

### Employee

Fields: `id`, `last_name`, `first_name`, `ssn` (nullable), `email`, `contract_type`, `contract_start_date`, `contract_end_date` (nullable), `hourly_rate` (nullable), `monthly_rate` (nullable), `is_active`.

### Salary

Fields: `id`, `employee_id`, `period_month`, `period_year`, `gross_amount`, `employer_contributions`, `employee_contributions`, `net_amount`, `status`, `fiscal_year_id`.

### AccountingAccount

Fields: `id`, `number` (string, e.g. `"707000"`), `label`, `account_type` (`asset` / `liability` / `equity` / `revenue` / `expense`), `is_active`.

### AccountingEntry

Fields: `id`, `date`, `label`, `debit`, `credit`, `account_id`, `fiscal_year_id`, `source_type` (nullable), `source_id` (nullable), `group_key` (nullable).

**Runtime group key convention:** `group_key` if set, else `"{source_type}:{source_id}"` if both present, else `"entry:{id}"`.

Entries are always balanced: sum of debits = sum of credits within a group.

### AccountingRule

Fields: `id`, `name`, `trigger_type` (e.g. `invoice_validated`, `payment_received`), `is_active`, plus rule lines defining which accounts to debit/credit and with what amount formula.

### AppSettings (singleton, id=1)

Fields: `association_name`, `association_address`, `association_siret`, `logo_path`, `social_purpose`, `invoice_number_template`, `invoice_sequence_digits`, `supplier_invoice_number_template`, `default_invoice_due_days` (0–365), `default_price_cours`, `default_price_adhesion`, `default_price_autre`, `smtp_host`, `smtp_port`, `smtp_use_ssl`, `smtp_username`, `smtp_password`, `smtp_sender_email`, `smtp_bcc`.

### ImportRun / ImportLog

ImportRun: one record per Excel import attempt. Fields: `id`, `filename`, `file_hash`, `import_type` (`gestion` / `comptabilite`), `status`, `created_at`, `executed_by`.

ImportLog: diagnostic rows linked to an ImportRun. Fields: `id`, `run_id`, `sheet`, `row_num`, `level` (`info` / `warning` / `error`), `message`, `object_type`, `object_id` (nullable).

### AuditLog

Fields: `id`, `timestamp`, `user_id`, `action`, `entity_type`, `entity_id`, `details`.

---

## API shape

Base URL: `/api`. All responses are JSON. Errors use `{"detail": "...", "code": "..."}`.

### Authentication

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/login` | Login with username/password. Sets JWT cookie. |
| POST | `/api/auth/logout` | Clears JWT cookie. |
| POST | `/api/auth/change-password` | Change own password. |
| GET | `/api/auth/me` | Get current user profile. |

### Core resources (standard CRUD pattern)

Each resource follows: `GET /api/{resource}` (list), `POST /api/{resource}` (create), `GET /api/{resource}/{id}` (detail), `PUT /api/{resource}/{id}` (update), `DELETE /api/{resource}/{id}` (delete where allowed).

Resources: `contacts`, `invoices`, `supplier-invoices`, `payments`, `cash`, `bank`, `bank-deposits`, `employees`, `salaries`, `accounting-accounts`, `accounting-entries`, `accounting-rules`, `fiscal-years`.

### Notable endpoints

| Method | Path | Notes |
|---|---|---|
| POST | `/api/invoices/{id}/validate` | Validates invoice, assigns number |
| POST | `/api/invoices/{id}/send-email` | Sends PDF by email |
| GET | `/api/invoices/{id}/pdf` | Returns PDF binary |
| POST | `/api/invoices/{id}/bad-debt` | Marks as bad debt |
| POST | `/api/bank/import-ofx` | Imports OFX bank file |
| POST | `/api/excel-import/preview` | Preview Excel import (admin only) |
| POST | `/api/excel-import/execute` | Execute Excel import (admin only) |
| GET | `/api/excel-import/history` | List import runs (admin only) |
| POST | `/api/excel-import/undo/{run_id}` | Undo an import run (admin only) |
| POST | `/api/excel-import/redo/{run_id}` | Redo an undone import run (admin only) |
| GET | `/api/dashboard` | Dashboard aggregates |
| GET | `/api/accounting/ledger` | General ledger (grand livre) |
| GET | `/api/accounting/balance` | Balance sheet |
| POST | `/api/settings/backup` | Create in-app backup (admin only) |
| POST | `/api/settings/restore` | Restore from backup (admin only) |
| GET | `/api/health` | Health check (unauthenticated) |

### Pagination

List endpoints accept `?page=1&per_page=20`. Responses include `total`, `page`, `per_page`, `items`.

---

## Excel import system

### File types

**Gestion** (`Gestion AAAA.xlsx`): processes sheets `Contacts`, `Factures`, `Paiements`, `Caisse`, `Banque`. Also generates accounting entries via rules.

**Comptabilite** (`Comptabilite AAAA.xlsx`): processes sheet `Journal`.

### Coexistence rules

- Exact file re-import (same SHA-256 hash) is automatically rejected.
- Objects already present in the database (exact match) are silently ignored.
- Blocking ambiguities: multiple contacts with the same normalized name; multiple invoice candidates for a payment.
- Exact duplicate journal entries (same date, account, normalized label, debit, credit) are ignored.

### Scope of reset

Selective reset identifies in-scope runs by checking whether the fiscal year name appears as a substring of the imported file name. A full reset wipes all business data but keeps users, settings, and chart of accounts.

### Undo/redo

Each ImportRun tracks which DB rows it created. Undo deletes those rows (blocked if any were subsequently modified). Redo re-executes the same run.

---

## Business rules

### Invoice numbering

Template variables: `{year}` (4-digit year), `{seq}` (zero-padded sequence per year). Sequence resets each year. Digits count is configurable (default: 3).

### Due date

`due_date = invoice_date + AppSettings.default_invoice_due_days days` when not explicitly provided.

### Accounting entry grouping

A group of accounting entries representing one business event shares either a `group_key` value, or a common `source_type`/`source_id` pair. The runtime key for display and grouping is: `group_key || "{source_type}:{source_id}" || "entry:{id}"`.

### Fiscal year assignment

Objects (invoices, payments, entries) are assigned to a fiscal year based on their date falling within the year's `start_date`..`end_date` range.

### WAL mode

SQLite runs in WAL mode. Backup procedures must copy `solde.db`, `solde.db-wal`, and `solde.db-shm` together.

---

## Configuration (environment variables)

| Variable | Required | Default | Description |
|---|---|---|---|
| `JWT_SECRET_KEY` | Yes | — | JWT signing key |
| `DATABASE_URL` | Yes | — | `sqlite+aiosqlite:///data/solde.db` |
| `ADMIN_USERNAME` | No | `admin` | Bootstrap admin (first run only) |
| `ADMIN_PASSWORD` | No | `changeme` | Bootstrap password (first run only) |
| `ADMIN_EMAIL` | No | `admin@exemple.fr` | Bootstrap email |
| `DEBUG` | No | `false` | Enables verbose errors and Swagger |
| `SWAGGER_ENABLED` | No | `false` | Exposes `/api/docs` independently of `DEBUG` |
| `FISCAL_YEAR_START_MONTH` | No | `8` | First month of the fiscal year |

---

## Project directory structure (key paths)

```
backend/
  main.py              FastAPI app factory, middleware, router registration
  config.py            Settings (pydantic-settings, reads .env)
  database.py          Async SQLAlchemy engine, session factory, WAL setup
  models/              SQLAlchemy ORM models
  schemas/             Pydantic request/response schemas
  routers/             FastAPI routers (one per resource)
  services/            Business logic layer
  alembic/             Alembic migrations (auto-applied at startup)
frontend/
  src/
    views/             Vue page components
    components/        Reusable UI components
    stores/            Pinia stores
    composables/       Vue composables
    router/            Vue Router (includes admin guards)
    locales/           i18n translation files (FR)
tests/
  unit/                pytest unit tests (services, engines)
  integration/         pytest integration tests (API endpoints)
  conftest.py          Fixtures: async test client, in-memory SQLite DB
data/
  solde.db             Main SQLite database
  solde.db-wal         WAL file (must be backed up with solde.db)
  solde.db-shm         Shared memory file
  backups/             In-app backup files
  pdfs/                Generated invoice PDFs
  logs/                Rotating application logs
```

---

## Key conventions

- All monetary values: Python `Decimal`, never `float`.
- All API inputs validated by Pydantic v2 schemas at the router boundary.
- Services raise typed exceptions; routers catch and convert to HTTP errors.
- Unhandled exceptions bubble to `UnhandledExceptionMiddleware` → JSON 500 `{detail, code}`.
- All DB access through SQLAlchemy 2 async sessions (no raw SQL with string concatenation).
- Alembic migrations type-annotated (`revision: str`, `down_revision: str | None`, etc.).
- Vue components use Composition API + `<script setup>` only. No Options API.
- All user-facing strings go through vue-i18n translation keys. Never hardcode strings in components.
- Admin-only routes: `/settings`, `/users`, `/system`, `/import` — guarded in both router (`requiresAdmin`) and API middleware.
