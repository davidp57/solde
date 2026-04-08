# Changelog

Toutes les modifications notables apportées à Solde ⚖️ sont documentées ici.

Le format suit [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Ce projet respecte le [Versionnage sémantique](https://semver.org/lang/fr/).

---

## [Non publié]

### Ajouté

**Backend**
- Fabrique d'application FastAPI (`create_app()`) avec lifespan, CORS, service des fichiers statiques Vue.js
- Configuration Pydantic Settings avec validation : `JWT_SECRET_KEY` (min 32 caractères), `FISCAL_YEAR_START_MONTH` (défaut 8 = août), paramètres SMTP optionnels
- Moteur SQLAlchemy 2 async avec SQLite en mode WAL et contrôle des clés étrangères
- Modèle `User` avec enum `UserRole` : `READONLY`, `SECRETAIRE`, `TRESORIER`, `ADMIN`
- Service d'authentification : hachage bcrypt (direct, compatible Python 3.13), tokens JWT accès + rafraîchissement
- Routeur auth : `POST /api/auth/login`, `POST /api/auth/refresh`, `GET /api/auth/me`, `POST /api/auth/users` (admin uniquement)
- Dépendance `get_current_user` et fabrique `require_role(*roles)` pour l'autorisation des routes
- **Alembic** : `alembic.ini`, `backend/alembic/env.py` (async), `script.py.mako`, migration `0001` (tables `users` + `app_settings`)
- **Modèle `AppSettings`** : table single-row (id=1) pour les paramètres de l'association et SMTP
- **API Settings** : `GET /api/settings/` et `PUT /api/settings/` avec mise à jour partielle (admin uniquement) — `smtp_password` exclu de la réponse
- **Service settings** : `get_settings()` (création automatique si absente) et `update_settings()` (partial update)
- 44 tests pytest (unitaires + intégration) — 88 % de couverture

**Frontend**
- Scaffold Vue.js 3 avec TypeScript, Vue Router, Pinia, Vitest, ESLint + Prettier
- PrimeVue 4 avec preset Aura (`@primeuix/themes`) et primeicons
- `vue-i18n` v11 avec locale française (auth, navigation, paramètres, rôles utilisateurs)
- Client API axios avec injection du header `Authorization` et rafraîchissement automatique du token sur 401
- `useAuthStore` (Pinia) : connexion/déconnexion/rafraîchissement, persistance localStorage, computed `isAdmin`/`isTresorier`
- `LoginView.vue` : formulaire PrimeVue avec messages d'erreur i18n
- `AppLayout.vue` : layout responsive — barre latérale desktop + tiroir mobile
- `NavMenu.vue` : menu de navigation adapté au rôle
- Vue Router avec guards `requiresAuth` et `requiresAdmin`, chargement paresseux des routes protégées
- **`api/settings.ts`** : `getSettingsApi()` et `updateSettingsApi()`
- **`SettingsView.vue`** : formulaire PrimeVue complet — infos association (nom, SIRET, adresse, mois début exercice) + configuration SMTP (host, port, user, from, TLS toggle) avec messages de succès/erreur
- 11 tests Vitest unitaires pour le store auth — tous verts

**Infra**
- `Dockerfile` multi-stage : `node:22-alpine` pour le build Vue.js, `python:3.13-slim` pour le runtime, utilisateur non-root `solde`
- `docker-compose.yml` : 1 service, 1 volume `./data`, port 8000
- `.dockerignore`
- `.env.example` documenté (JWT_SECRET_KEY, DATABASE_URL, SMTP optionnel)
- README mis à jour avec les instructions d'installation dev et Docker

### Modifié

- Remplacement de `passlib[bcrypt]` par `bcrypt` en import direct (compatibilité Python 3.13 + bcrypt ≥ 4.0)
- `UserRole` migré de `(str, Enum)` vers `StrEnum` (Python 3.11+)
- Annotations de type ajoutées sur `_build_engine()`, `lifespan()`, `require_role()` et `do_run_migrations()` (mypy strict)

---

[Non publié]: https://github.com/davidp57/solde/commits/feature/phase1-foundations
