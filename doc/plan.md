# Plan — Solde ⚖️ Association Accounting Application

## TL;DR

Solde is a modular monolithic Python web application (FastAPI + SQLite) designed to manage the accounting of a French loi 1901 tutoring association. It replaces two Excel files with an integrated solution covering client and supplier invoicing, multi-method payment tracking, cash handling, bank reconciliation, and double-entry accounting with automatically generated entries driven by a configurable rules engine. It is deployed with Docker on Synology and targets roughly 384 MB of RAM at most. The UI is a modern responsive Vue.js 3 application.

---

## Technical architecture

### Stack

| Component | Choice | RAM rationale |
|---|---|---|
| Backend | **FastAPI** + Uvicorn (1 worker) | ~50–80 MB idle |
| Database | **SQLite** (WAL mode) | ~0 MB (file-based) |
| Frontend | **Vue.js 3** + PrimeVue + Vite | 0 MB on the server side |
| ORM | **SQLAlchemy 2** (async) | Included in the Python process |
| Migrations | **Alembic** | CLI only, no runtime RAM cost |
| PDF | **WeasyPrint** | ~30–50 MB peak during generation |
| E-mail | **smtplib** (Python stdlib) | No extra memory cost |
| Auth | **JWT** (`python-jose` + bcrypt) | Included in the Python process |
| Container | **Single Docker container** | One service only |

**Estimated total RAM: ~80–130 MB idle, ~180 MB peak during PDF generation, well below the 384 MB budget.**

### Project structure

```
solde/
├── docker-compose.yml
├── Dockerfile
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Configuration (fiscal year, SMTP, etc.)
│   ├── database.py                # SQLite session + engine
│   ├── models/                    # SQLAlchemy models
│   │   ├── contact.py             # Contacts (members, suppliers)
│   │   ├── invoice.py             # Invoices (clients + suppliers)
│   │   ├── payment.py             # Payments
│   │   ├── cash.py                # Cash movements and counts
│   │   ├── bank.py                # Bank transactions and deposits
│   │   ├── accounting_*.py        # Entries, accounts, fiscal years, rules
│   │   ├── salary.py              # Salaries
│   │   └── user.py                # Users and roles
│   ├── routers/                   # API routes by module
│   ├── services/                  # Business logic by module
│   ├── schemas/                   # Pydantic schemas
│   ├── templates/                 # HTML templates for PDF generation (Jinja2)
│   └── alembic/                   # Database migrations
├── frontend/
│   ├── src/
│   │   ├── views/                 # Vue pages
│   │   ├── components/            # Reusable components
│   │   ├── composables/           # Shared frontend logic
│   │   ├── stores/                # Pinia stores
│   │   └── api/                   # API client layer (axios)
│   └── package.json
├── data/                          # Docker volume: SQLite + uploaded files
└── tests/
```

### Single-container Docker deployment

- **One Dockerfile only**: builds Vue.js and serves the static assets through FastAPI.
- **One mounted volume**: `./data:/app/data` for SQLite, uploaded supplier invoices, and generated PDFs.
- **Portainer-compatible**: standard `docker-compose.yml`.

---

## Data model

### `contacts`
`id, type (client|supplier|both), last_name, first_name, email, phone, address, notes, created_at`
- A member is represented as a `client` contact.
- A subcontractor or supplier is represented as a `supplier` contact.

### `invoices`
`id, number (YYYY-NNNN), type (client|supplier), contact_id, date, due_date, label (cs|a|cs+a|general), description, total_amount, paid_amount (computed), status (draft|sent|paid|partial|overdue|disputed), pdf_path, created_at`

### `invoice_lines`
`id, invoice_id, description, quantity, unit_price, amount`
- Supports multi-line invoices such as course fees plus membership fees on the same document.

### `payments`
`id, invoice_id, contact_id, amount, date, method (cash|cheque|transfer), cheque_number, reference, deposited (bool), deposit_date, notes, created_at`
- `deposited` indicates whether a cheque or a cash receipt has already been deposited in the bank.

### `cash_register`
`id, date, amount, type (in|out), contact_id, payment_id, reference, description, balance_after, created_at`

### `cash_counts`
`id, date, count_100, count_50, count_20, count_10, count_5, count_2, count_1, count_cents, total_counted, balance_expected, difference, notes`

### `bank_transactions`
`id, date, amount, reference, description, balance_after, reconciled (bool), reconciled_with, source (manual|import), created_at`

### `deposits`
`id, date, type (cheques|cash), total_amount, bank_reference, notes`
- Linked to payments through a `deposit_payments` join table.

### `accounting_accounts`
`id, number (e.g. 411100), label, type (asset|liability|expense|income), parent_number, is_default (bool)`
- Pre-filled with a simplified non-profit chart of accounts.
- Extendable by the user.

### `accounting_entries`
`id, entry_number, date, account_id, label, debit, credit, fiscal_year_id, source_type (invoice|payment|salary|bank|manual|closing), source_id, created_at`
- `source_type` + `source_id` keep a trace back to the originating business action.
- Entries become immutable once the fiscal year is closed.

### `accounting_rules`
`id, name, trigger_type (invoice_client_cs|invoice_client_a|payment_cash|payment_cheque|payment_transfer|deposit_cash|deposit_cheques|salary|subcontracting|bank_fees|manual), is_active (bool), priority, description`

### `accounting_rule_entries`
`id, rule_id, account_number, side (debit|credit), amount_field (amount|gross_salary|net_salary|employer_charges|employee_charges), description_template`
- Each rule contains N entries defining the generated journal lines.
- `description_template` uses Jinja2 syntax, for example `{{invoice.number}} {{contact.last_name}}`.

### `fiscal_years`
`id, name, start_date, end_date, status (open|closing|closed), opening_balance_entry_id`
- Default range is August N to July N+1, and is configurable.

### `users`
`id, username, email, password_hash, role (admin|tresorier|secretaire|readonly), is_active, created_at`

### `salaries`
`id, employee_id (→ contacts), month (YYYY-MM), hours, gross, employee_charges, employer_charges, tax, net_pay, created_at`
- Data is entered manually from the CEA payroll platform.
- Total employer cost is computed as `gross + employer_charges`.

---

## Detailed features

### Module 1 — Authentication & Settings
- JWT login with refresh token
- Roles: admin (full access), treasurer (management + accounting), secretary (invoices + payments), readonly (view only)
- Settings page for fiscal year configuration (default August→July), association details (name, SIRET, address shown on invoices), SMTP settings, and logo
- Chart of accounts configuration (add/update accounts)

### Module 2 — Contacts
- Contacts CRUD with type (`client`, `supplier`, `both`)
- Contact detail view with invoices, payments, and remaining balance
- Search and filters
- Bad debt handling with transfer to `416xxx` accounts

### Module 3 — Client invoices
- Invoice creation with contact selection, type (`cs`/`a`/`cs+a`/`general`), invoice lines, and automatic total calculation
- Automatic sequential numbering in `YYYY-NNNN` format
- Statuses: Draft → Sent → Partially paid → Paid / Disputed
- PDF generation from an HTML template (logo, association details, line details, legal notice for non-VAT non-profit)
- E-mail sending with PDF attachment
- Invoice duplication for recurring billing
- **Automatic triggering** of accounting entries through the rules engine

### Module 4 — Supplier invoices
- Record date, supplier, amount, description, and reference
- Upload PDF or image of the supplier invoice
- Track payment status
- Typical categories: subcontracting, supplies, insurance, telecom, miscellaneous fees
- **Automatic triggering** of accounting entries

### Module 5 — Payments
- Record a payment on an invoice: amount, method, date, cheque number if needed
- Partial payments are supported
- Automatic invoice status update
- "Payments to deposit" view for cheques and cash not yet deposited
- **Automatic triggering** of accounting entries depending on payment method

### Module 6 — Cash
- Cash journal: chronological list of movements (cash collections, bank cash deposits, purchases)
- Real-time balance
- **Physical count** UI by denomination (100€, 50€, 20€, 10€, 5€, 2€, 1€, cents) with automatic total calculation
- **Reconciliation** between expected balance and counted cash
- Count history

### Module 7 — Bank
- Bank journal with running balance
- **Statement import**: CSV (Crédit Mutuel format), OFX/QIF
- Smarter parsing of imported bank labels
- Bank reconciliation with existing payments and invoices
- **Deposit slip** creation for cheques and cash with payment selection, total calculation, and internal deposited flag

### Module 8 — Accounting rules engine
- **Default rules** preconfigured from the Excel bookkeeping logic already identified
- Editing UI: define N journal lines for each event type (course invoice, cash payment, etc.)
- Each generated line defines source account, side (debit/credit), source amount field, and label template
- Rules can be enabled or disabled
- New trigger types can be added
- **Preview** generated entries before applying them
- Rules are applied automatically on each management action such as invoice creation, payment recording, and bank deposit creation

### Module 9 — Accounting
- **General journal** with filters by date, account, and source
- **Trial balance** with debit/credit/balance summary by account
- **General ledger** per account, equivalent to current extracts for clients, cash, and current account
- **Invoice status view** showing the balance of each invoice
- Manual journal entry form for exceptional cases not covered by rules
- Consistency check ensuring total debits equal total credits
- CSV and PDF exports

### Module 10 — Fiscal year close
- Pre-close checks: balanced accounting and fully reconciled invoices
- Result calculation (`income - expenses`) posted to account `120000` or `129000`
- Simplified balance sheet generation
- Income statement generation
- Carry-forward entry to `110000`
- Fiscal year lock after close
- Open the next fiscal year with opening entries
- Read-only consultation of closed years

### Module 11 — Salaries
- Monthly salary entry per employee from CEA data: hours, gross, employer charges, employee charges, tax, net
- Automatic total employer cost calculation
- No payroll calculation logic in Solde itself, because CEA remains the payroll source
- Monthly history
- Subcontracting link with supplier invoices for self-employed teachers
- **Automatic triggering** of accounting entries (`641000`, `645100`, `421000`, `431100`, etc.)

### Module 12 — Existing data import
- Import current Excel files (`Gestion 2025` + `Comptabilité 2025`)
- Automatic mapping of known columns
- Validation report before import
- Import of contacts, invoices, payments, and accounting entries

### Module 13 — Dashboard
- Global view with bank balance, cash balance, unpaid invoices, and current result
- Simple charts showing monthly income/expense evolution
- Alerts for overdue invoices, stale cash reconciliation, and key deadlines

---

## Default accounting rules

| Event | Debit | Credit |
|---|---|---|
| Client invoice - course (`cs`) | `411100` Members | `706110` Tutoring income |
| Client invoice - membership (`a`) | `411100` Members | `756000` Membership income |
| Payment received - cash | `531000` Cash | `411100` Members |
| Payment received - cheque | `511200` Cheques to deposit | `411100` Members |
| Payment received - transfer | `512100` Current account | `411100` Members |
| Cash deposit to bank | `512100` Current account | `531000` Cash |
| Cheque deposit to bank | `512100` Current account | `511200` Cheques to deposit |
| Supplier invoice - subcontracting | `611100` Subcontracting | `401xxx` Supplier |
| Supplier payment - bank transfer | `401xxx` Supplier | `512100` Current account |
| Supplier invoice - supplies | `602250` Supplies | `401xxx` or `531000` |
| Bank fees | `627000` Banking services | `512100` Current account |
| Gross salary | `641000` Salaries | `421000` Salaries payable |
| Employer charges | `645100` Employer contributions | `431100` URSSAF |
| Salary payment | `421000` Salaries payable | `512100` Current account |
| URSSAF payment | `431100` URSSAF | `512100` Current account |

---

## Key files to create

### Backend
- `backend/main.py` — entry point, router registration, StaticFiles mounting
- `backend/config.py` — Pydantic settings (DB path, JWT secret, SMTP, fiscal year)
- `backend/database.py` — async SQLite WAL session
- `backend/models/*.py` — SQLAlchemy models
- `backend/routers/*.py` — one router per module
- `backend/services/*.py` — business logic modules
- `backend/services/accounting_engine.py` — accounting rules engine (core of the accounting automation)
- `backend/services/pdf_generator.py` — PDF generation with WeasyPrint
- `backend/services/bank_import.py` — CSV/OFX statement parsers
- `backend/services/excel_import.py` — import of legacy Excel files
- `backend/schemas/*.py` — Pydantic validation
- `backend/templates/invoice.html` — Jinja2 template for invoice PDFs

### Frontend
- `frontend/src/views/Login.vue`
- `frontend/src/views/Dashboard.vue`
- `frontend/src/views/Contacts.vue` + `ContactDetail.vue`
- `frontend/src/views/Invoices.vue` + `InvoiceForm.vue` + `InvoiceDetail.vue`
- `frontend/src/views/Payments.vue` + `PaymentForm.vue`
- `frontend/src/views/CashRegister.vue` + `CashCount.vue`
- `frontend/src/views/Bank.vue` + `BankImport.vue` + `BankReconciliation.vue`
- `frontend/src/views/Deposits.vue` + `DepositForm.vue`
- `frontend/src/views/Accounting.vue` + `Journal.vue` + `Balance.vue` + `Ledger.vue`
- `frontend/src/views/AccountingRules.vue` + `RuleEditor.vue`
- `frontend/src/views/FiscalYearClose.vue`
- `frontend/src/views/Salaries.vue`
- `frontend/src/views/Settings.vue`
- `frontend/src/views/ImportExcel.vue`

### Infrastructure
- `Dockerfile` — multi-stage build: Vue.js build + Python runtime
- `docker-compose.yml` — one service, one volume, one port mapping
- `.env.example` — environment variables

---

## Global verification checklist

1. **Unit tests** (`pytest`) for critical business logic such as the rules engine, salary calculations, invoice numbering, and fiscal year close.
2. **Integration tests** for complete workflows (`invoice → payment → accounting entry → balance`).
3. **Docker smoke test**: `docker-compose up` from scratch must produce a working application.
4. **RAM test**: use `docker stats` under load and confirm usage stays below 384 MB.
5. **Responsive test**: verify all views on mobile using Chrome DevTools.
6. **Excel import test**: import the real files and verify coherence.
7. **Fiscal year close test**: close a full year and verify the balance sheet and income statement.
8. **SMTP test**: send an invoice by e-mail.

---

## Decisions already taken

- **Modular monolith** over microservices because RAM is the primary constraint.
- **SQLite** over PostgreSQL because it adds no extra runtime memory and is sufficient for the expected volume.
- **Vue.js 3 + PrimeVue** for the frontend because it offers rich components such as DataTable, Calendar, and Dialog with a modern application feel.
- **Simplified non-profit chart of accounts** with extension capability.
- **CSV/OFX statement import** for banking, with no DSP2/Open Banking connection in the MVP.
- **No VAT management**, because the association is out of VAT scope.
- **Euro-only** support.
- **`YYYY-NNNN`** invoice numbering.
- **Salaries** are entered manually from CEA data.
- **Deposit slips** are tracked internally only, with no PDF output.
- **Closed fiscal years** remain visible in read-only mode.

## Explicitly excluded scope

- Bank API integration (DSP2/Open Banking)
- VAT management
- Multi-currency support
- FEC export (`Fichier des Écritures Comptables`), which could be added later
- Grants management as a dedicated module
- Automated budget planning
- Native mobile application
