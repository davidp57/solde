# GitHub Copilot Instructions — Solde ⚖️

## Language rules

- **Code and comments**: English only
- **Communication with the user**: French only
- **UI labels, messages, and user-facing text**: French (i18n-ready — use translation keys, never hardcode strings directly in components)
- **Documentation**:
   - `README.md`: French + English
   - user documentation and installation / how-to guides: French + English
   - new or updated technical and developer documentation: English
   - legacy technical documentation must be migrated to English progressively until alignment is complete
   - `CHANGELOG.md`, release notes, backlog tracking: French
   - Exception: inline code comments stay in English.

---

## Project context

Solde (⚖️) is a web application for managing the accounting of a French loi 1901 non-profit (soutien scolaire). See `doc/plan.md` for the full architecture plan and `doc/roadmap.md` for the implementation roadmap.

**Stack**: FastAPI + SQLite + Vue.js 3 + PrimeVue + Docker (single container, Synology NAS target, ≤ 384 MB RAM)

---

## Development workflow

### Git Flow

This project follows **git flow**:
- `main` — production-ready releases only
- `develop` — integration branch, always deployable
- `feature/*` — new features branched from `develop`
- `fix/*` — bug fixes branched from `develop`
- `hotfix/*` — urgent fixes branched from `main`
- `release/*` — release preparation branched from `develop`

All work happens on feature branches. Never commit directly to `main` or `develop`.

### Branch naming

```
feature/short-description
fix/short-description
hotfix/short-description
release/x.y.z
```

### Commit messages

Follow **Conventional Commits** (`type(scope): description` in English):
- `feat(invoices): add PDF generation for client invoices`
- `fix(payments): correct partial payment status update`
- `chore(deps): upgrade fastapi to 0.115`
- `docs(api): document accounting engine endpoints`
- `test(rules): add unit tests for default accounting rules`
- `refactor(db): extract session factory to database module`

---

## TDD

Always write tests **before** implementing functionality:
1. Write a failing test that describes the expected behaviour
2. Implement the minimum code to make it pass
3. Refactor, keeping tests green

Test coverage targets:
- Business logic services (accounting engine, invoice numbering, fiscal year close): **≥ 90%**
- API endpoints: **≥ 80%**
- Frontend composables: **≥ 70%**

Test files mirror the source structure:
- `backend/services/accounting_engine.py` → `tests/unit/test_accounting_engine.py`
- `backend/routers/invoices.py` → `tests/integration/test_invoices_api.py`

---

## Quality control (pre-push)

Run the following checks **before every push** to avoid CI failures. This is mandatory and applies on every machine.

**Python (backend)** — run from the repo root:
```powershell
ruff check backend/ tests/
ruff format --check backend/ tests/   # fix with: ruff format backend/ tests/
python -m mypy backend/
pytest tests/ -q
```

**Vue.js (frontend)** — run from `frontend/`:
```powershell
npx eslint src/
npx vue-tsc --noEmit
npx vitest run
```

All checks must be green before pushing or opening a PR. Never bypass with `--no-verify` unless there is a documented exceptional reason.

## Multi-PC workflow

This project is developed on two machines. Before starting any work on a branch:
```powershell
git pull --rebase
```
This avoids non-fast-forward push rejections. If a push is rejected, always use `git pull --rebase` (not `git merge`) before retrying.

---

## Documentation maintenance

Keep the following documents up to date with every significant change:

| Document | Langue | Emplacement | Déclencheur |
|---|---|---|---|
| `README.md` | **FR + EN** | root | Chaque release |
| Documentation utilisateur | **FR + EN** | `doc/user/` | Fonctionnalité ajoutée ou modifiée |
| Documentation d'installation / how-to | **FR + EN** | `doc/user/` ou root | Installation, exploitation ou premiers pas modifiés |
| Documentation développeur | **EN** | `doc/dev/` | Architecture ou API modifiée |
| Documentation technique historique | **Migration vers EN** | `doc/` | À traduire progressivement jusqu'à alignement complet |
| `CHANGELOG.md` | **FR** | root | Chaque PR mergée vers `develop` |
| Notes de release | **FR** | `doc/releases/` | Chaque release |
| `doc/backlog.md` | **FR** | `doc/` | Ticket créé, avancé ou complété |
| `doc/roadmap.md` | **EN à terme** | `doc/` | Lot complété, planifié ou repriorisé |
| `doc/plan.md` | **EN à terme** | `doc/` | Décisions d'architecture mises à jour |

`CHANGELOG.md` suit le format **Keep a Changelog** (sections Unreleased → version).

---

## Project planning and delivery workflow

### Development cycle

1. **Analyse and create tickets** — add work items to `doc/backlog.md` (format: `BIZ-NNN` / `TEC-NNN` / `CHR-NNN` depending on category — see backlog legend, priorities P1–P3, dates, estimates, explicit status). Estimates represent **Copilot's own implementation time** (how long the AI agent takes to complete the work), not the user's time.
2. **Feed the roadmap when relevant** — if a ticket represents a new feature, major initiative, innovative idea, or strategic shift, also add it to `doc/roadmap.md` under "Not yet planned".
3. **Group tickets into lots** — related backlog items are bundled into named lots (e.g. *Lot A — Import Excel*, *Lot F — Tests*). Each lot is identified in the backlog.
4. **Assign a target version** — agree on a version (`MAJOR.MINOR`, no patch level) per lot. **Every versioned lot must appear in the roadmap**: functional lots get a subsection with detail, technical lots get a one-line summary.
5. **Implement each lot in git-flow** — one feature branch per lot (or per PR if it makes sense to split), with a PR into `develop`.
6. **Update CHANGELOG continuously** — every merged PR adds its entries under the `[Non publié]` section.
7. **Release** — create release notes (`doc/releases/vX.Y.Z.md`), stamp the version and date in `CHANGELOG.md`, bump version numbers.

### Keeping docs in sync

- `doc/backlog.md` and `doc/roadmap.md` must be **kept up to date at all times**: coherent content, correct dates, accurate statuses and priorities, proper lot grouping, zero markdown formatting errors.
- `CHANGELOG.md` reflects **shipped work**; `doc/backlog.md` reflects **planned and in-progress work** — no item should live in both as active.
- `doc/roadmap.md` contains **every versioned lot** from the backlog. Functional lots are detailed (one subsection per feature); technical lots are kept to a one-line summary.

### Backlog management

`doc/backlog.md` is the shared project backlog and the **single source of truth** for all tracked work items.

**Structure**: the backlog follows a table-first format inspired by batch-driven backlogs:
- **Active lots** — one table per lot with columns `ID | Titre | Prio | Est. | Créé | Démarré | Terminé`.
- **Hors lots** — a single table for open items not yet assigned to a lot.
- **Détails** — a brief (3–5 lines) description per open ticket.
- **Lots terminés** — a summary table of completed lots, with full details in a collapsible `<details>` section.
- **Légende** — priority and status definitions.

**Rules**:
- When the user mentions a point to track, record it in `doc/backlog.md` immediately.
- New tickets go in the "Hors lots" table or directly in an active lot table.
- Track each item with an explicit status and keep that status updated as work progresses.
- When a ticket is completed, move it from the active section to "Lots terminés" / closed details.
- Prefer updating `doc/backlog.md` rather than leaving actionable follow-up items only in the chat conversation.
- Always maintain: correct lot grouping, priority ordering (P1 first), consistent formatting, and accurate completion dates.

### Roadmap management

`doc/roadmap.md` tracks the high-level delivery plan.

- Every lot with an agreed target version appears with its planned `MAJOR.MINOR` version.
- Functional lots get a detailed subsection; technical lots get a one-line summary.
- Update the roadmap after completing a lot, planning new lots, or changing priorities.

### Per-change checklist

After every change (feature, fix, refactor):

1. Update or add tests
2. Run the full quality gate (see **Quality control** section above) — all green
3. Verify zero errors in VS Code
4. Update `CHANGELOG.md` (`[Non publié]` section)
5. Update `doc/backlog.md` if the change closes or advances a ticket

---

## Release process

When asked to create a release, follow these steps **in order**:

1. **Analyse changes** since the last release (git log, CHANGELOG Unreleased section)
2. **Determine the version bump** following Semantic Versioning (semver):
   - `MAJOR` (x.0.0): breaking changes
   - `MINOR` (0.x.0): new features, backward-compatible
   - `PATCH` (0.0.x): bug fixes, backward-compatible
3. **Propose the new version number** and a one-line summary of changes
4. **Ask the user for confirmation** before making any changes
5. Once confirmed:
   - Update `pyproject.toml` (backend version)
   - Update `package.json` (frontend version)
   - Move CHANGELOG `Unreleased` section to the new version with today's date
   - Create French release notes in `doc/releases/vX.Y.Z.md`
   - Commit: `chore(release): bump version to X.Y.Z`
6. **Determine the PR target**:
   - From a `feature/*` or `fix/*` branch → PR into `develop`
   - From `develop` or a `release/*` branch → PR into `main`
7. **Create the PR** with:
   - Title: `release: vX.Y.Z` or descriptive feature title
   - Description in **English**: summary of changes, breaking changes (if any), migration notes (if any)
   - Always provide the PR title and description as **copyable markdown blocks** in the chat, so the user can paste them directly into GitHub

---

## Code conventions

- **Python**: type annotations required on all public functions and methods; Pydantic v2 for schemas; SQLAlchemy 2 async style
- **Vue.js**: Composition API + `<script setup>` syntax; Pinia for state; no Options API
- **SQL**: use Alembic migrations for every schema change; never modify the DB directly
- **Security**: validate all inputs at API boundaries; no secrets in code (use `.env`); parameterised queries only (SQLAlchemy ORM, no raw SQL with string concatenation)
- **Decimal arithmetic**: use Python `Decimal` (not `float`) for all monetary amounts to avoid rounding errors
- **Error handling**: raise typed exceptions in services; handle them in routers; return structured JSON errors

---

## RAM constraint reminder

Target: ≤ 384 MB total on Synology NAS. When adding dependencies or architectural choices:
- Prefer lazy loading and on-demand imports
- Uvicorn: 1 worker only
- WeasyPrint: import at generation time, not at startup
- No in-process caches larger than a few MB
