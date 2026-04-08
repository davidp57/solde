# Architecture — Solde ⚖️

## Vue d'ensemble

Solde est une application web monolithique modulaire déployée dans un seul conteneur Docker sur un NAS Synology. L'interface Vue.js 3 est servie comme fichiers statiques directement par FastAPI, ce qui élimine le besoin d'un reverse proxy ou d'un serveur web séparé.

```
Navigateur
    │
    ▼
Docker container (port 8080)
    │
    ├── Uvicorn (1 worker)
    │       │
    │       └── FastAPI
    │               ├── /api/**  →  Routers Python
    │               └── /*       →  StaticFiles (frontend/dist/)
    │
    └── Volume ./data/
            ├── solde.db          (SQLite WAL)
            ├── uploads/          (factures fournisseurs)
            └── pdfs/             (factures clients générées)
```

**Budget RAM cible : ≤ 384 Mo sur NAS Synology**

| Composant | RAM estimée |
|---|---|
| Uvicorn + FastAPI (idle) | ~50–80 Mo |
| SQLite (pas en mémoire) | ~0 Mo |
| Vue.js (fichiers statiques) | 0 Mo côté serveur |
| WeasyPrint (pic génération PDF) | ~30–50 Mo |
| **Total idle** | **~80–130 Mo** |
| **Total pic** | **~180 Mo** |

---

## Stack technique

| Couche | Technologie | Version | Justification |
|---|---|---|---|
| Serveur API | FastAPI + Uvicorn | 0.115+ | Async natif, performances, documentation OpenAPI auto |
| Base de données | SQLite (WAL mode) | — | Zéro configuration, adapté usage mono-instance NAS |
| ORM | SQLAlchemy 2 async | 2.0+ | Sessions async, type safety, migrations Alembic |
| Migrations | Alembic | — | Contrôle de version du schéma |
| Authentification | python-jose (JWT) + bcrypt | — | JWT stateless ; bcrypt direct (passlib incompatible Python 3.13) |
| Validation | Pydantic v2 | 2.0+ | Schemas d'entrée/sortie, Settings de configuration |
| Génération PDF | WeasyPrint | — | Import à la demande pour économiser la RAM |
| Envoi email | smtplib (stdlib) | — | Pas de dépendance externe |
| Frontend | Vue.js 3 + Vite | 3.x | Composition API, TypeScript natif |
| UI | PrimeVue 4 | 4.x | Composants riches, thème Aura CSS-only |
| État | Pinia | 2.x | Léger, Composition API compatible |
| Routeur | Vue Router | 4.x | Guards de navigation, lazy-loading |
| i18n | vue-i18n | 11.x | Toutes les chaînes UI externalisées en français |
| Client HTTP | axios | — | Intercepteurs JWT + auto-refresh 401 |
| Tests backend | pytest + pytest-asyncio + httpx | — | Tests async, client ASGI en mémoire |
| Tests frontend | Vitest | — | Natif Vite, compatible jsdom |
| Linting/Format | ruff (Python) + ESLint + Prettier (JS) | — | Qualité uniforme |

---

## Structure du projet

```
solde/
├── backend/
│   ├── __init__.py
│   ├── main.py              # create_app(), lifespan, CORS, montage StaticFiles
│   ├── config.py            # Pydantic Settings (JWT, SMTP, année fiscale)
│   ├── database.py          # Engine async, WAL, get_db(), init_db()
│   ├── models/              # Modèles SQLAlchemy (une table = un fichier)
│   ├── routers/             # Routes FastAPI par domaine métier
│   ├── services/            # Logique métier (indépendante de HTTP)
│   ├── schemas/             # Pydantic : validation entrées, sérialisation sorties
│   ├── templates/           # Templates Jinja2 pour les PDFs WeasyPrint
│   └── alembic/             # Migrations Alembic
├── frontend/
│   ├── src/
│   │   ├── api/             # Fonctions d'appel API + client axios + types TypeScript
│   │   ├── layouts/         # Layouts applicatifs (AppLayout responsive)
│   │   ├── views/           # Pages Vue (une route = une vue)
│   │   ├── components/      # Composants réutilisables
│   │   ├── stores/          # Stores Pinia (auth, ...)
│   │   ├── router/          # Définition des routes + guards
│   │   └── i18n/            # Fichiers de traduction (fr.ts)
│   ├── vite.config.ts       # Proxy /api → backend en dev
│   └── vitest.config.ts
├── tests/
│   ├── unit/                # Tests unitaires (services, config)
│   ├── integration/         # Tests API (httpx AsyncClient)
│   └── conftest.py          # Fixtures partagées (DB in-memory, client, admin_user)
├── data/                    # Volume Docker (gitignore)
├── doc/
│   ├── plan.md              # Spécifications fonctionnelles et modèle de données
│   ├── roadmap.md           # Avancement par phase et prochaines étapes
│   └── architecture.md      # Ce document
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

---

## Décisions d'architecture

### SQLite plutôt que PostgreSQL

Usage mono-instance sur NAS domestique, quelques dizaines d'utilisateurs maximum. SQLite en mode WAL offre la concurrence lecture/écriture suffisante. Évite un second conteneur et ~50 Mo de RAM. Facilite les sauvegardes (copie d'un seul fichier).

### Mono-container Docker

Un seul conteneur simplifie le déploiement sur Portainer (NAS Synology). Le build multi-stage (`node:22-alpine` → `python:3.13-slim`) produit une image unique qui sert à la fois l'API et les fichiers statiques.

### Frontend servi par FastAPI

Élimine le besoin de Nginx ou d'un proxy inverse. FastAPI monte `frontend/dist/` via `StaticFiles` avec `html=True` pour le routing SPA (toutes les routes inconnues retournent `index.html`).

### bcrypt direct (sans passlib)

`passlib` est incompatible avec `bcrypt >= 4.0` sur Python 3.13 (attribut `__about__` manquant). Solution : appel direct à `bcrypt.hashpw()` / `bcrypt.checkpw()`.

### WeasyPrint importé à la demande

WeasyPrint charge ~30–50 Mo de bibliothèques au moment de l'import. Import différé dans le service de génération PDF pour ne pas pénaliser le démarrage.

### Tokens JWT stateless

Pas de table de sessions en base. Le refresh token (durée longue) permet de renouveler l'access token (durée courte) sans re-authentification. La révocation n'est pas implémentée en Phase 1 (acceptable pour une appli interne avec peu d'utilisateurs).

### Rôles applicatifs

| Rôle | Périmètre |
|---|---|
| `ADMIN` | Tout, y compris gestion des utilisateurs et paramètres |
| `TRESORIER` | Gestion complète + comptabilité (sans gestion utilisateurs) |
| `SECRETAIRE` | Factures et paiements uniquement |
| `READONLY` | Consultation seule, aucune modification |

---

## Flux d'authentification

```
Navigateur                         API
    │                               │
    │  POST /api/auth/login         │
    │  (username + password)        │
    │ ─────────────────────────►   │
    │                               │  Vérifie bcrypt
    │  { access_token,              │  Génère JWT (15 min)
    │    refresh_token }            │  Génère refresh (7 jours)
    │ ◄─────────────────────────   │
    │                               │
    │  GET /api/...                 │
    │  Authorization: Bearer <jwt>  │
    │ ─────────────────────────►   │
    │                               │  Décode JWT
    │  Données                      │  Vérifie expiration + rôle
    │ ◄─────────────────────────   │
    │                               │
    │  (JWT expiré → 401)           │
    │  POST /api/auth/refresh       │
    │  { refresh_token }            │
    │ ─────────────────────────►   │
    │  { access_token, ... }        │
    │ ◄─────────────────────────   │
```

L'intercepteur axios dans `api/client.ts` gère automatiquement le rafraîchissement et met en file d'attente les requêtes concurrentes pendant le renouvellement du token.

---

## Conventions de code

- **Python** : annotations de type obligatoires sur toutes les fonctions publiques ; Pydantic v2 pour les schemas ; style SQLAlchemy 2 async
- **Vue.js** : Composition API + syntaxe `<script setup>` ; Pinia pour l'état ; pas d'Options API
- **SQL** : migrations Alembic pour tout changement de schéma ; jamais de modification directe de la base
- **Sécurité** : validation de toutes les entrées aux frontières API ; pas de secrets dans le code (variables d'environnement) ; requêtes paramétrées uniquement (ORM SQLAlchemy, pas de SQL par concaténation)
- **Monétaire** : `Decimal` Python (jamais `float`) pour tous les montants afin d'éviter les erreurs d'arrondi
