# Contributing to Solde

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.11+ | |
| Node.js | 20+ (22 recommended) | Matches the Docker build image |
| npm | bundled with Node.js | |
| Docker + Docker Compose | recent stable | Optional — backend integration tests run without Docker (in-memory ASGI + SQLite) |
| PowerShell | any recent version | Windows only; `dev.ps1` script |

---

## Local setup

### 1. Clone and set up the backend

```powershell
git clone git@github.com:davidp57/solde.git
cd solde
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS
pip install -e ".[dev]"
Copy-Item .env.example .env     # Windows
# cp .env.example .env          # Linux / macOS
alembic upgrade head
```

Edit `.env` and set at minimum `JWT_SECRET_KEY` to a random string of 32+ characters.

### 2. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 3. Start both dev servers

On Windows with PowerShell:

```powershell
./dev.ps1
```

This starts the FastAPI backend on `http://localhost:8000` and the Vite frontend on `http://localhost:5173`. It installs `node_modules` if missing and stops both processes on `Ctrl+C`.

Manual equivalent:

```powershell
# Terminal 1 — backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```

Useful URLs in dev mode:

- Application (hot-reload): `http://localhost:5173`
- API + static app: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/api/docs` (requires `DEBUG=true` in `.env`)

---

## Git workflow — Git Flow

This project follows [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/).

| Branch | Purpose |
|---|---|
| `main` | Production-ready releases only |
| `develop` | Integration branch, always deployable |
| `feature/*` | New features, branched from `develop` |
| `fix/*` | Bug fixes, branched from `develop` |
| `hotfix/*` | Urgent fixes, branched from `main` |
| `release/*` | Release preparation, branched from `develop` |

**Never commit directly to `main` or `develop`.**

### Creating a feature branch

```bash
git checkout develop
git pull --rebase
git checkout -b feature/my-feature-description
```

### Multi-PC sync

Always rebase before starting work on a branch that may have been pushed from another machine:

```bash
git pull --rebase
```

Never use `git merge` to catch up — use `--rebase` to avoid non-fast-forward push rejections.

---

## Commit messages — Conventional Commits

Format: `type(scope): description` (English, imperative mood, lowercase)

| Type | Use |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `chore` | Build, config, tooling, no production code change |
| `docs` | Documentation only |
| `test` | Tests only |
| `refactor` | Code change with no feature or bug change |
| `perf` | Performance improvement |

Examples:

```
feat(invoices): add configurable number templates
fix(pdf): remove duplicate SIRET from sender block
chore(deps): upgrade fastapi to 0.115
docs(admin): add Synology Portainer deployment guide
test(accounting): add journal pagination integration tests
refactor(import): split excel_import.py into domain modules
```

---

## Quality gate — mandatory before every push

All checks must be green. Never bypass with `--no-verify` without a documented exceptional reason.

### Backend (run from repo root)

```powershell
ruff check backend/ tests/
ruff format --check backend/ tests/    # fix: ruff format backend/ tests/
python -m mypy backend/
pytest tests/ -q
```

### Frontend (run from `frontend/`)

```powershell
npx eslint src/
npx vue-tsc --noEmit
npx vitest run
```

### Fix formatting automatically

```powershell
ruff format backend/ tests/            # Python formatting
cd frontend && npx eslint src/ --fix   # JS/TS auto-fix
```

---

## Pull request process

1. Make sure the quality gate is fully green locally.
2. Push your branch and open a PR against `develop`.
3. PR title follows the same Conventional Commits format.
4. PR description in **English**: summary of changes, breaking changes if any, migration notes if any.
5. Update `CHANGELOG.md` under `[Non publié]` with the relevant entries.
6. Update `doc/backlog.md` to mark the ticket as completed.
7. Bump the patch version in `pyproject.toml` and `frontend/package.json`.

---

## Code conventions

### Python

- Type annotations required on all public functions and methods.
- Pydantic v2 for all input/output schemas.
- SQLAlchemy 2 async style (`async with session` / `await session.execute(...)`).
- `Decimal` (not `float`) for all monetary amounts.
- Raise typed exceptions in services; catch and map in routers.
- No raw SQL with string concatenation — ORM queries or parameterized text only.
- No secrets in code; use `.env` loaded via `Settings`.

### Vue.js / TypeScript

- Composition API with `<script setup>` syntax only. No Options API.
- Pinia for all shared state.
- All user-facing strings go through `vue-i18n` (`t('key')`). Never hardcode French strings in templates.
- Components stay under ~500 lines. Extract sub-components and composables beyond that.
- Route-level components use lazy imports (`() => import('./views/...')`).

### SQL / Alembic

- Every schema change gets its own Alembic migration.
- Naming: `NNNN_short_description.py`.
- Never run `create_all()` or DDL outside migrations.

---

## Adding a new feature — checklist

- [ ] Write the failing test first (TDD)
- [ ] Implement the minimum code to make it pass
- [ ] Add Alembic migration if the schema changes
- [ ] Add or update i18n keys in `frontend/src/i18n/fr.ts`
- [ ] Run the full quality gate
- [ ] Update `CHANGELOG.md`
- [ ] Update `doc/backlog.md`
- [ ] Bump patch version

---

## Environment variables reference

See [../admin/configuration.md](../admin/configuration.md) for the full variable reference.

For local development, the minimum `.env` looks like:

```bash
JWT_SECRET_KEY=dev-only-change-me-at-least-32-chars
DEBUG=true
```

With `DEBUG=true`, Swagger UI is available at `/api/docs` and detailed error messages are returned by the API.
