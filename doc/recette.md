# Suivi de recette — phase post-merge lot N

Ce fichier trace toutes les modifications apportées **directement sur `develop`** pendant la phase de validation applicative (recette), à partir du merge de la PR #51 (lot N — UX Formulaires).

Chaque ticket correspond à un ou plusieurs commits liés. Les identifiants `REC-NNN` sont locaux à ce document.

---

## Tickets

### REC-001 — Version applicative lue depuis `pyproject.toml` côté backend

| Champ | Valeur |
|---|---|
| **Type** | `chore` |
| **Date** | 2026-04-25 |
| **Commit** | `5247f2e` |
| **Fichiers** | `backend/config.py`, `.env.example` |

**Description** : La version de l'application n'est plus définie dans `.env` via `APP_VERSION`. Elle est désormais lue depuis les métadonnées du package (`importlib.metadata.version("solde")`) en s'appuyant sur le champ `version` de `pyproject.toml`, seule source de vérité.

---

### REC-002 — Fix Docker : compatibilité gdk-pixbuf Debian Trixie

| Champ | Valeur |
|---|---|
| **Type** | `fix` |
| **Date** | 2026-04-25 |
| **Commit** | `047b672` |
| **Fichiers** | `Dockerfile` |

**Description** : Le paquet `libgdk-pixbuf2.0-0` n'existe plus sous Debian Trixie. Remplacé par `libgdk-pixbuf-xlib-2.0-0` pour que WeasyPrint puisse générer les PDFs.

---

### REC-003 — Fix Docker : SPA routing sur rechargement direct + .gitattributes

| Champ | Valeur |
|---|---|
| **Type** | `fix` |
| **Date** | 2026-04-25 |
| **Commit** | `01058cd` |
| **Fichiers** | `backend/main.py`, `.gitattributes` |

**Description** : Un rechargement direct sur une route Vue (`/contacts`, `/invoices`…) retournait une 404. FastAPI sert maintenant `index.html` en fallback pour toutes les routes non-API (`/api/**`). Ajout de `.gitattributes` pour forcer LF sur `entrypoint.sh` et éviter les erreurs de syntaxe shell sur Windows.

---

### REC-004 — Ajout du bouton « Télécharger une sauvegarde » (CHR-019)

| Champ | Valeur |
|---|---|
| **Type** | `feat` |
| **Date** | 2026-04-25 |
| **Commit** | `209fb94` |
| **Fichiers** | `frontend/src/api/settings.ts`, `frontend/src/components/settings/SettingsBackupPanel.vue`, `frontend/src/views/SettingsView.vue`, `frontend/src/i18n/fr.ts`, `doc/dev/exploitation.md`, `doc/backlog.md` |

**Description** : Nouveau panneau dans la page Paramètres permettant à un admin de déclencher une sauvegarde de la base de données et de la télécharger directement depuis le navigateur. Nom du fichier horodaté. Ajout de la section déploiement Portainer / NAS Synology dans `exploitation.md`.

---

### REC-005 — Fix navigation : écran Salaires accessible rôle Management

| Champ | Valeur |
|---|---|
| **Type** | `feat` |
| **Date** | 2026-04-25 |
| **Commit** | `992f907` |
| **Fichiers** | `frontend/src/components/NavMenu.vue`, `frontend/src/router/index.ts`, `frontend/src/tests/views/NavMenu.spec.ts` |

**Description** : L'accès à l'écran Salaires était limité aux rôles `tresorier` et `admin`. Il est élargi au rôle `secretaire` (Management), conformément au besoin métier de la phase de recette.

---

### REC-006 — Source de vérité version dans Vite : passage à `pyproject.toml`

| Champ | Valeur |
|---|---|
| **Type** | `chore` |
| **Date** | 2026-04-25 |
| **Commit** | `d61399b` |
| **Fichiers** | `frontend/vite.config.ts`, `frontend/package.json` |

**Description** : `vite.config.ts` lisait la version depuis `package.json`. Il lit maintenant `pyproject.toml` via regex (`/^version\s*=\s*"([^"]+)"/m`) et injecte `__APP_VERSION__` dans le bundle. `package.json` reste à jour mais n'est plus la source de vérité pour Vite.

---

### REC-007 — Fix Docker : `pyproject.toml` absent du stage `frontend-builder`

| Champ | Valeur |
|---|---|
| **Type** | `fix` |
| **Date** | 2026-04-25 |
| **Commit** | `4f19c62` |
| **Fichiers** | `Dockerfile` |

**Description** : Suite à REC-006, le build Docker échouait : le stage `frontend-builder` ne copiait pas `pyproject.toml`. Ajout d'un `COPY pyproject.toml ../` avant `COPY frontend/ ./` dans ce stage.

---

### REC-008 — CRUD complet des règles comptables (admin uniquement)

| Champ | Valeur |
|---|---|
| **Type** | `feat` |
| **Date** | 2026-04-25 |
| **Commit** | `1fe2274` |
| **Fichiers** | `backend/schemas/accounting_rule.py`, `backend/services/accounting_rule_service.py`, `backend/routers/accounting_rule.py`, `backend/config.py`, `backend/main.py`, `frontend/src/api/accounting.ts`, `frontend/src/components/accounting/AccountingRuleDialog.vue`, `frontend/src/views/AccountingRulesView.vue`, `frontend/src/i18n/fr.ts`, `tests/integration/test_accounting_rules_api.py` |

**Description** : L'écran des règles comptables passe de lecture seule à CRUD complet réservé aux admins.
- Nouveau schéma `AccountingRuleCreate` ; endpoints `POST /api/accounting/rules/` (201, 409 si doublon) et `DELETE /{id}` (204)
- `PUT /{id}` resserré : trésorier → admin uniquement
- Dialog `AccountingRuleDialog.vue` : formulaire create/edit avec sélecteur de déclencheur (verrouillé en édition), nom, description, priorité, toggle actif, table de lignes comptables éditables
- 26 libellés français + 26 descriptions métier par déclencheur dans `fr.ts`
- La table affiche le libellé lisible du déclencheur et sa description
- Boutons Éditer / Supprimer (avec confirmation) visibles admin uniquement
- 6 nouveaux tests d'intégration (create, doublon 409, create forbidden trésorier, delete, delete 404, delete forbidden trésorier)

---

### REC-009 — Fix vue-i18n SyntaxError 9 au clic sur « Nouvelle règle »

| Champ | Valeur |
|---|---|
| **Type** | `fix` |
| **Date** | 2026-04-25 |
| **Commit** | `4ea32a5` |
| **Fichiers** | `frontend/src/i18n/fr.ts` |

**Description** : L'ouverture du dialog `AccountingRuleDialog` provoquait une `SyntaxError: 9` (erreur de compilation de message vue-i18n). La clé `accounting.rules.entries_subtitle` contenait `{{label}}, {{amount}}, {{date}}` — les doubles accolades sont interprétées comme interpolation vue-i18n v9 et causent un échec du parseur. Reformulation de la chaîne pour éviter tout `{`.

---

## État d'ensemble

| ID | Titre | Type | Commit | Statut |
|---|---|---|---|---|
| REC-001 | Version depuis `pyproject.toml` backend | chore | `5247f2e` | ✅ livré |
| REC-002 | Docker : gdk-pixbuf Debian Trixie | fix | `047b672` | ✅ livré |
| REC-003 | Docker : SPA routing hard-refresh | fix | `01058cd` | ✅ livré |
| REC-004 | Bouton sauvegarde BDD (CHR-019) | feat | `209fb94` | ✅ livré |
| REC-005 | Salaires accessible rôle Management | feat | `992f907` | ✅ livré |
| REC-006 | Version Vite depuis `pyproject.toml` | chore | `d61399b` | ✅ livré |
| REC-007 | Docker : `pyproject.toml` dans builder | fix | `4f19c62` | ✅ livré |
| REC-008 | CRUD règles comptables (admin) | feat | `1fe2274` | ✅ livré |
| REC-009 | Fix vue-i18n SyntaxError 9 — `entries_subtitle` | fix | `4ea32a5` | ✅ livré |
