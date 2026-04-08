# Solde ⚖️

Application web de gestion comptable pour une association loi 1901 (soutien scolaire).
Remplace deux fichiers Excel par une solution intégrée : facturation, paiements, caisse, banque, comptabilité en partie double.

---

## Fonctionnalités

- **Facturation** clients et fournisseurs (PDF, envoi email)
- **Paiements** multi-modes (espèces, chèque, virement)
- **Caisse** avec comptage physique et rapprochement
- **Banque** avec import CSV/OFX et rapprochement
- **Comptabilité** en partie double avec moteur de règles configurable
- **Multi-utilisateurs** avec rôles (Admin, Trésorier, Secrétaire, Lecture seule)
- **Plan comptable** associatif simplifié pré-configuré

---

## Prérequis

- [Docker](https://docs.docker.com/get-docker/) et Docker Compose
- Ou pour le développement local : Python 3.11+ et Node.js 20+

---

## Démarrage rapide (Docker)

```bash
# 1. Cloner le dépôt
git clone git@github.com:davidp57/solde.git
cd solde

# 2. Configurer l'environnement
cp .env.example .env
# Éditer .env et renseigner JWT_SECRET_KEY (32+ caractères), paramètres SMTP, etc.

# 3. Lancer
docker-compose up -d

# 4. Ouvrir dans le navigateur
# http://localhost:8080
```

Le premier démarrage crée automatiquement la base de données et un compte administrateur
avec les identifiants définis dans `.env`.

---

## Développement local

### Backend (Python)

```bash
# Créer et activer l'environnement virtuel
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/macOS

# Installer les dépendances
pip install -e ".[dev]"

# Configurer l'environnement
cp .env.example .env
# Éditer .env (JWT_SECRET_KEY obligatoire)

# Appliquer les migrations
alembic upgrade head

# Lancer le serveur de développement
uvicorn backend.main:app --reload --port 8000
```

### Frontend (Vue.js)

```bash
cd frontend
npm install
npm run dev
# Ouvre http://localhost:5173
# Le proxy Vite redirige /api vers le backend sur le port 8000
```

### Tests

```bash
# Backend
pytest tests/ -v --cov=backend

# Frontend
cd frontend
npm run test:unit
```

---

## Variables d'environnement

Voir `.env.example` pour la liste complète. Variables obligatoires :

| Variable | Description |
|---|---|
| `JWT_SECRET_KEY` | Clé secrète JWT (minimum 32 caractères) |
| `DATABASE_URL` | Chemin vers la base SQLite (défaut : `sqlite+aiosqlite:///./data/solde.db`) |

Variables optionnelles (email) :

| Variable | Description |
|---|---|
| `SMTP_HOST` | Serveur SMTP pour l'envoi des factures |
| `SMTP_PORT` | Port SMTP (défaut : 587) |
| `SMTP_USERNAME` | Identifiant SMTP |
| `SMTP_PASSWORD` | Mot de passe SMTP |
| `SMTP_FROM` | Adresse expéditeur |

---

## Structure du projet

```
solde/
├── backend/            # API FastAPI
│   ├── main.py         # Point d'entrée
│   ├── config.py       # Configuration Pydantic Settings
│   ├── database.py     # SQLAlchemy async + SQLite WAL
│   ├── models/         # Modèles SQLAlchemy
│   ├── routers/        # Routes API par module
│   ├── services/       # Logique métier
│   ├── schemas/        # Validation Pydantic (entrées/sorties)
│   └── templates/      # Templates Jinja2 pour les PDFs
├── frontend/           # Application Vue.js 3
│   └── src/
│       ├── api/        # Client axios + types
│       ├── layouts/    # AppLayout responsive
│       ├── stores/     # État Pinia (auth, ...)
│       ├── views/      # Pages
│       └── i18n/       # Traductions françaises
├── tests/              # Tests Python (pytest)
├── data/               # Volume Docker : base SQLite + fichiers
├── doc/                # Documentation technique
│   ├── plan.md         # Architecture et décisions techniques
│   ├── roadmap.md      # Avancement et prochaines étapes
│   └── architecture.md # Diagrammes et choix d'architecture
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## Documentation

- [Architecture technique](doc/architecture.md)
- [Plan complet du projet](doc/plan.md)
- [Roadmap et état d'avancement](doc/roadmap.md)
- [Changelog](CHANGELOG.md)

---

## Licence

[Elastic License 2.0 (ELv2)](LICENSE) — auto-hébergement libre, redistribution et offre SaaS commerciale réservées.
