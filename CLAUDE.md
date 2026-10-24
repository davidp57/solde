# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Source of truth for process & conventions:** [`.github/copilot-instructions.md`](.github/copilot-instructions.md).
> It defines the git-flow rules, release process, backlog/roadmap workflow, documentation matrix, and estimation/calibration protocol in full. This file summarizes the engineering essentials and the architecture that requires reading multiple files to grasp. When the two disagree, copilot-instructions.md wins.

## Language rules (non-negotiable)

- **Code, identifiers, inline comments**: English only.
- **Communication with the user**: French only.
- **UI strings**: French, always via i18n keys (`frontend/src/i18n/fr.ts`) — never hardcode user-facing text in components.
- **Docs**: `README.md` + user/admin docs = FR+EN; new dev/technical docs = EN; `CHANGELOG.md`, release notes, backlog = FR.

## Project context

Solde (⚖️) is the accounting web app for a French *loi 1901* non-profit (soutien scolaire): invoicing, payments, treasury, Excel historical imports, and double-entry bookkeeping. Deployed as a **single Docker container** targeting a Synology NAS with a hard **≤ 384 MB RAM** budget.

**Stack**: FastAPI + SQLAlchemy 2 (async) + SQLite (WAL) + Alembic · Vue 3 (`<script setup>`) + PrimeVue 4 + Pinia + Vue Router + vue-i18n · WeasyPrint for PDF · JWT in HttpOnly cookies.

## Commands

### Run dev environment (Windows)
```powershell
.\dev.ps1   # applies Alembic migrations, starts backend (uvicorn :8000) + frontend (vite :5173); Ctrl+C stops both
```
Auto-login is enabled in dev (`admin` / `admin1234`). API docs at http://localhost:8000/docs.

### Quality gate — run BEFORE every push (mandatory, mirrors CI)
```powershell
# Backend, from repo root:
ruff check backend/ tests/
ruff format --check backend/ tests/      # autofix: ruff format backend/ tests/
python -m mypy backend/
pytest tests/ -q

# Frontend, from frontend/:
npx eslint src/
npx vue-tsc --noEmit
npx vitest run
```
Never bypass hooks with `--no-verify` without a documented reason.

### Targeted tests
```powershell
pytest tests/unit/test_accounting_engine.py -q                       # one file
pytest tests/unit/test_accounting_engine.py::test_name -q            # one test
pytest tests/ -q --cov=backend --cov-report=term-missing             # with coverage
```
Backend tests run async (`asyncio_mode = auto`); fixtures (in-memory DB, ASGI client) live in `tests/conftest.py`.

```powershell
cd frontend && npx vitest run src/tests/some.spec.ts                 # one frontend file
```

### Migrations
```powershell
python -m alembic revision --autogenerate -m "short description"
python -m alembic upgrade head
```
Every schema change goes through Alembic — never alter the DB directly. Naming: `NNNN_short_description.py` (zero-padded sequence).

## Architecture

### Single-container model
Vue is built at image-build time; FastAPI serves the static `frontend/dist/` (with SPA fallback) under `/*` and the API under `/api/**`. No separate reverse proxy. One Uvicorn worker. `data/` is the mounted volume (`solde.db` + WAL, `pdfs/`, `uploads/`, `logs/`, `backups/`).

### Strict backend layering (`backend/`)
```
Router (routers/)  → HTTP parse, auth dependency, maps typed exceptions → HTTPException. NO business logic.
Service (services/)→ all business logic & DB writes. Receives a session. NEVER imports from routers.
Model (models/)    → SQLAlchemy ORM, one file per table.
database.py        → async engine, WAL pragma, get_db().
```
One router file + one service area per business domain (invoice, payment, bank, cash, accounting, salary, contact, backup, excel_import…). Unhandled exceptions are caught by `UnhandledExceptionMiddleware` in `main.py` → generic JSON `500 {detail, code}`. `main.py` also wires `create_app()`, lifespan, security headers, CORS, and StaticFiles.

### Frontend (`frontend/src/`)
`api/` (axios calls + TS types, JWT 401-refresh interceptor) · `stores/` (Pinia) · `composables/` · `views/` (one per route) · `router/` (role-based guards, lazy loading) · `i18n/fr.ts` (all strings).

### Roles & areas
Technical roles: `readonly`, `secretaire` (Manager), `tresorier` (Accountant), `admin`. Authorization enforced at the router level via FastAPI dependencies. Areas: **Management** (secretaire+), **Accounting** (tresorier+), **Administration** (admin only).

### Domain gotchas (read [`docs/dev/architecture.md`](docs/dev/architecture.md) before touching these)
- **`Decimal` for all money** — never `float`.
- **Bank category `no_entry`** is a *phantom* category, intentionally exempt from accounting-rule processing, enforced at engine level, by `TriggerType` having no such value, and by `NON_TRIGGERABLE_CATEGORIES` in `backend/models/accounting_rule.py`. Never add it to `_BANK_CATEGORY_TRIGGER`.
- **AccountingEntry `group_key`**: `group_key` col → else `"{source_type}:{source_id}"` → else `"entry:{id}"`. Used for journal clustering, import-state diff, dedup.
- **Backups**: always copy `solde.db`, `solde.db-wal`, `solde.db-shm` together (WAL mode).
- The accounting engine (`services/accounting_engine.py`) and Excel import (`services/excel_import/`, `import_reversible.py`) are the most complex subsystems.

## Code conventions

- **Python**: type annotations on all public functions; Pydantic v2 schemas; SQLAlchemy 2 async style. `backend.services.*` is type-checked **strict** by mypy — keep it fully typed. Ruff line length 100, rules `E,F,I,UP,B,SIM`.
- **Vue**: Composition API + `<script setup>` only (no Options API); Pinia for state.
- **Security**: validate inputs at API boundaries; uploads checked by magic bytes not just Content-Type; parameterized queries only; secrets via `.env`.
- **RAM budget**: prefer lazy/on-demand imports (WeasyPrint imported at generation time, not startup); 1 Uvicorn worker; no large in-process caches.

## TDD & coverage targets

Write the failing test first. Targets: business-logic services **≥ 90%**, API endpoints **≥ 80%**, frontend composables **≥ 70%**. Tests mirror source layout (`backend/services/x.py` → `tests/unit/test_x.py`; `backend/routers/x.py` → `tests/integration/test_x_api.py`).

## Git flow (summary — see copilot-instructions.md for the full rules)

`main` (prod) ← `develop` (integration) ← `feature/*` / `fix/*`. Hotfixes from `main`. **Releases only on `release/x.y.z` branches.** Never commit directly to `main`/`develop` (except acceptance-testing *recette* fixes and **documentation-only edits** — see Documentation hygiene — which go straight to `develop`). Conventional Commits in English (`type(scope): description`). Multi-PC project: `git pull --rebase` before starting, and on any rejected push.

## Default action workflow (standing authorization)

For every non-trivial change, unless told otherwise, proceed end-to-end without waiting for intermediate go-aheads:

0. **Sync first (mandatory)** — before reading the backlog or starting any work, `git fetch` then bring the branch up to date (`git pull --ff-only` on `develop`, or rebase the working branch onto latest `origin/develop`). Never reason about "what's left to do" from a stale checkout.
1. **Analyse** scope and impacted files. If the request is exploratory (question/analysis, no code change), stop here.
2. **Branch** from `develop` (`feature/<id>` or `fix/<id>`). One branch + one PR per lot, not per ticket, unless asked.
3. **Implement** with tests (TDD) and the docs/CHANGELOG/backlog updates from the per-change checklist.
4. **Quality gate green** (backend + frontend, mirrors CI) before pushing.
5. **If the user must test manually**, stop and wait for explicit approval ("c'est bon" / "go") before continuing; otherwise proceed.
6. **Commit + push** (Conventional Commits in English, with the required `Co-Authored-By` trailer).
7. **Open the PR** targeting `develop` and report its URL.
8. **Merge it into `develop` once CI is green** — every required check passing, no conflict. Report the merge. A red or pending check is not a merge: wait, or say what is blocking.

This grants standing authorization to **commit, push, open PRs, and merge them into `develop` when CI is green** without asking each time. It does **not** authorize **merging into `main`**, force-push, or pushing tags — those stay with the user (merges to `main` are always manual; `release/x.y.z` branches target `main`).

## Working rules (surgical mode)

- **Surgical changes**: never modify adjacent code, comments, or formatting unrelated to the request; do not refactor working code unless that *is* the task.
- **Minimalism**: produce the minimum needed to solve the request; no speculative features or abstractions.
- **Zero assumptions**: if an instruction is ambiguous or contradictory, stop and ask before coding.

## Documentation hygiene

Keep the backlog reflecting real status. The backlog is a **per-lot `.backlog/` directory** (see Agent skills below): active lots are directories `.backlog/<LOT-ID>/` (`PRD.md` + `tickets/NN-slug.md`); completed lots are compacted into `.backlog/archive/<LOT-ID>.md` once closed > 3 days. The lot index is `.backlog/README.md`. `docs/roadmap.md` remains the source of truth for **sequencing**; `.backlog/` is the source of truth for **scope + status**. One branch + one PR per lot.

**Documentation-only commits go straight to `develop`** — a commit whose diff touches **only** documentation (Markdown / `docs/**` / `.backlog/**`, plus root docs like `CHANGELOG.md`, `README.md`, `CLAUDE.md`) needs **no branch or PR**: backlog, roadmap, plan, dev/user docs, release notes, changelog. As soon as a commit also touches **code, tests, config, or any non-documentation file**, the exception no longer applies and it follows the normal feature/fix branch + PR flow. Releases keep their dedicated `release/x.y.z` flow regardless.

## Agent skills

The Matt Pocock engineering skills (`/to-prd`, `/to-issues`, `/triage`) are configured per repo (no fork). They read three config files:

- **Issue tracker** — lots/PRDs/tickets live under `.backlog/<LOT-ID>/` (active) and `.backlog/archive/<LOT-ID>.md` (completed). `/to-prd` writes `PRD.md` + adds a row to `.backlog/README.md`; `/to-issues` writes `tickets/NN-slug.md`. See [`docs/agents/issue-tracker.md`](docs/agents/issue-tracker.md).
- **Triage labels** — single `Status:` vocabulary (⬜ ready · 🔄 in-progress · 🧑 waiting-human · ✅ done · 🚫 wontfix), mapped to Matt's triage roles. Artifacts are created at ⬜ ready. See [`docs/agents/triage-labels.md`](docs/agents/triage-labels.md).
- **Domain docs** — single-context repo; glossary and prior decisions. See [`docs/agents/domain.md`](docs/agents/domain.md).

Ticket IDs keep the project taxonomy (`BIZ-NNN` / `TEC-NNN` / `CHR-NNN`); the `NN-` file prefix is only for dependency ordering inside a lot.

## Per-change checklist

After each change: update/add tests → full quality gate green → update `CHANGELOG.md` (`[Non publié]`) → if user-visible, update `docs/user/changelog-user.md` → update the lot's `.backlog/<LOT-ID>/` (ticket status, PRD) if a ticket advances → bump patch version in `pyproject.toml` **and** `frontend/package.json`.
