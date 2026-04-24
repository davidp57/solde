# Contributing to Solde

## Purpose

This guide centralizes local setup, quality commands, and contribution conventions for the repository.
It complements `README.md`, which is intentionally kept short and acts as a bilingual entry point.

## Stack and prerequisites

### Tooling

- Python `3.11+`
- Node.js `20+` (`22` recommended to match the Docker image)
- npm
- Docker if you also want to reproduce the containerized runtime
- PowerShell on Windows if you want to use `dev.ps1`

### Main technologies

- backend: FastAPI, async SQLAlchemy, Alembic, Pydantic v2, SQLite
- frontend: Vue 3, Vite, TypeScript, PrimeVue, Pinia
- tests: pytest on the backend, Vitest on the frontend

## Local setup

### 1. Clone the repository and prepare the backend environment

```powershell
git clone git@github.com:davidp57/solde.git
cd solde
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
Copy-Item .env.example .env
alembic upgrade head
```

On Linux or macOS, adapt the virtual environment activation and the `.env` copy step.

### 2. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 3. Run the application locally

The easiest option on Windows is:

```powershell
./dev.ps1
```

This script:

- starts backend and frontend in the same terminal session;
- installs `frontend/node_modules` if needed;
- stops both processes with `Ctrl+C`.

Manual option:

```powershell
uvicorn backend.main:app --reload --port 8000
```

```bash
cd frontend
npm run dev
```

Useful URLs:

- Vite frontend: `http://localhost:5173`
- FastAPI-served app when the frontend is built: `http://localhost:8000`
- API docs: `http://localhost:8000/api/docs` (requires `SWAGGER_ENABLED=true` or `DEBUG=true` in `.env`)

## Quality commands

These commands reflect the current repository expectations before opening a pull request.

### Backend

Run from the repository root:

```bash
ruff check backend/ tests/
ruff format --check backend/ tests/   # fix with: ruff format backend/ tests/
python -m mypy backend/
pytest tests/ -q
```

### Frontend

Run from the `frontend/` directory:

```bash
npx eslint src/
npx vue-tsc --noEmit
npx vitest run
```

### Practical guidance

- activate the Python virtual environment before backend commands;
- run the full matrix before a PR, even if your change is scoped to a subset of files;
- for fast iteration, start with focused checks and then replay the full matrix before the final commit;
- on a multi-machine setup, always run `git pull --rebase` before starting work on a branch to avoid push rejections.

## Repository structure

- `backend/`: API, schemas, services, models, migrations
- `frontend/`: Vue.js application
- `tests/`: backend pytest suite
- `doc/`: project, technical, and user documentation
- `data/`: local or Docker-mounted persisted data

## Development conventions

### Languages

- code, symbol names, comments, and docstrings: English
- user-facing UI text: French through i18n keys
- communication with the user in agent sessions: French
- documentation policy:
	- `README.md`: French + English
	- user documentation and installation guides: French + English
	- technical and developer documentation: English
	- backlog, changelog, release notes: French

### Backend

- type annotations are required on public functions and methods;
- use Pydantic v2 for input/output schemas;
- use SQLAlchemy 2 async style;
- use Alembic migrations for every schema change;
- use `Decimal` for monetary amounts;
- raise typed exceptions in services and convert them to HTTP responses in routers.

### Frontend

- Vue 3 Composition API with `script setup`
- Pinia for shared state
- no Options API
- no hardcoded user-facing strings in components; use i18n keys instead

### Documentation and backlog

- `doc/backlog.md` is the source of truth for tracked follow-up items outside the roadmap;
- if a tracked item starts on a branch, update its status and dates in the backlog;
- update the impacted docs in the same branch whenever a significant change is delivered.

## Git workflow

The project follows a git-flow-style workflow:

- `main`: production-ready releases only
- `develop`: integration branch
- working branches must be created from `develop`

Preferred branch prefixes:

- `feature/*` for features
- `fix/*` for bug fixes
- `hotfix/*` for production urgencies
- `release/*` for release preparation

For documentation-only work, use an explicit branch name while still branching from `develop`.

### Commit messages

Use Conventional Commits in English:

- `feat(import): add reversible run history`
- `fix(settings): return 404 for unknown fiscal year`
- `docs(readme): clarify Docker operations`

## Pull request expectations

Before opening a PR:

1. resync your branch with `develop` if needed;
2. update the backlog if the work is tracked in `doc/backlog.md`;
3. update `README.md`, technical docs, user docs, or `CHANGELOG.md` when the change justifies it;
4. run the relevant quality matrix;
5. prepare a concise English PR description with summary, key changes, and checks performed.

## TDD and expected quality level

The repository aims for a TDD workflow:

1. write or adjust a test describing the expected behavior;
2. implement the minimum change to make it pass;
3. refactor while keeping tests green.

Coverage targets referenced by the repository instructions:

- backend business services: `>= 90 %`
- API endpoints: `>= 80 %`
- frontend composables: `>= 70 %`

## Useful docs to revisit depending on the task

- `README.md` for the project entry point
- `doc/dev/docker-operations.md` for Docker runtime and persisted data
- `doc/plan.md` for the architecture target
- `doc/roadmap.md` for delivery sequencing
- `doc/user/` for user-facing behavior and workflows