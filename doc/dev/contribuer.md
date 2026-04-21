# Contribuer à Solde

## Objectif

Ce document centralise la mise en route locale, les commandes de qualité et les conventions de contribution du dépôt.
Il complète le `README.md`, qui reste une page d'entrée plus courte orientée installation et navigation dans la documentation.

## Pile et prérequis

### Outils

- Python `3.11+` ;
- Node.js `20+` (`22` recommandé pour coller à l'image Docker) ;
- npm ;
- Docker si tu veux aussi reproduire le mode d'exécution conteneurisé ;
- PowerShell recommandé sur Windows pour `dev.ps1`.

### Technologies du projet

- backend : FastAPI, SQLAlchemy async, Alembic, Pydantic v2, SQLite ;
- frontend : Vue 3, Vite, TypeScript, PrimeVue, Pinia ;
- tests : pytest côté backend, Vitest côté frontend.

## Mise en route locale

### 1. Cloner et préparer l'environnement backend

```powershell
git clone git@github.com:davidp57/solde.git
cd solde
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
Copy-Item .env.example .env
alembic upgrade head
```

Sous Linux/macOS, adapter l'activation de l'environnement virtuel et la copie du fichier `.env`.

### 2. Installer le frontend

```bash
cd frontend
npm install
cd ..
```

### 3. Lancer l'application

Option la plus simple sous Windows :

```powershell
./dev.ps1
```

Ce script :

- démarre le backend et le frontend dans la même session ;
- installe `frontend/node_modules` si nécessaire ;
- arrête proprement les deux processus avec `Ctrl+C`.

Option manuelle :

```powershell
uvicorn backend.main:app --reload --port 8000
```

```bash
cd frontend
npm run dev
```

Accès utiles :

- frontend Vite : `http://localhost:5173`
- application servie par FastAPI si le frontend est compilé : `http://localhost:8000`
- docs API : `http://localhost:8000/api/docs`

## Commandes de qualité

Les commandes ci-dessous correspondent aux attentes actuelles du dépôt avant ouverture d'une PR.

### Backend

```bash
ruff check .
ruff format --check .
mypy .
pytest tests/
```

### Frontend

```bash
cd frontend
npx vue-tsc --noEmit -p tsconfig.app.json
npx vue-tsc --noEmit
npx eslint src/
npx vitest run
```

### Conseils pratiques

- activer l'environnement virtuel Python avant les commandes backend ;
- lancer toute la matrice avant une PR, même si le changement est concentré sur un sous-ensemble ;
- pour une itération rapide, commencer par les tests ciblés puis rejouer la matrice complète avant commit final.

## Structure du dépôt

- `backend/` : API, schémas, services, modèles, migrations ;
- `frontend/` : application Vue.js ;
- `tests/` : tests backend pytest ;
- `doc/` : documentation projet, technique et utilisateur ;
- `data/` : données persistées locales ou montées en Docker.

## Conventions de développement

### Langues

- code, noms de symboles, commentaires et docstrings : anglais ;
- interface utilisateur, documentation du dépôt et communication avec l'utilisateur : français.

### Backend

- annotations de type requises sur les fonctions et méthodes publiques ;
- schémas d'entrée/sortie en Pydantic v2 ;
- SQLAlchemy 2 en mode async ;
- migrations Alembic pour toute évolution de schéma ;
- `Decimal` pour les montants monétaires ;
- exceptions typées dans les services, conversion en réponses HTTP dans les routers.

### Frontend

- Vue 3 Composition API avec `script setup` ;
- Pinia pour l'état global ;
- pas d'Options API ;
- textes utilisateurs via les clés i18n, pas en dur dans les composants.

### Documentation et backlog

- toute documentation du dépôt est rédigée en français ;
- `doc/backlog.md` est la source de vérité des sujets ouverts ou suivis hors roadmap ;
- si un sujet démarre sur une branche, son statut et ses dates doivent être mis à jour dans le backlog ;
- les documents impactés par un changement significatif doivent être mis à jour dans la même branche.

## Workflow Git

Le projet suit un workflow de type git-flow :

- `main` : releases de production ;
- `develop` : branche d'intégration ;
- branches de travail dérivées de `develop`.

Nommage attendu en priorité :

- `feature/*` pour une fonctionnalité ;
- `fix/*` pour un correctif ;
- `hotfix/*` pour une urgence en production ;
- `release/*` pour une préparation de release.

Pour une branche purement documentaire, utiliser un nom explicite convenu avec l'équipe tout en gardant une origine depuis `develop`.

### Commits

Utiliser les Conventional Commits en anglais :

- `feat(import): add reversible run history`
- `fix(settings): return 404 for unknown fiscal year`
- `docs(readme): clarify Docker operations`

## Attentes avant PR

Avant d'ouvrir une PR :

1. rebaser ou resynchroniser ta branche à partir de `develop` si nécessaire ;
2. mettre à jour le backlog si le ticket est suivi dans `doc/backlog.md` ;
3. mettre à jour le `README`, la doc technique, la doc utilisateur ou le `CHANGELOG.md` si le changement le justifie ;
4. lancer la matrice de qualité pertinente ;
5. préparer une description de PR concise en anglais avec résumé, changements clés et checks exécutés.

## TDD et niveau d'exigence attendu

Le dépôt vise une approche TDD :

1. écrire ou adapter un test qui décrit le comportement attendu ;
2. implémenter le minimum pour le faire passer ;
3. refactorer en gardant les tests verts.

Objectifs rappelés dans les consignes du dépôt :

- services métier backend : couverture `>= 90 %` ;
- endpoints API : couverture `>= 80 %` ;
- composables frontend : couverture `>= 70 %`.

## Docs utiles à relire selon le sujet

- `README.md` pour l'entrée projet ;
- `doc/dev/exploitation.md` pour le fonctionnement Docker et les données persistées ;
- `doc/plan.md` pour la cible d'architecture ;
- `doc/roadmap.md` pour la séquence de livraison ;
- `doc/user/` pour l'impact utilisateur des fonctionnalités existantes.