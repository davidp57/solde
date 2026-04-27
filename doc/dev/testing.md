# Testing — Solde ⚖️

## Philosophy — TDD

All new functionality follows Test-Driven Development:

1. Write a failing test that describes the expected behaviour.
2. Implement the minimum code to make it pass.
3. Refactor while keeping tests green.

Tests are not optional. A PR that adds a feature without tests will not be merged.

---

## Coverage targets

| Scope | Target |
|---|---|
| Business logic services (accounting engine, invoice numbering, fiscal year close) | ≥ 90% |
| API endpoints | ≥ 80% |
| Frontend composables | ≥ 70% |

---

## Backend tests — pytest

### Stack

- **pytest** with `pytest-asyncio` for async tests
- **httpx** `AsyncClient` pointed at the ASGI app (no real HTTP server)
- **In-memory SQLite** for isolation (each test module gets its own DB)
- Fixtures defined in `tests/conftest.py`

### Directory structure

Test files mirror the source tree:

| Source | Test file |
|---|---|
| `backend/services/accounting_engine.py` | `tests/unit/test_accounting_engine.py` |
| `backend/routers/invoices.py` | `tests/integration/test_invoices_api.py` |
| `backend/services/email_service.py` | `tests/unit/test_email_service.py` |

- `tests/unit/` — pure service/utility tests, no HTTP
- `tests/integration/` — full ASGI stack tests via `AsyncClient`

### Running tests

```powershell
# All tests
pytest tests/ -q

# With coverage report
pytest tests/ --cov=backend --cov-report=term-missing -q

# Single file
pytest tests/unit/test_accounting_engine.py -v

# Single test
pytest tests/unit/test_accounting_engine.py::test_balance_calculation -v
```

### Key fixtures (`tests/conftest.py`)

| Fixture | Scope | Purpose |
|---|---|---|
| `engine` | module | In-memory async SQLite engine with all migrations applied |
| `db` | function | Fresh async session per test |
| `client` | function | `AsyncClient` against the ASGI app with the test DB injected |
| `admin_token` | function | JWT for an admin user |
| `manager_token` | function | JWT for a `secretaire` (Manager) user |

### Writing a backend unit test

```python
import pytest
from decimal import Decimal
from backend.services.accounting_engine import compute_balance

@pytest.mark.asyncio
async def test_balance_is_zero_on_empty_db(db):
    result = await compute_balance(db, account_code="512000")
    assert result == Decimal("0")
```

### Writing an integration test

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_contact_requires_auth(client: AsyncClient):
    response = await client.post("/api/contacts", json={"nom": "Test"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_contact_as_admin(client: AsyncClient, admin_token: str):
    response = await client.post(
        "/api/contacts",
        json={"nom": "Dupont", "prenom": "Jean"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    assert response.json()["nom"] == "Dupont"
```

---

## Frontend tests — Vitest

### Stack

- **Vitest** with `jsdom` environment
- **@vue/test-utils** for component mounting
- **Pinia** testing utilities for store isolation

### Directory structure

```
frontend/src/
├── composables/
│   └── __tests__/           # Composable unit tests
└── tests/
    ├── views/               # View/component tests
    └── setup.ts             # Global test setup (i18n, PrimeVue stubs)
```

### Running tests

```bash
cd frontend

# Run all tests
npx vitest run

# Watch mode (dev)
npx vitest

# Coverage
npx vitest run --coverage
```

### Writing a composable test

```typescript
import { describe, it, expect } from 'vitest'
import { useInvoiceMetrics } from '@/composables/useInvoiceMetrics'

describe('useInvoiceMetrics', () => {
  it('returns zero remaining for a paid invoice', () => {
    const invoice = { total_amount: '100', paid_amount: '100', status: 'paid' }
    const { remainingForInvoice } = useInvoiceMetrics()
    expect(remainingForInvoice(invoice)).toBe(0)
  })
})
```

---

## End-to-end tests — Playwright

A single smoke E2E test verifies the full Docker stack (login, dashboard, basic navigation).

```bash
cd frontend
npx playwright test
```

The Playwright test requires the application to be running on `http://localhost:8000`. Use `dev.ps1` or `docker compose up` before running it.

---

## Mocking external dependencies

### WeasyPrint (PDF generation)

WeasyPrint requires native GTK libraries. In tests, mock it via `sys.modules` injection:

```python
import sys
from unittest.mock import MagicMock

sys.modules["weasyprint"] = MagicMock()
sys.modules["weasyprint.HTML"] = MagicMock()
```

See `tests/unit/test_pdf_service.py` for the full pattern.

### SMTP (email sending)

Use `unittest.mock.patch` to mock `smtplib.SMTP` and `smtplib.SMTP_SSL`:

```python
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_send_invoice_email(client, admin_token):
    with patch("smtplib.SMTP") as mock_smtp:
        mock_instance = MagicMock()
        mock_smtp.return_value.__enter__ = lambda s: mock_instance
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
        # ... test body
```

---

## CI — GitHub Actions

Tests run automatically on every push and pull request via `.github/workflows/`.

The CI pipeline runs:
1. `ruff check` + `ruff format --check` (Python linting/formatting)
2. `mypy` (Python type checking)
3. `pytest` with coverage
4. `vue-tsc --noEmit` (TypeScript type checking)
5. `eslint` (JavaScript/TypeScript linting)
6. `vitest run` (frontend unit tests)

A red CI blocks merge. Fix all issues locally before pushing.
