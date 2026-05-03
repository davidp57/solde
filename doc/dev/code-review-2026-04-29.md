# Code Review — Solde v1.1.0

**Date**: 2026-04-29  
**Scope**: Python backend (FastAPI/SQLAlchemy), TypeScript frontend (Vue 3), infrastructure  
**Test suite**: 999/999 ✅

---

## Executive summary

The overall architecture is solid: clear router → service → model separation, Alembic migrations, comprehensive audit log, and integration tests covering critical user flows. Issues concentrate in three categories: authentication security, transaction atomicity, and minor technical debt.

| Severity | Count | Tickets |
|---|---|---|
| 🔴 Critical | 3 | TEC-133, TEC-134, TEC-135 |
| 🟠 Moderate | 5 | TEC-136, TEC-137, TEC-138, TEC-139, TEC-140 |
| 🟡 Minor | 2 | TEC-141, TEC-142 |

---

## 🔴 Critical issues

### TEC-133 — Access token stored in `localStorage` (XSS vulnerability)

**File:** `frontend/src/stores/auth.ts` (lines 34–36, 58–59)

```ts
function saveAccessToken(access: string): void {
  accessToken.value = access
  localStorage.setItem(ACCESS_TOKEN_KEY, access)  // ← accessible via JS
}
```

The refresh token is correctly protected (HttpOnly cookie), but the access token persisted in `localStorage` is accessible to any JavaScript running on the page. An XSS attack (via a compromised dependency, a mis-escaped template, etc.) allows stealing this token and impersonating the session.

**Recommended pattern:** store the access token **in memory only** (Pinia `ref`, not persisted). On page reload, silently call `POST /api/auth/refresh` (the HttpOnly cookie is sent automatically) to obtain a new token. The existing `initFromStorage()` and `localStorage` auth logic become unnecessary.

**Impact:** session takeover without user interaction if XSS is exploited.

---

### TEC-134 — Broken atomicity between data change and audit log

**Files:** `backend/routers/auth.py` (lines 437–447), `backend/routers/invoice.py` (lines 159–166)

Example in `update_user`:

```python
changes = body.model_dump(exclude_unset=True)
await db.commit()       # ← transaction 1: user change committed
await db.refresh(user)
await record_audit(...)  # ← added to session AFTER commit
return user
# Session closes: get_session() commits audit in transaction 2
```

The data change and the audit entry live in **two separate transactions**. If the second transaction fails (network hiccup, restart), the data is modified but the audit is lost. Any post-incident security investigation will be incomplete.

**Fix:** call `record_audit()` **before** `await db.commit()`. A single commit suffices; `get_session()` commits automatically at context exit.

```python
# Correct
await record_audit(db, action=..., actor=..., ...)
await db.commit()
```

---

### TEC-135 — Race condition on invoice numbering

**File:** `backend/services/invoice.py` (lines 154–168)

```python
result = await db.execute(
    select(Invoice.number).where(...).order_by(Invoice.id.desc()).limit(1)
)
last = result.scalar_one_or_none()
seq = int(m.group(1)) + 1 if m else 1
# ← no lock between SELECT and INSERT
```

Two concurrent create-invoice requests compute the same `last`, derive the same `seq`, and attempt to insert the same number. The `UNIQUE` constraint on `Invoice.number` then raises an unhandled `IntegrityError` → HTTP 500 for the user.

For the single-worker deployment (Synology NAS), the risk is low but real (multiple tabs, parallel API calls from the frontend). Options:
1. Wrap the numbering in a `SELECT ... FOR UPDATE` / `BEGIN IMMEDIATE` on SQLite.
2. Add a retry loop catching `IntegrityError` (simpler, less elegant).
3. Delegate to a database sequence (SQLite does not support this natively).

---

## 🟠 Moderate issues

### TEC-136 — Absolute file paths stored in the database

**File:** `backend/routers/invoice.py` (lines 532–536)

```python
upload_dir = Path("data/uploads/invoices").resolve()  # → absolute /app/data/...
file_path = upload_dir / safe_name
# Stored in Invoice.file_path / Invoice.pdf_path
```

Absolute paths (e.g. `/app/data/uploads/invoices/abc123.pdf`) become stale if the container is recreated in a different directory, the app is moved, or the data is migrated. All files attached to existing invoices would become inaccessible.

**Fix:** store paths relative to a configurable root (e.g. `uploads/invoices/abc123.pdf`), and resolve to the full path at read time via a centralised helper.

---

### TEC-137 — Double JWT decoding on every API request

**Files:** `backend/main.py` (line 116), `backend/routers/auth.py` (line 76)

`MustChangePasswordMiddleware.dispatch()` decodes the JWT on **every** non-exempt API request, then `get_current_user` decodes it again within the same request lifecycle. Unnecessary overhead.

**Options:**
- Store the decoded payload in `request.state` from the middleware and read it in `get_current_user`.
- Remove the decode logic from the middleware and delegate it entirely to `get_current_user` (the `mcp` guard can be checked after token validation).

---

### TEC-138 — Unbounded growth of the rate limiter dictionary

**File:** `backend/services/rate_limiter.py`

```python
self._attempts: dict[str, list[float]] = defaultdict(list)
```

Cleanup of expired attempts (`_attempts[key] = [t for t in ...]`) is only triggered when the **same key** (IP) passes through `is_rate_limited()` again. IPs that attempt once or twice and then disappear remain in the dictionary indefinitely. During a mass scan (thousands of source IPs), memory usage is unbounded.

**Fix:** add a periodic purge (e.g. every 1000 calls or via `asyncio.create_task` every N minutes) that removes keys whose entire attempt list has expired. Alternative: use a bounded LRU cache.

---

### TEC-139 — OpenAI token usage not tracked in streaming mode

**File:** `backend/services/chat_service.py` (line 211)

```python
# Gemini → correctly tracks prompt_tokens + completion_tokens ✅
# OpenAI → always returns None ❌
yield delta.content, None
```

The Gemini path correctly surfaces token counters via `usage_metadata`. The OpenAI path always returns `None`, making the `prompt_tokens` / `completion_tokens` columns in `chat_log` useless for monitoring OpenAI API consumption.

**Fix:** pass `stream_options={"include_usage": True}` in `client.chat.completions.create()` and extract `chunk.usage` from the last event.

---

### TEC-140 — Audit log endpoint without pagination or filtering

**File:** `backend/routers/settings.py` (line 410)

```python
result = await db.execute(select(AuditLog).order_by(...).limit(1000))
```

1,000 entries returned with no filters (by date, actor, action) and no pagination. As logs accumulate (daily logins, changes, email sends), the JSON response grows large and the Administration screen slows down.

**Fix:** add `skip`, `limit`, `action`, `actor_id`, `from_date`, `to_date` parameters to `GET /api/settings/audit-logs`, with a sensible default (`limit=100`).

---

## 🟡 Minor improvements

### TEC-141 — User roles hardcoded as string literals in the frontend

**File:** `frontend/src/stores/auth.ts` (lines 17–29) and components

```ts
user.value?.role === 'admin'
user.value?.role === 'tresorier'
user.value?.role === 'secretaire'
```

Role values are repeated verbatim in the store and likely in components (`v-if="isAdmin"`, etc.). A silent typo (e.g. `'Admin'` instead of `'admin'`) would go unnoticed at compile time.

**Fix:** declare a shared constants object or TypeScript enum:
```ts
export const USER_ROLES = { ADMIN: 'admin', TRESORIER: 'tresorier', SECRETAIRE: 'secretaire', READONLY: 'readonly' } as const
```
Use `USER_ROLES.ADMIN` everywhere instead of string literals.

---

### TEC-142 — Systematic `# type: ignore[return-value]` suppressions in routers

**Files:** `backend/routers/invoice.py`, `contact.py`, `payment.py`, etc.

```python
return invoice  # type: ignore[return-value]
return updated  # type: ignore[return-value]
```

These suppressions indicate a type mismatch between SQLAlchemy models (`Invoice`) and the Pydantic `response_model` schemas. They mask potentially legitimate mypy errors.

**Fix:** ensure Pydantic schemas are configured with `model_config = ConfigDict(from_attributes=True)` and use `InvoiceRead.model_validate(invoice)` explicitly, or annotate service function return types correctly so mypy accepts them without suppression.

---

## Notable strengths

- **Solid overall security**: defensive HTTP headers (CSP, HSTS, X-Frame-Options), refresh token in HttpOnly cookie, magic-byte validation on uploads, anti-path-traversal regex on backups.
- **Password lifecycle management**: `must_change_password`, `password_changed_at` (invalidates prior tokens), enforced complexity policy.
- **Exemplary test architecture**: 36 unit files + 30 integration files, clean fixtures (per-test truncation, accelerated bcrypt), 999 tests in 81 seconds.
- **Robust accounting engine**: state machine on invoice statuses, validated transitions, accounting entries generated by configurable rules.
- **Excel import pipeline**: correctly split into 16 sub-modules after TEC-050 refactoring, with an explicit coexistence policy.
- **Backup service**: `sqlite3.backup()` on a thread worker, FIFO rotation, path-traversal protection, clean restart via SIGTERM.
