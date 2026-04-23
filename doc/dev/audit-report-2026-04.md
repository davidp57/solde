# Audit technique — Solde ⚖️

**Date** : 22 avril 2026  
**Périmètre** : revue complète de l'architecture, du code backend / frontend, de la sécurité, des tests, du déploiement Docker et de la qualité générale du projet.

---

## Table des matières

1. [Synthèse exécutive](#1-synthèse-exécutive)
2. [Architecture & structure](#2-architecture--structure)
3. [Sécurité](#3-sécurité)
4. [Qualité du code backend](#4-qualité-du-code-backend)
5. [Qualité du code frontend](#5-qualité-du-code-frontend)
6. [Tests & couverture](#6-tests--couverture)
7. [Base de données & migrations](#7-base-de-données--migrations)
8. [Docker & déploiement](#8-docker--déploiement)
9. [Documentation & processus](#9-documentation--processus)
10. [Synthèse des actions recommandées](#10-synthèse-des-actions-recommandées)

---

## 1. Synthèse exécutive

Le projet **Solde** est une application web de comptabilité associative qui affiche un bon niveau de maturité architecturale pour un v0.1. Le stack choisi (FastAPI + SQLite + Vue 3 + PrimeVue) est pertinent pour le cas d'usage. Les fondations sont solides : séparation claire modèles/services/routeurs, authentification JWT avec RBAC, comptabilité en partie double, i18n, et un Dockerfile multi-stage efficace.

**Cependant, l'audit révèle des problèmes significatifs** dans les domaines suivants, classés par criticité :

| Criticité | Domaine | Résumé |
|-----------|---------|--------|
| 🔴 Critique | Sécurité | Absence de rate limiting, CORS permissif, tokens en localStorage, pas de CSP |
| 🔴 Critique | Tests | 29 % de couverture (cible : 70–90 %), 11 tests en échec |
| 🟠 Majeur | Maintenabilité | Fichier `excel_import.py` de **5 038 lignes** — god class ingérable |
| 🟠 Majeur | Concurrence | Numérotation des écritures comptables non thread-safe |
| 🟡 Modéré | CORS production | Configuration `allow_origins=[]` bloquera le frontend en production |
| 🟡 Modéré | Résilience | `except Exception` généralisé masque les erreurs |
| 🟡 Modéré | Cohérence versions | `pyproject.toml` = 0.1.0, `package.json` = 0.0.0 |
| 🔵 Mineur | Divers | Patterns Decimal(str(…)) systématiques, pagination non bornée, endpoint reset-db dangereux |

---

## 2. Architecture & structure

### Points forts ✓

- **Séparation claire des couches** : `models/` → `schemas/` → `services/` → `routers/`. C'est un pattern professionnel bien respecté.
- **Composition API + `<script setup>`** côté frontend, conforme aux conventions du projet.
- **i18n en place** dès le départ avec `vue-i18n` et un fichier `fr.ts` complet.
- **Composants UI réutilisables** : `AppPage`, `AppPanel`, `AppStatCard`, etc. — bonne pratique de design system.
- **Routing avec guards de rôle** côté Vue Router, en cohérence avec le RBAC backend.
- **Lazy loading** systématique des vues Vue (dynamic imports).

### Problèmes identifiés

#### 🟠 P1 — Fichiers monstres (god modules)

| Fichier | Lignes |
|---------|--------|
| `services/excel_import.py` | **5 038** |
| `services/import_reversible.py` | **3 030** |
| `services/excel_import_parsers.py` | 824 |
| `services/accounting_entry_service.py` | 718 |
| `services/settings.py` | 692 |

**`excel_import.py`** avec plus de 5 000 lignes est un anti-pattern classique de « god class ». Même si des modules auxiliaires ont été extraits (`excel_import_parsers.py`, `excel_import_policy.py`, etc.), le fichier principal reste ingérable. Le nombre de `except Exception` (≥ 15 occurrences dans ce seul fichier) confirme une complexité hors norme.

**Recommandation** : refactorer en un package `services/excel_import/` avec des modules dédiés (orchestrateur, contacts, factures, paiements, comptabilité, salaires).

#### 🟡 P2 — Absence de layer applicatif (Use Cases)

Les routeurs appellent directement les services. Pour un projet de cette taille, l'ajout d'un layer applicatif (use cases / application services) serait prématuré, mais à anticiper si le domaine continue de croître.

#### 🟡 P3 — Modèle Payment avec `__allow_unmapped__ = True`

```python
class Payment(Base):
    __allow_unmapped__ = True
    invoice_number: str | None = None  # transient, non-mapped
    invoice_type: InvoiceType | None = None  # transient, non-mapped
```

Ce pattern mélange données persistées et données transientes sur le même ORM model. C'est un anti-pattern qui rend le modèle ambigu. Mieux vaut utiliser un DTO séparé ou peupler ces champs au niveau du schéma Pydantic.

---

## 3. Sécurité

### Points forts ✓

- Hachage des mots de passe avec **bcrypt**.
- JWT avec validation `iat` vs `password_changed_at` (révocation implicite à la rotation de mot de passe).
- Validation minimum 8 caractères sur les mots de passe.
- Upload de fichiers sécurisé : UUID pour les noms de fichiers (anti path traversal), vérification MIME + taille.
- Pas d'injection SQL : utilisation systématique de l'ORM SQLAlchemy, requêtes paramétrées.
- Pas de `v-html` dans les templates Vue (pas de risque XSS côté rendu).
- Jinja2 avec `autoescape=True` pour la génération de PDF.

### Problèmes identifiés

#### 🔴 S1 — Absence de rate limiting / protection brute force

L'endpoint `/api/auth/login` n'a **aucun mécanisme de limitation de débit**. Un attaquant peut effectuer un nombre illimité de tentatives de connexion.

**Recommandation** : Ajouter un middleware de rate limiting (ex. `slowapi` ou un simple compteur Redis/mémoire). Minimum : 5 tentatives / minute par IP sur `/auth/login`.

#### 🔴 S2 — JWT stocké en `localStorage` (XSS → vol de session)

```typescript
localStorage.setItem(ACCESS_TOKEN_KEY, access)
localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
```

Le `localStorage` est accessible par n'importe quel JavaScript de la page. Si une XSS est exploitée (dépendance tierce compromise, par exemple), l'attaquant récupère directement les tokens.

**Recommandation** : Stocker le refresh token dans un cookie `HttpOnly`, `Secure`, `SameSite=Strict`. L'access token peut rester en mémoire (variable JS) avec un rafraîchissement automatique.

#### 🔴 S3 — Pas d'en-têtes de sécurité HTTP

Aucun en-tête CSP, HSTS, X-Content-Type-Options, X-Frame-Options n'est configuré. En mono-conteneur, c'est la responsabilité de l'application.

**Recommandation** : Ajouter un middleware FastAPI qui injecte :
```
Content-Security-Policy: default-src 'self'; script-src 'self'
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
```

#### 🟠 S4 — CORS en production : `allow_origins=[]`

```python
allow_origins=["*"] if cfg.debug else [],
```

En mode production (`debug=False`), **aucune origine n'est autorisée**. Le frontend servi depuis le même conteneur ne sera probablement pas affecté (même origine), mais si l'API est accédée depuis un sous-domaine ou un reverse proxy, ça sera bloqué. C'est un piège insidieux car fonctionnel en dev, cassé en prod dans certains cas.

**Recommandation** : Ajouter un paramètre de configuration `cors_allowed_origins` pour la production, ou bien ne pas configurer CORS du tout si le frontend est servi du même domaine.

#### 🟠 S5 — Endpoint `POST /api/settings/reset-db` en production

Cet endpoint efface **toutes les données applicatives** et n'est protégé que par le rôle ADMIN. Il n'y a aucune confirmation supplémentaire, aucun log d'audit, et il est actif en production.

**Recommandation** : Désactiver cet endpoint hors `debug=True`, ou au minimum demander une double confirmation (token TOTP, re-saisie mot de passe).

#### 🟠 S6 — Mot de passe admin par défaut « changeme »

```python
admin_password: str = "changeme"
```

Si l'admin ne change pas le mot de passe après le bootstrap, l'application reste accessible avec des credentials triviaux. Pas de mécanisme de forçage de changement au premier login.

**Recommandation** : Forcer le changement de mot de passe au premier login (ajouter un flag `must_change_password` au modèle User).

#### 🟡 S7 — Secret JWT en dev/test auto-assigné

```python
_DEV_TEST_JWT_SECRET = "dev-secret-key-local-only-change-me-1234567890"
```

Si par erreur `debug=True` est activé en production, un secret fixe et public est utilisé. La protection existe (crash si `jwt_secret_key` manquant en non-debug), mais le fallback automatique augmente le risque.

#### 🟡 S8 — Pas de log d'audit sur les actions sensibles

Les échecs de connexion, les changements de rôle, les suppressions de données ne sont pas tracés dans un journal d'audit structuré. Le log applicatif standard ne suffit pas pour un contexte associatif gérant des données financières.

---

## 4. Qualité du code backend

### Points forts ✓

- **Decimal partout** pour les montants (pas de `float`), conformément aux instructions du projet.
- **Pydantic v2** avec validators cohérents (montants positifs, noms non vides, etc.).
- **Type annotations** sur les fonctions publiques des services.
- **SQLAlchemy 2** avec `Mapped[]` et `mapped_column()` — style moderne.
- **Numérotation automatique des factures** avec format `YYYY-C-NNNN`.
- **Machine à états** pour les statuts de facture avec transitions validées.
- **Lazy import de WeasyPrint** pour respecter la contrainte mémoire 384 Mo.

### Problèmes identifiés

#### 🟠 C1 — Numérotation des écritures comptables non concurrency-safe

```python
async def _next_entry_number(db: AsyncSession) -> str:
    result = await db.execute(select(func.count(AccountingEntry.id)))
    count = result.scalar_one_or_none() or 0
    return f"{count + 1:06d}"
```

Cette approche utilise `COUNT(*)` pour générer le numéro suivant. Si deux requêtes concurrentes arrivent, elles peuvent générer le même numéro. Avec SQLite et 1 worker Uvicorn ce risque est faible, mais il viole le principe de fiabilité comptable.

**Recommandation** : Utiliser `SELECT MAX(entry_number)` avec un lock, ou mieux, une séquence SQLite (`INSERT` + `last_insert_rowid`).

#### 🟠 C2 — Pattern `Decimal(str(x))` systématique

~30 occurrences de `Decimal(str(e.debit))`, `Decimal(str(inv.total_amount))`, etc.

Les colonnes `Numeric(10,2)` de SQLAlchemy avec aiosqlite retournent parfois des `float` au lieu de `Decimal`. Le contournement `Decimal(str(...))` est correct mais fragile et verbeux.

**Recommandation** : Configurer un `TypeDecorator` SQLAlchemy personnalisé qui garantit le retour en `Decimal` nativement, éliminant le besoin de conversion manuelle.

#### 🟡 C3 — `except Exception` excessif dans l'import Excel

Plus de 15 blocs `except Exception` dans `excel_import.py` et les routeurs associés. Ce pattern attrape tout (y compris `KeyboardInterrupt`, `SystemExit` via les re-raises). Même si certains sont justifiés pour la résilience de l'import, la majorité devrait attraper des exceptions typées.

#### 🟡 C4 — Pagination non bornée sur les endpoints de liste

```python
limit: int | None = Query(default=None, ge=1),
```

Tous les endpoints de liste (`/invoices/`, `/contacts/`, `/payments/`, etc.) ont `limit=None` par défaut. Un client peut donc récupérer la totalité de la base en une seule requête.

**Recommandation** : Ajouter un `limit` par défaut (ex. 100) et un `max_limit` (ex. 1000).

#### 🟡 C5 — Numérotation des factures basée sur `LIKE` pattern

```python
result = await db.execute(
    select(Invoice.number)
    .where(Invoice.number.like(pattern))
    .order_by(Invoice.id.desc())
    .limit(1)
)
```

L'ordre par `id` plutôt que par la partie séquentielle du numéro pourrait produire un résultat incorrect si des factures ont été insérées dans un ordre non chronologique (import, par exemple). De plus, le split `last.split("-")[-1]` suppose un format fixe.

#### 🔵 C6 — Settings singleton sans thread-safety

```python
_settings: Settings | None = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

Avec 1 worker Uvicorn, le risque est quasi nul. Mais si le nombre de workers augmente, c'est une race condition. Un simple `@lru_cache` serait plus idiomatique :
```python
@lru_cache
def get_settings() -> Settings:
    return Settings()
```

---

## 5. Qualité du code frontend

### Points forts ✓

- **Composition API + `<script setup>`** systématique — aucun Options API.
- **Pinia** pour le state management, avec un store auth bien structuré (token refresh, auto-login dev, etc.).
- **Intercepteur Axios** avec refresh queue pour gérer les 401 concurrents — implémentation solide.
- **i18n complet** : tous les labels sont des clés de traduction, pas de strings hardcodées dans les templates.
- **Composants UI réutilisables** (`AppPage`, `AppPanel`, `AppStatCard`, etc.).
- **Guard de navigation** Vue Router avec vérification de rôle.
- **Dark mode** avec composable dédié.
- **Pas de `v-html`** — aucun risque XSS via templates.

### Problèmes identifiés

#### 🟠 F1 — Pas de store Pinia pour les entités métier

Seuls 3 stores existent : `auth.ts`, `counter.ts` (généré par le scaffolding Vue), `fiscalYear.ts`. Les données métier (factures, contacts, paiements) sont gérées localement dans les vues, ce qui implique :
- Pas de cache côté client (chaque navigation re-fetch)
- Duplication de logique de chargement entre vues

**Recommandation** : Au minimum, ne pas ajouter de stores supplémentaires maintenant si les vues fonctionnent bien, mais supprimer `counter.ts` (code mort issu du scaffolding).

#### 🟡 F2 — `loginApi` utilise `axios` directement au lieu de `apiClient`

```typescript
// auth.ts
const response = await axios.post<TokenResponse>('/api/auth/login', form, { ... })
```

Les fonctions `loginApi`, `refreshApi`, `getMeApi` utilisent l'instance `axios` globale plutôt que l'`apiClient` configuré. C'est volontaire (ces requêtes se font avant/sans token), mais le mélange de deux instances Axios est source de confusion et contourne le timeout configuré.

#### 🟡 F3 — Version frontend `0.0.0`

```json
"version": "0.0.0"
```

Le `package.json` affiche `0.0.0` alors que `pyproject.toml` est en `0.1.0`. Les versions doivent être synchronisées.

#### 🔵 F4 — Pas de gestion d'erreur globale côté API

L'`apiClient` ne gère les erreurs que pour les 401. Les erreurs réseau, les 500, les 422 ne sont pas interceptées globalement. Chaque composant doit gérer ses propres erreurs.

---

## 6. Tests & couverture

### État actuel

| Métrique | Valeur | Cible |
|----------|--------|-------|
| Tests collectés | 739 | — |
| Tests passés | 617 | — |
| Tests échoués | 11 | 0 |
| Erreurs | 1 | 0 |
| **Couverture globale** | **29 %** | **≥ 80–90 %** |

### Problèmes identifiés

#### 🔴 T1 — Couverture à 29 % — largement sous les objectifs

Les instructions du projet fixent :
- Services métier : ≥ 90 %
- API endpoints : ≥ 80 %
- Composables frontend : ≥ 70 %

Avec 29 % de couverture globale, aucune de ces cibles n'est atteinte. Les modules critiques sont particulièrement mal couverts :
- `services/settings.py` : 21 %
- `services/salary_service.py` : 25 %

#### 🔴 T2 — 11 tests en échec + 1 erreur

Les tests échoués concernent principalement le parsing Excel (`test_excel_import_parsers.py`, `test_excel_import_parsing.py`). Cela indique soit des régressions non corrigées, soit un code qui a évolué sans mise à jour des tests — les deux sont inacceptables dans un workflow TDD.

Échecs identifiés :
- `test_parse_invoice_sheet_extracts_optional_cs_a_components`
- `test_parse_invoice_sheet_accepts_zero_value_cs_a_component`
- `test_parse_invoice_sheet_blocks_inconsistent_explicit_cs_a_components`
- `test_parse_payment_sheet_normalizes_payment_fields`
- `test_parse_cash_sheet_ignores_safe_rows_and_parses_signed_amount`
- `test_parse_bank_sheet_ignores_balance_description_and_parses_credit_debit`
- `test_parse_entries_sheet_ignores_zero_rows_and_reports_invalid_amounts`
- `test_parse_entries_sheet_keeps_change_num_marker`
- `test_parse_date_handles_datetime_and_string_formats`

Plus 1 erreur sur l'API d'import de test.

#### 🟡 T3 — Aucun test frontend d'intégration

Les tests frontend existent (16 fichiers spec), ce qui est positif. Mais il n'y a pas de tests end-to-end (Cypress, Playwright) pour valider les flux critiques complets.

#### 🟡 T4 — TDD non respecté

Les instructions du projet prescrivent une méthodologie TDD stricte (test first). La couverture à 29 % et les 11 tests en échec démontrent que cette discipline n'a pas été suivie. Les tests semblent écrits après coup plutôt qu'en amont.

---

## 7. Base de données & migrations

### Points forts ✓

- **21 migrations Alembic** bien numérotées et nommées.
- **WAL mode** activé pour SQLite (bonnes perfs en lecture concurrente).
- **`PRAGMA foreign_keys=ON`** activé explicitement.
- **`Numeric(10,2)` / `Numeric(12,2)`** pour tous les montants.
- **Index** sur les colonnes de filtrage et de jointure.

### Problèmes identifiés

#### 🟡 D1 — `init_db()` crée les tables + fait `metadata.create_all`

```python
await conn.run_sync(Base.metadata.create_all)
```

En parallèle des migrations Alembic. Cela signifie que si une migration est oubliée, `create_all` masquera le problème en dev mais pas en production (où seul Alembic tourne dans le `CMD` Docker). C'est une source classique de divergence schéma.

**Recommandation** : Retirer `Base.metadata.create_all` de `init_db()` et se reposer uniquement sur Alembic. Garder `create_all` uniquement dans la fixture de test.

#### 🟡 D2 — Pas de contrainte `CHECK` sur les montants

Les colonnes `amount`, `total_amount`, etc. n'ont pas de contrainte `CHECK` en base pour empêcher les valeurs négatives. La validation est faite au niveau Pydantic, mais un accès direct à la base (migration, script) pourrait insérer des données invalides.

#### 🔵 D3 — Noms de comptes hardcodés dans les données par défaut

Le plan comptable par défaut dans `accounting_account.py` contient des noms de clients spécifiques en dur (« Riad ALIOUCHE », « Fatou NDOYE/AST »). Ce sont des données personnelles qui ne devraient pas être dans le code source (RGPD).

---

## 8. Docker & déploiement

### Points forts ✓

- **Multi-stage build** : stage Node.js pour le frontend, Python slim pour le runtime.
- **Non-root user** (`solde:solde`).
- **1 worker Uvicorn** — conforme à la contrainte 384 Mo.
- **WeasyPrint deps** correctement installées.
- **Volume `./data`** pour la persistance.

### Problèmes identifiés

#### 🟠 K1 — Migrations dans le `CMD`

```dockerfile
CMD ["sh", "-c", "python -m alembic upgrade head && python -m uvicorn ..."]
```

Si la migration échoue, le conteneur ne démarre pas mais le `&&` shell masque la cause dans les logs. De plus, les migrations s'exécutent à chaque redémarrage.

**Recommandation** : Utiliser un script `entrypoint.sh` dédié avec gestion d'erreurs, ou séparer la migration dans un `initContainer` / `docker-compose` service séparé.

#### 🟡 K2 — Pas de health check Docker

Aucun `HEALTHCHECK` dans le Dockerfile, aucun `healthcheck:` dans le docker-compose. Le NAS Synology ne peut pas savoir si l'application est fonctionnelle.

**Recommandation** :
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/docs || exit 1
```

#### 🟡 K3 — `.env` non documenté

Le `docker-compose.yml` référence `env_file: .env` mais aucun `.env.example` n'est fourni. Un nouvel utilisateur ne sait pas quelles variables configurer.

#### 🔵 K4 — Pas de `docker-compose.override.yml` pour le dev

Le `docker-compose.yml` est orienté production. Le développement utilise `dev.ps1`, ce qui est correct, mais un `docker-compose.override.yml` avec les volumes de dev serait un plus.

---

## 9. Documentation & processus

### Points forts ✓

- **Plan d'architecture** (`doc/plan.md`) et **roadmap** (`doc/roadmap.md`) en place.
- **Backlog** centralisé dans `doc/backlog.md`.
- **Changelog** avec format Keep a Changelog.
- **Copilot instructions** détaillées (conventions de commit, git flow, TDD, etc.).

### Problèmes identifiés

#### 🟡 O1 — Absence de `.env.example`

Aucun fichier `.env.example` pour documenter les variables d'environnement nécessaires.

#### 🟡 O2 — Pas de documentation d'API (au-delà de Swagger)

L'API auto-documentée via OpenAPI/Swagger est un bon début, mais il manque une documentation développeur des flux métier (cycle de vie d'une facture, processus d'import Excel, mécanisme comptable).

#### 🔵 O3 — `counter.ts` dans le frontend

Fichier `stores/counter.ts` généré par le scaffolding Vue.js, non utilisé. Code mort.

---

## 10. Synthèse des actions recommandées

### 🔴 Priorité critique — À corriger immédiatement

| # | Action | Effort |
|---|--------|--------|
| S1 | **Ajouter un rate limiting** sur `/auth/login` (slowapi ou middleware custom) | Faible |
| S2 | **Migrer le refresh token vers un cookie HttpOnly** | Moyen |
| S3 | **Ajouter les en-têtes de sécurité HTTP** (CSP, HSTS, X-Frame-Options) | Faible |
| T1 | **Corriger les 11+1 tests en échec** | Moyen |
| T2 | **Monter la couverture** au minimum à 60 % (quick wins : services non couverts) | Élevé |

### 🟠 Priorité haute — Sprint suivant

| # | Action | Effort |
|---|--------|--------|
| P1 | **Refactorer `excel_import.py`** en package avec modules < 500 lignes | Élevé |
| C1 | **Corriger la numérotation des écritures** (MAX + lock au lieu de COUNT) | Faible |
| S5 | **Désactiver `reset-db`** en production ou ajouter un garde-fou | Faible |
| S6 | **Forcer le changement du mot de passe admin** au premier login | Moyen |
| K1 | **Séparer les migrations** du démarrage Uvicorn | Faible |

### 🟡 Priorité modérée — Backlog technique

| # | Action | Effort |
|---|--------|--------|
| S4 | Configurer les origines CORS pour la production | Faible |
| S8 | Ajouter un **journal d'audit** structuré pour les actions sensibles | Moyen |
| C2 | Créer un **TypeDecorator** pour Decimal et éliminer Decimal(str(…)) | Moyen |
| C3 | Typer les exceptions dans l'import Excel (remplacer `except Exception`) | Moyen |
| C4 | Ajouter des **limites de pagination** par défaut (100) et max (1000) | Faible |
| D1 | Retirer `create_all` de `init_db()` — Alembic seul pour le schéma | Faible |
| K2 | Ajouter un **HEALTHCHECK** Docker | Faible |
| K3 | Créer un `.env.example` | Faible |
| F3 | Synchroniser les versions frontend/backend | Faible |

### 🔵 Priorité faible — Nettoyage

| # | Action | Effort |
|---|--------|--------|
| D3 | Retirer les noms de personnes du plan comptable par défaut (RGPD) | Faible |
| F1 | Supprimer `stores/counter.ts` (code mort) | Trivial |
| P3 | Éliminer `__allow_unmapped__` du modèle Payment | Faible |
| C6 | Utiliser `@lru_cache` pour le singleton Settings | Trivial |

---

## 11. Suivi des corrections — Sprint 2026-04-22

Toutes les recommandations prioritaires (critique, haute, modérée) ont été implémentées dans la branche `chore-review-claude-opus`, mergée dans `develop` le 2026-04-23.

### ✅ Priorité critique — Corrigé

| # | Action | Ticket | Date |
|---|--------|--------|------|
| S1 | Rate limiting sur `/auth/login` (slowapi, 5 req/min) | BL-045 | 2026-04-22 |
| S2 | Refresh token migré vers cookie `HttpOnly`/`Secure`/`SameSite=Strict` | BL-046 | 2026-04-22 |
| S3 | En-têtes de sécurité HTTP (CSP, HSTS, X-Frame-Options, etc.) | BL-047 | 2026-04-22 |
| T1 | 11 tests en échec corrigés + 1 erreur API | BL-048 | 2026-04-22 |
| T2 | Couverture remontée à ~71 % (+44 tests unitaires) | BL-049 | 2026-04-22 |

### ✅ Priorité haute — Corrigé

| # | Action | Ticket | Date |
|---|--------|--------|------|
| P1 | `excel_import.py` (5 567 L) éclaté en package 16 sous-modules | BL-050 | 2026-04-22 |
| C1 | Numérotation des écritures : `MAX+1` au lieu de `COUNT` | BL-051 | 2026-04-22 |
| S5 | `reset-db` protégé : HTTP 403 si `debug=False` | BL-052 | 2026-04-22 |
| S6 | Changement de mot de passe forcé au premier login / reset admin | BL-053 | 2026-04-22 |
| K1 | `entrypoint.sh` séparant migrations et démarrage Uvicorn | BL-054 | 2026-04-22 |

### ✅ Priorité modérée — Corrigé

| # | Action | Ticket | Date |
|---|--------|--------|------|
| S4 | CORS configurables via `CORS_ALLOWED_ORIGINS` | BL-055 | 2026-04-22 |
| S8 | Journal d'audit structuré (table `audit_logs`, 7 types d'événements) | BL-056 | 2026-04-22 |
| C2 | `DecimalType` TypeDecorator — élimination des `Decimal(str(...))` | BL-057 | 2026-04-22 |
| C3 | Exceptions typées dans l'import Excel | BL-058 | 2026-04-22 |
| C4 | `limit=100`/`max=1000` sur tous les endpoints de liste | BL-059 | 2026-04-22 |
| D1 | `create_all` retiré de `init_db()` — Alembic seul | BL-060 | 2026-04-22 |
| K2 | `HEALTHCHECK` Docker + `docker-compose.yml` | BL-061 | 2026-04-22 |
| F3 | Versions frontend/backend synchronisées à `0.1.0` | BL-062 | 2026-04-22 |

### ✅ Priorité faible — Corrigé

| # | Action | Ticket | Date |
|---|--------|--------|------|
| D3 | Noms de personnes retirés du plan comptable par défaut (RGPD) | BL-063 | 2026-04-22 |
| F1 | `stores/counter.ts` supprimé | BL-064 | 2026-04-22 |
| P3 | `__allow_unmapped__` éliminé du modèle Payment | BL-065 | 2026-04-22 |
| C6 | `@lru_cache` pour le singleton Settings | BL-066 | 2026-04-22 |

### 🔵 Ouvert

| # | Action | Raison |
|---|--------|--------|
| K3 | `.env.example` | Non planifié dans ce sprint |
| O2 | Documentation développeur des flux métier | Chantier long terme |

---

## Conclusion

Le projet montre un **bon niveau de conception architecturale** — la séparation des responsabilités, le choix des technologies, la gestion de l'i18n et le système de comptabilité en partie double témoignent d'une compréhension solide du domaine.

Les **faiblesses principales** sont typiques d'un développement entièrement piloté par IA : **couverture de test insuffisante** (l'IA génère du code fonctionnel mais ne maintient pas la discipline TDD), **fichiers géants** (l'IA accumule du code sans refactorer), et **lacunes de sécurité non fonctionnelles** (rate limiting, en-têtes HTTP, stockage des tokens — des aspects que l'IA ne « pense » pas spontanément).

Les corrections critiques (sécurité + tests) sont réalisables rapidement et transformeraient ce prototype fonctionnel en application prête pour la production.
