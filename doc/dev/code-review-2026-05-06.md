# Code Review — Solde ⚖️ — 2026-05-06

Deep code review covering: security, architecture, quality, efficiency, and UI/UX.

---

## Summary

The codebase is generally **well-structured**, with a clear separation of concerns (routers → services → models), proper role-based access control, solid auth patterns (HttpOnly refresh cookies, token invalidation on password change), and good use of type annotations. The following findings represent areas for improvement.

| Category | Critical | High | Medium | Low | Total |
| --- | --- | --- | --- | --- | --- |
| Security | 0 | 2 | 3 | 1 | 6 |
| Architecture | 0 | 1 | 2 | 1 | 4 |
| Quality | 0 | 1 | 3 | 2 | 6 |
| Efficiency | 0 | 1 | 2 | 0 | 3 |
| **Total** | **0** | **5** | **10** | **4** | **19** |

---

## Security findings

### S-HIGH-1 — `_next_entry_number` race condition (entry numbering)

**Files**: `backend/services/accounting_engine.py:48-60`

`_next_entry_number()` does `SELECT MAX(entry_number)` then generates the next value. With concurrent requests, two operations could get the same max value and produce duplicate numbers. There is no `UNIQUE` constraint on `entry_number` and no retry logic (unlike invoice numbering which already has a retry on `IntegrityError`).

**Impact**: Duplicate accounting entry numbers → data integrity issue.
**Fix**: Add a `UNIQUE` constraint on `accounting_entries.entry_number` + retry loop on `IntegrityError`, mirroring the existing pattern in `invoice_service._next_number()`.

---

### S-HIGH-2 — Chat API key stored as plaintext in DB

**Files**: `backend/models/app_settings.py`, `backend/services/chat_service.py:44`, `backend/routers/settings.py`

The `chat_api_key` (Google/OpenAI API key) is stored as a plain `String` column in `app_settings` and returned via `GET /api/settings`. While this endpoint is manager-restricted, the API key is visible to secretaires/trésoriers who are not admins. Also, API keys in SQLite are backed up in plain text.

**Impact**: API key exposure to non-admin roles; key visible in backups.
**Fix**: (1) Mask the API key in `AppSettingsRead` schema (only show last 4 chars). (2) Consider encrypting at rest with a key derived from `JWT_SECRET_KEY`. (3) Only expose the full key on a dedicated admin-only endpoint.

---

### S-MED-1 — SMTP password in plaintext in DB and API response

**Files**: `backend/models/app_settings.py`, `backend/schemas/settings.py`

Same pattern as chat API key: `smtp_password` is stored in clear in the DB and returned in the `GET /api/settings` response visible to managers.

**Fix**: Mask in API response; expose full value only through a separate admin-only write endpoint.

---

### S-MED-2 — Missing CSRF protection on state-changing cookie-authenticated endpoint

**Files**: `backend/routers/auth.py:237-264` (`POST /api/auth/refresh`)

The refresh endpoint relies on a cookie for authentication. While `samesite="strict"` mitigates CSRF in modern browsers, older browsers may not enforce it. A CSRF token or double-submit pattern would add defense-in-depth.

**Impact**: Low in practice (strict SameSite + single-origin app), but not standards-compliant for cookie-based mutation.
**Fix**: Consider adding a custom header check (e.g. `X-Requested-With`) that cannot be sent cross-origin.

---

### S-MED-3 — No password length upper bound

**Files**: `backend/schemas/auth.py:14-21`

The password validator enforces a minimum of 8 characters but no maximum. An attacker could submit a multi-MB password, causing bcrypt to spend excessive CPU time hashing.

**Impact**: Potential DoS via login/change-password endpoints.
**Fix**: Add `max_length=128` (or similar) on password fields in Pydantic schemas.

---

### S-LOW-1 — `_SafeFormatMap` in email service — limited template injection surface

**Files**: `backend/services/email_service.py:84-87`

The `_SafeFormatMap` class is safe for unknown keys but the template is user-editable (admin configures it). A malicious or ignorant admin could insert `{__class__}` or similar attributes. Python's `str.format_map()` does not allow arbitrary attribute access (unlike `format(**locals())`), so this is informational only.

**Impact**: None with current implementation, but document the constraint.
**Fix**: Document that only whitelisted keys are supported; optionally validate template keys on save.

---

## Architecture findings

### A-HIGH-1 — `_next_entry_number` exposed as a pseudo-private function across modules

**Files**: `backend/services/accounting_engine.py:48`, `backend/services/accounting_entry_service.py:35`

`_next_entry_number` is prefixed with `_` (private convention) but is imported and used by `accounting_entry_service.py`. This breaks the encapsulation contract and makes the dependency hard to discover.

**Fix**: Rename to `next_entry_number` (public) or extract to a shared utility module.

---

### A-MED-1 — Services commit transactions directly

**Files**: Multiple services (`accounting_account.py`, `accounting_rule_service.py`, etc.)

Some services call `await db.commit()` directly. This is fine in isolation, but when a router calls multiple services in one request, partial commits can leave inconsistent state if a later step fails. The `get_db()` dependency already auto-commits on success.

**Impact**: Risk of partial data in complex operations.
**Fix**: Audit services that commit directly; prefer `flush()` in services and let the session context manager handle commit/rollback. The router should be the commit boundary.

---

### A-MED-2 — Large router files without sub-modules

**Files**: `backend/routers/bank.py` (~550 lines), `backend/routers/invoice.py` (~520 lines)

These routers contain significant business logic delegation and many endpoints. While not critical, extracting helper functions or splitting into sub-routers would improve maintainability.

**Fix**: Consider splitting `bank.py` into `bank_transactions.py` / `bank_deposits.py` / `bank_import.py` sub-routers.

---

### A-LOW-1 — Duplicate schema patterns for bank payment operations

**Files**: `backend/schemas/bank.py`

Multiple schemas (`BankTransactionClientPaymentCreate`, `BankTransactionClientPaymentLink`, `BankTransactionClientPaymentLinks`, `BankTransactionClientPaymentsCreate`) share very similar structures. The router also uses `BankTransactionClientPaymentCreate` for supplier payments (`create_supplier_payment_from_transaction`).

**Fix**: Consolidate or rename schemas for clarity. Low priority.

---

## Quality findings

### Q-HIGH-1 — Silent error swallowing in frontend `.catch(() => {})`

**Files**: Multiple views (`ClientInvoicesView.vue:1231`, `ContactHistoryContent.vue:797,807`, `DashboardView.vue:340`, etc.)

At least 10 locations silently swallow API errors with empty `.catch(() => {})`. Users get no feedback when operations fail (e.g. payment creation, deposit listing).

**Impact**: Silent failures → user confusion, potential data inconsistency without awareness.
**Fix**: Replace with `.catch((e) => toast.add({ severity: 'error', ... }))` or at minimum log to console. Critical operations should always surface errors.

---

### Q-MED-1 — Missing test coverage for accounting engine

**Files**: `tests/` — no `test_accounting_engine.py`

The accounting engine is the most critical business logic (journal entry generation, rule application, fiscal year assignment). Despite the project's 90% coverage target for business services, there is no dedicated test file for `accounting_engine.py`.

**Fix**: Create `tests/unit/test_accounting_engine.py` with tests for rule application, split entries, double-entry creation, and entry numbering.

---

### Q-MED-2 — No input length validation on several text fields

**Files**: `backend/schemas/bank.py`, `backend/schemas/payment.py`

Fields like `description`, `notes`, `reference` in bank transaction and payment schemas have no `max_length` constraint. SQLAlchemy models use `Text` (unlimited) or `String(100)` but the Pydantic schema doesn't enforce the limit.

**Impact**: Data can be truncated silently at DB level for `String(N)` columns, or can be arbitrarily large for `Text` columns.
**Fix**: Add `max_length` validators in Pydantic schemas matching DB constraints.

---

### Q-MED-3 — Inconsistent error messages language

**Files**: Multiple routers

Some error messages are in French (`"Une transaction avec cette référence existe déjà."`) while others are in English (`"Invoice not found"`, `"Insufficient permissions"`). This makes error handling unpredictable for the frontend.

**Impact**: Inconsistent UX; frontend cannot reliably match on error strings for custom handling.
**Fix**: Standardize on English error codes with a `code` field (already done in auth). Add i18n-mapped error display in frontend based on the code.

---

### Q-LOW-1 — `_REGISTERED_MODEL_MODULES` in conftest.py is fragile

**Files**: `tests/conftest.py:34-77`

All models must be manually imported for table creation. If a new model is added without updating this list, tests will fail with cryptic errors. No check ensures completeness.

**Fix**: Use `import backend.models` with a registry pattern, or dynamically import all modules in `backend/models/`.

---

### Q-LOW-2 — Missing `__all__` exports in service/model packages

**Files**: `backend/services/__init__.py`, `backend/models/__init__.py`

Both `__init__.py` files exist but neither defines `__all__`. This makes it easy to accidentally import private symbols.

**Fix**: Low priority — add `__all__` or at least ensure `__init__.py` re-exports public API.

---

## Efficiency findings

### E-HIGH-1 — N+1 query pattern in `_serialize_transactions`

**Files**: `backend/routers/bank.py:57-83`

For each transaction listed, `_serialize_transaction` loads payment IDs individually. The batch version `_serialize_transactions` exists and uses `get_transaction_payment_ids_map`, which is good. However, `_serialize_transaction` (singular) is called after every mutation endpoint (create, update, link, etc.) — each call does 1 extra query per transaction.

More critically: the `list_transactions` endpoint returns up to 1000 transactions, each serialized via the batch function which does a single query for all IDs — this is efficient. But individual mutation endpoints call the singular version — this is fine (1 extra query for 1 tx).

**Real issue**: `get_monthly_funds_series` in `bank_service.py` performs 6-24 separate queries (one per month window) without batching.

**Fix**: Refactor `get_monthly_funds_series` to use a single query with `GROUP BY` on month, or a window function.

---

### E-MED-1 — `_next_entry_number` called per entry in a loop

**Files**: `backend/services/accounting_engine.py:116,264`

When creating multiple entries (e.g. a complete double-entry set for a split invoice with 3+ lines), `_next_entry_number` is called separately for each entry. Each call does `SELECT MAX(...)` + `flush()`. For a split invoice this can be 4-6 sequential queries.

**Fix**: Pre-allocate a range of numbers in a single call (e.g. `_next_entry_numbers(db, count=N)`), then assign them.

---

### E-MED-2 — `pdf_service` recreates Jinja2 `Environment` on every call

**Files**: `backend/services/pdf_service.py:8-10`

`_template_env()` creates a new `Environment` and `FileSystemLoader` every time a PDF is generated. While templates are filesystem-based and relatively cheap to load, the Jinja2 `Environment` with compiled templates would benefit from caching.

**Fix**: Make `_template_env()` a module-level singleton (or use `@lru_cache`).

---

## Positive observations (no action needed)

- **Auth flow**: HttpOnly cookies, token-in-memory, refresh rotation, password invalidation — well implemented.
- **XSS mitigation**: Markdown rendered with DOMPurify sanitization; Jinja2 templates have `autoescape=True`.
- **File upload validation**: Magic bytes check + MIME type + size limit — thorough.
- **Path traversal prevention**: Backup filenames validated with regex before filesystem access.
- **Rate limiting**: Simple but effective for single-worker deployment.
- **Security headers**: HSTS, CSP, X-Frame-Options all applied.
- **Decimal arithmetic**: Properly using `Decimal` for all monetary amounts.
- **Audit trail**: Comprehensive audit logging on all state-changing operations.
- **Non-root Docker**: Application runs as dedicated `solde` user.
- **WAL mode**: SQLite configured for better concurrent read performance.

---

## Recommendations prioritized

| Priority | ID | Action | Effort |
| --- | --- | --- | --- |
| 1 | S-HIGH-1 | Entry number race condition fix | ~15 min |
| 2 | S-HIGH-2 | Mask API keys in settings response | ~15 min |
| 3 | Q-HIGH-1 | Frontend: surface silent errors | ~30 min |
| 4 | E-HIGH-1 | Optimize monthly funds query | ~20 min |
| 5 | A-HIGH-1 | Rename `_next_entry_number` → public | ~5 min |
| 6 | S-MED-1 | Mask SMTP password in response | ~10 min |
| 7 | S-MED-3 | Password max length validation | ~5 min |
| 8 | Q-MED-1 | Accounting engine unit tests | ~45 min |
| 9 | E-MED-1 | Batch entry number allocation | ~15 min |
| 10 | E-MED-2 | Cache Jinja2 Environment | ~5 min |
| 11 | Q-MED-2 | Schema max_length validators | ~20 min |
| 12 | Q-MED-3 | Standardize error codes | ~30 min |
| 13 | A-MED-1 | Audit service-level commits | ~25 min |
| 14 | S-MED-2 | CSRF defense-in-depth | ~15 min |
| 15 | A-MED-2 | Split large router files | ~20 min |
