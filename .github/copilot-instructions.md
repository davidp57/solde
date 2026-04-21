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

## Quality control (pre-commit)

The following checks must pass before every commit. Configure them as pre-commit hooks:

**Python (backend)**:
```bash
ruff check .          # linting + import sorting
ruff format --check . # formatting
mypy .                # type checking (strict mode for services/)
pytest tests/         # full test suite
```

**Vue.js (frontend)**:
```bash
eslint src/           # linting
prettier --check src/ # formatting
vitest run            # unit tests
```

All checks must be green before opening a PR. Never bypass with `--no-verify` unless there is a documented exceptional reason.

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
| `doc/roadmap.md` | **EN à terme** | `doc/` | Après chaque fin de phase |
| `doc/plan.md` | **EN à terme** | `doc/` | Décisions d'architecture mises à jour |

`CHANGELOG.md` suit le format **Keep a Changelog** (sections Unreleased → version).

---

## Backlog management

`doc/backlog.md` is the shared project backlog and the source of truth for tracked follow-up items outside the initial roadmap.

- When the user mentions a point to track (bug, improvement, UX feedback, documentation need, technical debt, open question, process item), record it in `doc/backlog.md` with a short and concrete description.
- Track each item with an explicit status and keep that status updated as the work progresses (`Bac d'entrée`, `Prêt`, `En cours`, `Fait`).
- Prefer updating `doc/backlog.md` rather than leaving actionable follow-up items only in the chat conversation.

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
