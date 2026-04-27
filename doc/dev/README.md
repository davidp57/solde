# Developer Documentation — Solde ⚖️

This directory contains all technical documentation for contributors and developers working on Solde.

## Contents

| File | Description |
|---|---|
| [architecture.md](./architecture.md) | Stack, project structure, data model, key design decisions |
| [contributing.md](./contributing.md) | Local setup, Git workflow, commit conventions, pull request process |
| [testing.md](./testing.md) | Test strategy, backend (pytest) and frontend (Vitest), coverage targets, TDD |
| [development-process.md](./development-process.md) | Quality gates, CI, release process, versioning, branch model |

## Quick start

```powershell
# Clone and set up
git clone git@github.com:davidp57/solde.git
cd solde
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
Copy-Item .env.example .env
alembic upgrade head

# Start dev servers (Windows)
./dev.ps1
```

See [contributing.md](./contributing.md) for the full setup guide.
