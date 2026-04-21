# Solde ⚖️

Solde est une application web de gestion comptable pour une association loi 1901 de soutien scolaire.
Elle remplace une gestion fragmentée dans Excel par une application unique couvrant la facturation, les paiements, la trésorerie, les imports de reprise et la comptabilité en partie double.

## Ce que couvre l'application

- factures clients et fournisseurs, génération PDF et envoi par e-mail ;
- paiements clients, caisse, remises en banque et rapprochement bancaire ;
- imports historiques `Gestion` / `Comptabilite`, preview, historique réversible et reset sélectif ;
- comptabilité en partie double avec plan comptable, règles, journal, balance, grand livre, résultat et bilan ;
- gestion multi-utilisateurs avec rôles, profil utilisateur et administration des comptes.

## Pile technique

- backend : FastAPI, SQLAlchemy async, SQLite, Alembic, Pydantic v2 ;
- frontend : Vue 3, Vite, TypeScript, PrimeVue, Pinia ;
- déploiement : image Docker unique servant l'API et le frontend compilé ;
- stockage persistant : volume `data/` contenant base SQLite, pièces jointes, PDFs et logs.

## Démarrage rapide avec Docker

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

Configurer au minimum `JWT_SECRET_KEY`. Si tu veux éviter les valeurs de bootstrap par défaut, renseigne aussi `ADMIN_USERNAME`, `ADMIN_PASSWORD` et `ADMIN_EMAIL`.

Lancer l'application :

```bash
docker compose up -d --build
```

Puis ouvrir :

- application : `http://localhost:8000`
- documentation API : `http://localhost:8000/api/docs`

Au premier démarrage, Solde applique automatiquement les migrations Alembic puis crée un compte administrateur s'il n'existe encore aucun utilisateur.

## Démarrage rapide en local

Prérequis : Python 3.11+ et Node.js 20+ (`22` recommandé pour coller à l'image Docker).

### Backend

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
Copy-Item .env.example .env
alembic upgrade head
uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Raccourci Windows

Sur Windows, `./dev.ps1` démarre le backend et le frontend dans la même session PowerShell et arrête les deux avec `Ctrl+C`.

## Documentation

- [Installation, configuration et exploitation Docker](doc/dev/exploitation.md)
- [Guide de contribution et développement local](doc/dev/contribuer.md)
- [Architecture technique](doc/architecture.md)
- [Plan complet du projet](doc/plan.md)
- [Roadmap et état d'avancement](doc/roadmap.md)
- [Documentation utilisateur](doc/user/README.md)
- [Changelog](CHANGELOG.md)

## Structure du dépôt

```text
solde/
├── backend/        # API FastAPI, services métier, modèles SQLAlchemy, migrations
├── frontend/       # application Vue.js 3 / Vite / TypeScript
├── tests/          # tests backend pytest
├── data/           # base SQLite, uploads, PDFs, logs et autres données persistées
├── doc/            # documentation projet, technique et utilisateur
├── Dockerfile
├── docker-compose.yml
├── dev.ps1
└── pyproject.toml
```

## Licence

[Elastic License 2.0 (ELv2)](LICENSE) — auto-hébergement libre, redistribution et offre SaaS commerciale réservées.
