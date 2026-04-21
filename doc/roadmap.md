# Roadmap — Solde ⚖️

## Progress status

> Last updated: 2026-04-09 — active branch `develop`

| Phase | Status | Completed tasks |
|---|---|---|
| **1. Foundations** | ✅ Completed | 9/9 |
| **2. Core management** | ✅ Completed | 7/7 |
| **3. Invoicing** | ✅ Completed | 7/7 |
| **4. Payments & Treasury** | ✅ Completed | 14/14 |
| **5. Accounting** | ✅ Completed | 16/16 |
| **6. Advanced features** | ✅ Completed | 14/14 |
| **7. Plan completion** | ✅ Completed | 9/9 |

### ✅ plan.md is 100% implemented — fully functional application

All features from the initial plan are developed and tested.
**357 backend tests (74% coverage) + 11 frontend Vitest tests — 0 failures.**

### Delivered stack

**Backend** (`backend/`)
- `config.py` — Pydantic settings (`JWT_SECRET_KEY`, `FISCAL_YEAR_START_MONTH=8`, optional SMTP)
- `database.py` — SQLAlchemy 2 async + SQLite WAL + `get_db()` dependency
- `models/user.py` — `User`, `UserRole` (`READONLY`/`SECRETAIRE`/`TRESORIER`/`ADMIN`)
- `services/auth.py` — direct bcrypt for Python 3.13, JWT encode/decode
- `schemas/auth.py` — `LoginRequest`, `TokenResponse`, `UserCreate`, `UserRead`
- `routers/auth.py` — `/api/auth/login`, `/refresh`, `/me`, `/users` (admin)
- `main.py` — `create_app()`, lifespan, CORS, mount `frontend/dist/`
- Tests: `tests/unit/test_config.py` (7), `tests/unit/test_auth_service.py` (8), `tests/integration/test_auth_api.py` (9) → **24 passing, 83% coverage**

**Frontend** (`frontend/src/`)
- `main.ts` — PrimeVue 4 (Aura theme), vue-i18n v11, Pinia, Vue Router
- `i18n/fr.ts` — all UI keys (auth, nav, settings, user.role)
- `api/auth.ts` — `loginApi`, `refreshApi`, `getMeApi`
- `api/settings.ts` — `getSettingsApi`, `updateSettingsApi`
- `api/client.ts` — axios client with JWT interceptor and automatic 401 refresh
- `api/types.ts` — `LoginRequest`, `TokenResponse`, `UserRead`
- `stores/auth.ts` — login/logout/refresh, localStorage persistence, computed `isAdmin`/`isTresorier`
- `views/LoginView.vue` — full PrimeVue form with i18n error handling
- `views/SettingsView.vue` — full settings form (association info + SMTP with TLS toggle)
- `layouts/AppLayout.vue` — responsive desktop sidebar + mobile drawer
- `components/NavMenu.vue` — role-aware navigation menu
- `views/DashboardView.vue` — placeholder
- `router/index.ts` — `requiresAuth` and `requiresAdmin` guards, lazy loading
- Tests: `tests/stores/auth.spec.ts` (11) + localStorage mock setup → **11 passing**

---

```text
Phase 1      Phase 2      Phase 3      Phase 4             Phase 5        Phase 6          Phase 7
Found.  ──►  Mgmt    ──►  Inv.    ──►  Payments & Treasury ──► Accounting ──► Advanced ──► Plan completion
├─ Docker    ├─Contacts    ├─Clients     ├─Payments           ├─Engine        ├─Year close   ├─Balance sheet
├─FastAPI    └─Chart       ├─Suppliers   ├─Cash               ├─Journal       ├─Salaries     ├─Bad debt
├─SQLite      of accounts  ├─PDF         ├─Counts             ├─Balance       ├─Excel import ├─CSV export
├─JWT auth                  └─E-mail      ├─Bank               ├─Ledger        └─Dashboard    ├─Excel preview
└─Vue.js                                  ├─Deposits           └─Manual entry                  ├─Rule preview
                                          ├─OFX import                                        └─OFX/QIF import
                                          └─Reconciliation
```

---

## Phase 1 — Foundations

> **Goal**: end-to-end working infrastructure (Docker → login → settings page)

| # | Status | Task | Details |
|---|---|---|---|
| 1.1 | ✅ | Project setup | Folder structure, `.gitignore`, `pyproject.toml` |
| 1.2 | ✅ | Docker | Multi-stage `Dockerfile` (Vue.js build + Python runtime), `docker-compose.yml` (1 service, 1 `./data` volume) |
| 1.3 | ✅ | FastAPI backend | `main.py`, `config.py` (Pydantic settings), `database.py` (SQLite WAL, AsyncSession) |
| 1.4 | ✅ | Alembic | Init, async `env.py`, migration `0001` (users + app_settings) |
| 1.5 | ✅ | JWT auth | Login/logout, refresh token, verification middleware, `User` model + roles (admin, treasurer, secretary, readonly) |
| 1.6 | ✅ | Frontend scaffold | Vue.js 3 + Vite + PrimeVue 4 + Pinia + Vue Router, responsive layout (sidebar + mobile drawer), login page |
| 1.7 | ✅ | Settings page | `AppSettings` model, `GET/PUT /api/settings` (admin), full `SettingsView.vue` (association info + SMTP) |
| 1.8 | ✅ | Serve frontend | FastAPI `StaticFiles` mount for the Vue build (`frontend/dist/`) |
| 1.9 | ✅ | `.env.example` + README | Documented environment variables, local installation README |

**Validation criterion**: `docker-compose up` → browser → login → working settings page ✅

**Final state (`feature/phase1-foundations`)**:

- Backend: FastAPI + SQLite WAL + Alembic + JWT auth + bcrypt + settings API → **44 tests, 88% coverage**
- Frontend: scaffold + login + layout + guards + auth store + full `SettingsView` → **11 Vitest tests**
- Infrastructure: multi-stage Dockerfile, docker-compose.yml, .dockerignore, .env.example

### Dependencies

- None (starting point)

---

## Phase 2 — Core management

> **Goal**: manage contacts and the chart of accounts

| # | Status | Task | Details |
|---|---|---|---|
| 2.1 | ✅ | Contact model | SQLAlchemy `Contact` + Alembic migration 0002 |
| 2.2 | ✅ | Contacts API | REST CRUD, search (last name/first name/e-mail), type filters, soft delete |
| 2.3 | ✅ | Contacts UI | PrimeVue DataTable, create/edit dialog (`ContactForm.vue`), confirmed deletion |
| 2.4 | ✅ | AccountingAccount model | SQLAlchemy + Alembic migration 0003 |
| 2.5 | ✅ | Default chart of accounts | 24 preconfigured accounts, idempotent seed |
| 2.6 | ✅ | Chart of accounts API | REST CRUD + `POST /api/accounting/accounts/seed` |
| 2.7 | ✅ | Chart of accounts UI | DataTable with type filter, create/edit dialog (`AccountForm.vue`) |

**Validation criterion**: create, update, search, and delete contacts and accounting accounts ✅

**Final state (`feature/phase2-base`)**:

- Backend: `Contact` + `AccountingAccount` models, services, schemas, routers → **103 tests, 89% coverage**
- Frontend: `ContactsView`, `ContactForm`, `AccountingAccountsView`, `AccountForm`, routes, i18n
- Alembic: migrations 0002 (contacts) + 0003 (accounting_accounts)

### Dependencies

- Phase 1 (auth + DB)

---

## Phase 3 — Invoicing

> **Goal**: create invoices, generate PDFs, and send them by e-mail

| # | Status | Task | Details |
|---|---|---|---|
| 3.1 | ✅ | `Invoice` + `InvoiceLine` model | Number format `YYYY-C/F-NNNN`, client/supplier type, label (`cs\|a\|cs+a\|general`), multiple lines, statuses |
| 3.2 | ✅ | Client invoices API | CRUD, automatic sequential numbering, status transitions, duplication, migration 0004 |
| 3.3 | ✅ | Client invoices UI | `ClientInvoicesView.vue`, `ClientInvoiceForm.vue` with dynamic lines, status/year filters |
| 3.4 | ✅ | Supplier invoices API | CRUD, PDF/image/WebP upload (10 MB max, UUID file name) |
| 3.5 | ✅ | Supplier invoices UI | `SupplierInvoicesView.vue`, `SupplierInvoiceForm.vue`, upload dialog |
| 3.6 | ✅ | PDF generation | WeasyPrint (lazy import) + Jinja2 `invoice.html` template |
| 3.7 | ✅ | E-mail sending | smtplib + STARTTLS/SSL, invoice PDF attachment, automatic `draft` → `sent` transition |

**Validation criterion**: create a `cs+a` client invoice → generate PDF → send it by e-mail → find it in the list; record a supplier invoice with an attachment ✅

**Final state (`feature/phase3-invoicing`)**:

- Backend: `Invoice` + `InvoiceLine` models, service layer (numbering, transitions, duplication), schemas, router, pdf service, e-mail service → **145 tests, 79% coverage**
- Frontend: `ClientInvoicesView`, `SupplierInvoicesView`, `ClientInvoiceForm`, `SupplierInvoiceForm`, routes, i18n
- Alembic: migration 0004 (invoices + invoice_lines)

### Dependencies

- Phase 2 (contacts for `contact_id`)

---

## Phase 4 — Payments & Treasury

> **Goal**: manage the full payment lifecycle (collection → deposit → bank)

| # | Task | Details |
|---|---|---|
| 4.1 | `Payment` model | Amount, method (`cash\|cheque\|transfer`), cheque number, dates, deposit status |
| 4.2 | Payments API | Record payments on invoices, partial payments, automatic invoice status updates |
| 4.3 | Payments UI | Per-invoice and global list, form, "to collect" view |
| 4.4 | `CashRegister` + `CashCount` model | Cash movements (`in`/`out`), physical counts by denomination |
| 4.5 | Cash API | Journal auto-fed by cash payments, manual outflows, count + reconciliation |
| 4.6 | Cash UI | Journal with running balance, denomination-based count form (`100€` to cents), difference display |
| 4.7 | `BankTransaction` model | Date, amount, reference, label, balance, source (`manual\|import`), reconciliation |
| 4.8 | Bank API | Journal, manual entry, running balance |
| 4.9 | `Deposit` model | Cheque/cash deposit slips linked to payments |
| 4.10 | Deposits API | Creation from undeclared payments, mark payments as deposited |
| 4.11 | Deposits UI | Interactive payment selection, cheque summary, banknote breakdown |
| 4.12 | Bank statement import | Crédit Mutuel CSV parser + OFX/QIF |
| 4.13 | Bank import UI | File upload, preview, import |
| 4.14 | Bank reconciliation | API + UI to match imported transactions with payments/invoices |

**Validation criterion**:
1. Record a cash payment → visible in cash journal → perform a physical count → reconciliation OK.
2. Create a cash deposit slip → deposit it to the bank → visible in the bank account.
3. Import a Crédit Mutuel CSV file → reconcile transactions.

### Dependencies

- Phase 3 (invoices for `invoice_id`)

---

## Phase 5 — Accounting

> **Goal**: automatic accounting entry generation and accounting views

| # | Task | Details |
|---|---|---|
| 5.1 | `AccountingRule` + `AccountingRuleEntry` model | Rule: trigger type, priority, active flag; entry: account, side, amount field, description template |
| 5.2 | `AccountingEntry` + `FiscalYear` model | Double-entry accounting lines, source traceability, fiscal years |
| 5.3 | Rules engine | `accounting_engine.py`: consume an event → apply rules → generate entries |
| 5.4 | Default rules seed | 15 preconfigured rules (course invoice, cash payment, etc.) |
| 5.5 | Automatic integration | Hooks in invoice/payment/deposit services → call rules engine |
| 5.6 | Accounting rules API | CRUD, enable/disable, preview |
| 5.7 | Accounting rules UI | Rules list, visual editor (drag-and-drop entry lines), preview |
| 5.8 | General journal API | Entries list, filters (date, account, source, fiscal year) |
| 5.9 | Journal UI | DataTable with advanced filters and links to source objects |
| 5.10 | Trial balance API | Aggregated debit/credit/balance per account |
| 5.11 | Balance UI | Summary table with totals and drill-down to the ledger |
| 5.12 | General ledger API | Account extract with running balance |
| 5.13 | General ledger UI | Equivalent to current "Client extract", "Cash extract", and "Current account extract" sheets |
| 5.14 | Invoice status view | Pivot view for invoice balances (debit, credit, remaining due) |
| 5.15 | Manual entry | API + form for exceptional accounting entries |
| 5.16 | Export | CSV and PDF for accounting views |

**Validation criterion**:
1. Create a `cs` invoice → 2 auto-generated entries (`411100/706110`) → visible in the journal → reflected in the balance.
2. Record a cash payment → 2 auto-generated entries (`531000/411100`) → invoice appears settled in the invoice status view.
3. Modify a rule → confirm that newly generated entries follow the updated rule.

### Dependencies

- Phase 4 (all management events that trigger accounting entries)

---

## Phase 6 — Advanced features

> **Goal**: fiscal year close, salaries, existing data import, dashboard

| # | Task | Details |
|---|---|---|
| 6.1 | `FiscalYear` model enhancements | `open`→`closing`→`closed` statuses, closing and carry-forward entries |
| 6.2 | Closing API | Pre-close checks, result calculation, balance sheet and income statement generation, locking |
| 6.3 | Closing UI | Step-by-step wizard: checks → result → balance sheet → lock → open new year |
| 6.4 | Opening balances | Automatic opening entries for the new fiscal year |
| 6.5 | Closed year access | Fiscal-year filters across accounting views, read-only access |
| 6.6 | `Salary` model | Month, hours, gross, employer charges, employee charges, tax, net (CEA data) |
| 6.7 | Salaries API | Monthly CRUD, subcontracting link to supplier invoices |
| 6.8 | Salaries UI | Monthly employee table, history, total cost, subcontractor links |
| 6.9 | Salary entries | Rules engine integration for salaries (`641000`, `645100`, `421000`, `431100`) |
| 6.10 | Excel import | Parse `Gestion 2025.xlsx` + `Comptabilité 2025.xlsx`, map columns, validate |
| 6.11 | Excel import UI | Upload, preview, validation report, import confirmation |
| 6.12 | Dashboard | Key indicators (bank balance, cash balance, unpaid invoices, current result) |
| 6.13 | Dashboard charts | Monthly income/expense evolution (Chart.js or vue-chartjs) |
| 6.14 | Dashboard alerts | Overdue invoices, unreconciled cash, deadlines |

**Validation criterion**:
1. Close a fiscal year → coherent balance sheet and income statement → opening entries → new year open.
2. Enter a monthly salary → auto-generated accounting entries.
3. Import the two real Excel source files → imported data matches the originals.
4. Dashboard shows the correct indicators and alerts.

### Dependencies

- Phase 5 (full accounting is required before year close)

---

## Phase 7 — Plan completion

> **Goal**: implement all modules identified in `plan.md` but not yet covered by phases 1–6

| # | Status | Task | Details |
|---|---|---|---|
| 7.1 | ✅ | Contact history view | `ContactHistory` schema + service + `GET /contacts/{id}/history`; `ContactDetailView.vue` |
| 7.2 | ✅ | Bad debt handling (`416xxx`) | `mark_creance_douteuse()`: `411xxx` → `416xxx` entries + `POST /contacts/{id}/mark-douteux` |
| 7.3 | ✅ | Simplified balance sheet | `BilanRead` schema + `get_bilan()` + `GET /accounting/entries/bilan`; `AccountingBilanView.vue` |
| 7.4 | ✅ | Accounting CSV export | `export_service.py`: journal, balance, result, balance sheet (UTF-8 BOM, `;` separator) |
| 7.5 | ✅ | Excel import preview | `PreviewResult` + `preview_gestion_file/comptabilite_file` + 2 dry-run preview endpoints |
| 7.6 | ✅ | Rule preview | `preview_rule()` service + `POST /accounting/rules/{id}/preview` (simulation without commit) |
| 7.7 | ✅ | OFX/QIF import | `parse_ofx()` (SGML + XML) + `parse_qif()` (multiple date formats) + 2 endpoints |
| 7.8 | ✅ | Dockerfile WeasyPrint runtime libs | Added system libs: libpango, libcairo, libgdk-pixbuf2.0, shared-mime-info |
| 7.9 | ✅ | Phase 7 tests | 19 new tests (OFX/QIF unit + 4 integration files) → 357 tests total |

**Validation criterion**:
1. `POST /contacts/{id}/mark-douteux` → two `411xxx/416xxx` entries created ✅
2. `GET /accounting/entries/bilan` → assets and liabilities balance ✅
3. `GET /accounting/entries/journal/export/csv` → UTF-8 CSV download ✅
4. `POST /import/excel/gestion/preview` → row estimate without import ✅
5. `POST /bank/transactions/import-ofx` → transactions created from an OFX file ✅

**Final state**:

- Backend: 357 tests, 0 failures, 74% coverage
- Frontend: `AccountingBilanView.vue`, `ContactDetailView.vue`, journal CSV export, import preview, new routes, complete i18n
- Ruff: 0 errors

### Dependencies

- Phases 1–6 (all previous layers)

---

## Delivery summary by phase

| Phase | Modules | Tasks |
|---|---|---|
| **1. Foundations** | Auth, settings | 8 tasks |
| **2. Core management** | Contacts, chart of accounts | 7 tasks |
| **3. Invoicing** | Client invoices, supplier invoices, PDF, e-mail | 7 tasks |
| **4. Payments & Treasury** | Payments, cash, bank, deposits, bank import, reconciliation | 14 tasks |
| **5. Accounting** | Rules engine, journal, balance, ledger, invoice status | 16 tasks |
| **6. Advanced features** | Year close, salaries, Excel import, dashboard | 14 tasks |
| **7. Plan completion** | Balance sheet, bad debt, CSV export, import preview, OFX/QIF | 9 tasks |
| **Total** | **14 modules** | **75 tasks** |

---

## Dependency diagram

```text
Phase 1 (Foundations)
    │
    ▼
Phase 2 (Contacts + chart of accounts)
    │
    ▼
Phase 3 (Invoicing)
    │
    ▼
Phase 4 (Payments & Treasury)
    │
    ▼
Phase 5 (Accounting + rules engine)
    │
    ▼
Phase 6 (Year close + salaries + import + dashboard)
    │
    ▼
Phase 7 (Balance sheet, bad debt, CSV export, preview, OFX/QIF)
```

> Each phase depends on the previous one. Within a phase, some tasks can run in parallel, for example 2.1–2.3 (Contacts) and 2.4–2.7 (Chart of accounts).
