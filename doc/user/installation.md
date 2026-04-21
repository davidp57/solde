# Installation / Installation

## Français

### Objectif

Ce guide explique comment installer Solde pour une première utilisation, soit avec Docker, soit pour un démarrage local orienté développement ou test.

### Installation avec Docker

Prérequis : Docker et Docker Compose.

```bash
git clone git@github.com:davidp57/solde.git
cd solde
```

Créer le fichier d'environnement :

```powershell
Copy-Item .env.example .env
```

```bash
cp .env.example .env
```

Renseigner au minimum `JWT_SECRET_KEY`. Si vous voulez éviter les identifiants bootstrap par défaut, renseignez aussi `ADMIN_USERNAME`, `ADMIN_PASSWORD` et `ADMIN_EMAIL`.

Lancer l'application :

```bash
docker compose up -d --build
```

Accès utiles :

- application : `http://localhost:8000`
- documentation API : `http://localhost:8000/api/docs`

Au premier démarrage, Solde applique les migrations puis crée un compte administrateur s'il n'existe encore aucun utilisateur.

### Démarrage local

Prérequis : Python `3.11+` et Node.js `20+`.

Backend :

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
Copy-Item .env.example .env
alembic upgrade head
uvicorn backend.main:app --reload --port 8000
```

Frontend :

```bash
cd frontend
npm install
npm run dev
```

Sous Windows, `./dev.ps1` permet de lancer backend et frontend dans la même session.

### Aller plus loin

- Exploitation technique Docker : [../dev/exploitation.md](../dev/exploitation.md)
- Documentation utilisateur : [README.md](README.md)

## English

### Purpose

This guide explains how to install Solde for a first use, either with Docker or with a local setup for development and testing.

### Docker installation

Prerequisite: Docker and Docker Compose.

```bash
git clone git@github.com:davidp57/solde.git
cd solde
```

Create the environment file:

```powershell
Copy-Item .env.example .env
```

```bash
cp .env.example .env
```

Set at least `JWT_SECRET_KEY`. If you do not want to rely on the default bootstrap credentials, also set `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and `ADMIN_EMAIL`.

Start the application:

```bash
docker compose up -d --build
```

Useful URLs:

- application: `http://localhost:8000`
- API docs: `http://localhost:8000/api/docs`

On the first startup, Solde runs migrations and creates a bootstrap administrator if the database does not contain any user yet.

### Local startup

Prerequisites: Python `3.11+` and Node.js `20+`.

Backend:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
Copy-Item .env.example .env
alembic upgrade head
uvicorn backend.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

On Windows, `./dev.ps1` starts backend and frontend in the same session.

### Next steps

- Docker runtime and operations: [../dev/exploitation.md](../dev/exploitation.md)
- User documentation: [README.md](README.md)