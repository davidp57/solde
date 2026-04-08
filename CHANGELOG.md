# Changelog

Toutes les modifications notables apportées à Solde ⚖️ sont documentées ici.

Le format suit [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Ce projet respecte le [Versionnage sémantique](https://semver.org/lang/fr/).

---

## [Non publié]

### Ajouté

**Backend**
- Modèle `Contact` : type (`client` | `fournisseur` | `les_deux`), nom, prénom, email, téléphone, adresse, notes, soft-delete (`is_active`)
- Migration Alembic `0002` : table `contacts`
- Service contacts : CRUD complet, recherche insensible à la casse sur nom/prénom/email, filtrage par type, pagination
- Routeur `/api/contacts/` : CRUD REST avec guards rôle (`SECRETAIRE+`)
- Modèle `AccountingAccount` : numéro (unique), label, type (`actif` | `passif` | `charge` | `produit`), soft-delete
- 24 comptes comptables associatifs pré-configurés (`DEFAULT_ACCOUNTS`) + seed idempotent
- Migration Alembic `0003` : table `accounting_accounts`
- Service plan comptable : CRUD, seed idempotent, filtre par type
- Routeur `/api/accounting/accounts/` : CRUD REST + `POST /seed` avec guards rôle (`TRESORIER+`)
- 103 tests pytest (unitaires + intégration) — 89 % de couverture

**Frontend**
- `api/contacts.ts` : fonctions CRUD vers `/api/contacts/`
- `api/accounting.ts` : fonctions CRUD vers `/api/accounting/accounts/` + seed
- `ContactsView.vue` : DataTable PrimeVue avec recherche (debounce 300 ms) et filtre par type, Dialog création/édition, suppression avec confirmation
- `AccountingAccountsView.vue` : DataTable avec filtre par type (boutons), bouton Seed, Dialog création/édition
- `ContactForm.vue` : formulaire de création/édition de contact
- `AccountForm.vue` : formulaire de création/édition de compte comptable (numéro désactivé en édition)
- Routes `/contacts` et `/accounting/accounts` ajoutées au Vue Router
- Entrées de navigation contacts (`pi-users`) et plan comptable (`pi-list`) dans `NavMenu.vue`
- Clés i18n supplémentaires : `contacts.*`, `accounting.*`, `common.all`, `common.actions`

---

**Backend (Phase 1)**
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
