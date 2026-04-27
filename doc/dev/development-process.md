# Development Process — Solde ⚖️

## Branching and versioning

This project uses **Git Flow** and **Semantic Versioning** (semver).

- `main` — tagged production releases
- `develop` — integration branch, always deployable
- `feature/*` / `fix/*` — work branches off `develop`
- `hotfix/*` — urgent fix branches off `main`
- `release/*` — release preparation branches off `develop`

Version numbers follow `MAJOR.MINOR.PATCH`:
- `MAJOR`: breaking change
- `MINOR`: backward-compatible new feature
- `PATCH`: backward-compatible bug fix

The version is defined in **two places** (kept in sync manually):
- `pyproject.toml` — `version = "x.y.z"`
- `frontend/package.json` — `"version": "x.y.z"`

The backend reads the version at runtime via `importlib.metadata.version("solde")` and exposes it at `GET /api/health`.

---

## Development cycle

### 1. Pick a ticket

Consult `doc/backlog.md`. Pick a ticket from the active lots or the "Hors lots" section. Mark it as started (add a `Démarré` date).

### 2. Branch

```bash
git checkout develop
git pull --rebase
git checkout -b feature/short-description
```

Use `fix/` for bugs and `feature/` for everything else.

### 3. Develop (TDD)

- Write the failing test first.
- Implement the minimum code to make it pass.
- Refactor while keeping tests green.
- See [testing.md](./testing.md) for patterns and conventions.

### 4. Quality gate

Before every push, run the full gate:

```powershell
# Backend (repo root)
ruff check backend/ tests/
ruff format --check backend/ tests/
python -m mypy backend/
pytest tests/ -q

# Frontend
cd frontend
npx eslint src/
npx vue-tsc --noEmit
npx vitest run
```

All checks must be green. Fix everything before pushing.

### 5. Update documentation

- `CHANGELOG.md` — add entries under `[Non publié]`
- `doc/backlog.md` — mark ticket as completed, add `Terminé` date
- Bump `version` in `pyproject.toml` and `frontend/package.json` (patch increment)

### 6. Push and open PR

```bash
git push -u origin feature/short-description
```

Open a PR against `develop`. Title and description in English, following Conventional Commits format.

---

## Backlog management

`doc/backlog.md` is the single source of truth for all tracked work items.

- Add new tickets immediately when a task is identified.
- Use prefixes: `BIZ-NNN` (business feature), `TEC-NNN` (technical), `CHR-NNN` (chore).
- Group related tickets into named lots with a target version.
- Move completed tickets to the "Lots terminés" section with a completion date.

---

## Release process

When asked to create a release:

1. Analyse changes since the last release (git log, `CHANGELOG.md` `[Non publié]` section).
2. Determine the version bump (major / minor / patch).
3. Update `pyproject.toml` and `frontend/package.json` with the new version.
4. Move the `[Non publié]` section in `CHANGELOG.md` to a new versioned section `[x.y.z] — YYYY-MM-DD`.
5. Create French release notes in `doc/releases/vX.Y.Z.md`.
6. Commit: `chore(release): bump version to X.Y.Z`.
7. Open a PR from the release branch into `main` (or directly from `develop` if on a minor).
8. After merge, tag `main`: `git tag vX.Y.Z`.
9. Push the tag to trigger the GHCR image build: `git push origin vX.Y.Z`.

### Release notes template (`doc/releases/vX.Y.Z.md`)

```markdown
# Notes de version — vX.Y.Z

**Date** : YYYY-MM-DD

## Résumé

One-paragraph summary in French.

## Nouveautés

- ...

## Corrections

- ...

## Technique

- ...

## Mise à jour

See [../admin/administration.md](../admin/administration.md) for the upgrade procedure.
```

---

## CI/CD pipeline

GitHub Actions runs the full quality gate on every push and PR:

```
push / PR
    │
    ├── Python linting (ruff)
    ├── Python type check (mypy)
    ├── Backend tests (pytest)
    ├── Frontend type check (vue-tsc)
    ├── Frontend linting (eslint)
    └── Frontend tests (vitest)
```

Docker images are built and published to `ghcr.io/davidp57/solde` on every push to `main` (tagged `latest`) and on every version tag (`vX.Y.Z`).

---

## Working on two machines

Development happens on multiple machines. Standard sync procedure before starting work:

```bash
git fetch --all
git checkout develop
git pull --rebase
git checkout feature/my-branch
git pull --rebase
```

Always `--rebase`, never `--merge`, to keep a linear history on feature branches.

If a push is rejected:

```bash
git pull --rebase
git push
```

---

## Import coexistence policy (reference)

When `Gestion` and `Comptabilite` imports coexist with manually created objects:

- A file already imported with the same hash is rejected (idempotence safeguard).
- Exact duplicate business objects are silently ignored.
- Exact duplicate accounting lines are silently ignored.
- Ambiguous matches (multiple candidates) block the import — never resolved arbitrarily.
- `MANUAL` accounting entries are allowed to coexist with imported ones as long as there is no exact duplicate.

Editing rules for validated objects:
- `draft` invoices: freely editable.
- `sent` unpaid invoices: editable; auto-generated accounting entries are deleted and regenerated in the same transaction.
- `paid`, `partial`, `overdue`, `disputed` invoices: no direct editing.
- Payments: immutable after creation except for `reference`, `notes`, and `cheque_number`.
- Reversible import `undo/redo`: blocked if any imported object was subsequently modified through the standard API.
