<!-- markdownlint-disable MD033 -->
# Backlog — Archive (ledger historique) — Solde ⚖️

Ledger consolidé des lots terminés **avant la restructuration en `.backlog/`** :
deep history (avant 2026-05-02) puis lots terminés v1.5 → v1.7.3 repris de l'ancien
`doc/backlog.md`. Les lots récents archivés un par un sont dans ce même dossier
(`RF.md`, `RR.md`, `ML.md`, `BK2.md`). Index : [`../README.md`](../README.md).

---

## Lots terminés

| Lot | Nom | Version | Tickets | Terminé | Est. Copilot | Réel Copilot |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Quick wins P3 | v0.2 | CHR-064, CHR-062, TEC-066, TEC-063 | 2026-04-22 | — | — |
| 2 | Tests au vert | v0.2 | TEC-048 | 2026-04-22 | — | — |
| 3 | Sécurité sans impact structurel | v0.2 | TEC-047, TEC-052, TEC-055, TEC-060, TEC-051 | 2026-04-22 | — | — |
| 4 | Qualité backend sans impact API | v0.2 | TEC-065, TEC-057, TEC-059 | 2026-04-22 | — | — |
| 5 | Sécurité auth (full-stack) | v0.2 | TEC-045, BIZ-053, TEC-046 | 2026-04-22 | — | — |
| 6 | DevOps Docker | v0.2 | CHR-054, CHR-061 | 2026-04-22 | — | — |
| 7 | Refactoring structurel | v0.2 | TEC-050, TEC-058 | 2026-04-22 | — | — |
| 8 | Chantiers longs | v0.2 | BIZ-056, TEC-049 | 2026-04-22 | — | — |
| A | Backend rapide | v0.3 | TEC-085 | 2026-04-23 | — | — |
| B | UX quick wins | v0.3 | BIZ-070, BIZ-072, BIZ-074, BIZ-084, BIZ-042 | 2026-04-23 | — | — |
| C | Dashboard interactif | v0.3 | BIZ-075, BIZ-073 | 2026-04-23 | — | — |
| D | Polish UI | v0.3 | BIZ-071, BIZ-043 | 2026-04-23 | — | — |
| F | Tests | v0.4 | TEC-079, TEC-080, TEC-081 | 2026-04-24 | — | — |
| G | Refactoring frontend | v0.5 | TEC-077 | 2026-04-24 | — | — |
| I | Polish UI & contacts | v0.5 | BIZ-035, BIZ-037, CHR-038, BIZ-040 | 2026-04-24 | — | — |
| J | CI GitHub Actions | v0.5 | CHR-086, CHR-087 | 2026-04-24 | — | — |
| K | Documentation & Swagger | v0.5 | CHR-019, CHR-082 | 2026-04-24 | — | — |
| L | Gestion employés | v0.6 | BIZ-088 | 2026-04-25 | — | — |
| M | Sécurité applicative | v0.6 | TEC-091, TEC-092, TEC-093 | 2026-04-25 | — | — |
| N | UX & formulaires | v0.7 | BIZ-094, BIZ-095, BIZ-096, BIZ-097 | 2026-04-25 | — | — |
| Q | Recette post-merge N | v0.7 | voir doc/recette.md (REC-001..REC-015) | 2026-04-26 | — | — |
| R | Supervision système & audit | v0.8 | BIZ-108, BIZ-109 | 2026-04-26 | — | — |
| O | Qualité technique backend | v0.7 | TEC-098, TEC-099, TEC-100 | 2026-04-26 | — | — |
| P | Qualité technique frontend | v0.7 | TEC-101, TEC-102, TEC-103, TEC-104 | 2026-04-26 | — | — |
| S | Documentation & i18n | v0.8 | TEC-106, CHR-021, CHR-020, CHR-079 | 2026-04-27 | — | — |
| T | Chatbot IA + refactor Paramètres | v1.0 | BIZ-125, BIZ-126 | 2026-04-27 | — | — |
| H-UX | Améliorations UX (lot H) | v1.1 | settings gestionnaires, dialogue paiement, champs famille contacts, date facture, commentaires, PDF règlement, verrou édition | 2026-04-28 | — | — |
| I-BNK | UX Banque | v1.2 | BIZ-133, BIZ-134, BIZ-135, BIZ-136, BIZ-137 | 2026-05-01 | — | — |

Tickets fermés hors lots : TEC-067, TEC-068, BIZ-069, BIZ-076, CHR-083, BIZ-036, BIZ-041, BIZ-033, BIZ-088, BIZ-089, BIZ-090, TEC-105, TEC-039, BIZ-106, BIZ-107, TEC-110, BIZ-108, BIZ-109, BIZ-112, BIZ-113, BIZ-114, BIZ-115, BIZ-116, BIZ-118, BIZ-121, BIZ-117, **BIZ-119**, **BIZ-123**, **BIZ-124**, **BIZ-122**, **BIZ-111**, **BIZ-138**, **BIZ-139**, **BIZ-140**, **BIZ-141**, **TEC-142**, **TEC-143**, **TEC-146**, **TEC-152**, **TEC-153**, **TEC-154**, **BIZ-155**, **BIZ-156**, **BIZ-148**.
Tickets fermés pré-audit : CHR-001, CHR-002, BIZ-003 – BIZ-018, BIZ-022 – BIZ-023.

---

## Détails

<details>
<summary>Lot S — Documentation & i18n (2026-04-27)</summary>

### TEC-106 — Audit et complétion des clés i18n manquantes

Audit complet des 1 096 clés `t('...')` utilisées dans le frontend (1 358 appels bruts filtrés). Résultat : 2 clés manquantes (`common.active`, `common.inactive`) utilisées dans `EmployeesView.vue` — ajoutées dans `fr.ts`.

### CHR-020 — Documentation de contribution

`doc/dev/contributing.md` : setup local, `dev.ps1`, quality gate backend/frontend, conventions Git et workflow. Validé via PR #54.

### CHR-021 — Manuel utilisateur illustré

Manuel FR `doc/user/manuel.md` + référence LLM `doc/llm/reference.md`. Version textuelle complète, structure par rôle et parcours métier. Illustrations (captures annotées) reportées à une future itération.

### CHR-079 — Restructuration et nettoyage de la documentation

Restructuration complète du répertoire `doc/` : nouvelles arborescences `doc/admin/`, `doc/dev/`, `doc/user/`, `doc/llm/` ; suppression de 25 fichiers obsolètes ; README par section ; split des docs bilingues en fichiers par langue (`*.fr.md` / `*.en.md`). Corrections factuelles : `DATABASE_URL`, Vue Router 5, fixtures de test, durée de session, rôles règles comptables, version sync.

</details>

<details>
<summary>Lot T — Chatbot IA + refactor Paramètres (2026-04-28)</summary>

### BIZ-125 — Chatbot IA + page Aide

- **Terminé** : 2026-04-27
- **Livré** : sidebar chatbot flottante (SSE, Gemini/OpenAI), bouton FAB dans AppLayout, annulation, rendu Markdown via `marked` ; page `/aide` affichant `doc/user/manuel.md` en HTML ; panneau admin `SettingsChatPanel` (provider, clé API, modèle) ; backend : endpoints `/api/chat`, `/api/chat/config`, `/api/chat/logs`, `/api/help/manual` ; migrations 0035 (colonnes chat dans `app_settings`) et 0036 (table `chat_log`).

### BIZ-126 — Refactor UX écran Paramètres

- **Terminé** : 2026-04-27
- **Livré** : `SettingsAssociationSmtpPanel.vue` (413 lignes) scindé en `SettingsAssociationPanel.vue` (infos association + facturation) et `SettingsSmtpPanel.vue` (SMTP) ; chaque panneau sauvegarde indépendamment. Réalisé sur la même branche que BIZ-125.

</details>

<details>
<summary>Tickets fermés hors lots — détails (BIZ-111, BIZ-117, BIZ-119, BIZ-122, BIZ-123, BIZ-124)</summary>

### BIZ-111 — Import one-shot adresses postales depuis factures Word

- **Terminé** : 2026-04-26
- **Livré** : script `scripts/import_addresses_from_docx.py` — extrait les adresses postales depuis les factures Word historiques et enrichit `Contact.adresse` (dry-run par défaut, `--commit` pour appliquer). 48 contacts mis à jour. Dépendance `python-docx` ajoutée dans `pyproject.toml`. Amélioration associée : affichage de l'adresse dans le PDF facture + suppression du SIRET en doublon dans la section Émetteur.

### BIZ-117 — Assistant IA intégré

**Clôturé ❌ Non réalisable** — intégration d'un LLM tiers exclue pour raisons de confidentialité des données comptables ; modèle local incompatible avec la contrainte RAM ≤ 384 MB du NAS.

### BIZ-119 — Tableau de bord avec cartes d'actions rapides

- **Terminé** : 2026-04-26
- **Livré** : panneau « Actions rapides » en haut du dashboard — 3 cartes (facture client, paiement, caisse) ouvrant des wizards de saisie inline ; wizard facture client avec confirmation et bouton « Saisir une autre ».

### BIZ-122 — Intégrer description dans l'e-mail de facture

- **Terminé** : 2026-04-26
- **Livré** : paramètre description ajouté à mail_service.send_invoice_email ; si renseigné, l'objet du message devient Facture {numéro} — {description} ; routeur send-email passe invoice.description au service.

### BIZ-123 — Prix par défaut par type de ligne de facture

- **Terminé** : 2026-04-26
- **Livré** : colonnes `default_price_cours`, `default_price_adhesion`, `default_price_autres` sur `AppSettings` (migration 0034) ; section « Prix unitaires par défaut » dans les paramètres ; pré-remplissage automatique au `addLine()` et au changement de `line_type` dans `ClientInvoiceForm` ; correction race-condition (`onMounted` async avant `addLine`).

### BIZ-124 — Templates de numérotation configurables pour les factures

- **Terminé** : 2026-04-26
- **Livré** : `client_invoice_number_template` (`{year}`, `{seq}`) + `client_invoice_seq_digits` + `supplier_invoice_number_template` (strftime) sur `AppSettings` (migrations 0032, 0033) ; service `_next_number` avec regex ; endpoint `GET /api/invoices/next_number` (aperçu sans side-effect) ; affichage du numéro prévu dans le formulaire de création et dans la confirmation du wizard.

</details>

<details>
<summary>Historique des estimations — lots techniques 1-8 (2026-04-22)</summary>

Total estimé initial : ~40h — total révisé : ~55h.
Principaux postes de dérapage : quality gates (~10 min/commit), tests d'intégration, migrations Alembic, refactoring TEC-050.

### Lot 1 — Quick wins P3 — ~45 min

| Ticket | Estimation | Détail |
| --- | --- | --- |
| CHR-064 | 5 min | Supprimer un fichier + vérifier qu'il n'est pas importé |
| CHR-062 | 5 min | Changer une string dans `package.json` |
| TEC-066 | 20 min | Remplacer le pattern `global` par `@lru_cache`, vérifier les tests |
| TEC-063 | 15 min | Remplacer 2 noms dans les fixtures + migration Alembic si nécessaire |

### Lot 2 — Tests au vert (TEC-048) — ~2h

11 échecs dans `excel_import_parsers` / `excel_import_parsing` + 1 erreur API de test. Suite déjà au vert (739/739) après corrections antérieures.

### Lot 3 — Sécurité sans impact structurel — ~4h

| Ticket | Est. initiale | Est. révisée | Temps réel | Détail |
| --- | --- | --- | --- | --- |
| TEC-047 | 30 min | 1h | ~1h15 | Middleware 5 en-têtes + test CSP PrimeVue |
| TEC-052 | 20 min | 30 min | ~40 min | Conditionner endpoint sur `settings.debug` |
| TEC-055 | 20 min | 30 min | ~25 min | Paramètre `cors_allowed_origins` |
| TEC-060 | 30 min | 45 min | ~30 min | Retirer `create_all` de `init_db()` |
| TEC-051 | 50 min | 1h15 | ~50 min | `MAX(entry_number)` + lock + migration |

### Lot 4 — Qualité backend sans impact API — ~6h

| Ticket | Est. initiale | Est. révisée | Temps réel | Détail |
| --- | --- | --- | --- | --- |
| TEC-065 | 1h | 1h30 | ~1h30 | Déplacer attributs transients vers `PaymentRead` |
| TEC-057 | 2h | 2h30 | ~3h30 | `TypeDecorator` Decimal + 63 occurrences |
| TEC-059 | 1h30 | 2h | ~45 min | `limit=100` / `max=1000` sur tous les endpoints |

### Lot 5 — Sécurité auth (full-stack) — ~10h

| Ticket | Est. initiale | Est. révisée | Temps réel | Détail |
| --- | --- | --- | --- | --- |
| TEC-045 | 1h | 1h30 | ~1h | `slowapi` rate limiting sur `/auth/login` |
| BIZ-053 | 2h | 3h | ~1h30 | Migration `must_change_password` + guard |
| TEC-046 | 4h | 5h30 | — | Cookie `HttpOnly` + intercepteur Axios + `/auth/refresh` |

### Lot 6 — DevOps Docker — ~1h30

| Ticket | Est. initiale | Est. révisée | Détail |
| --- | --- | --- | --- |
| CHR-054 | 40 min | 50 min | `entrypoint.sh` avec gestion d'erreur |
| CHR-061 | 20 min | 20 min | `HEALTHCHECK` Docker + docker-compose |

### Lot 7 — Refactoring structurel — ~12h

| Ticket | Est. initiale | Est. révisée | Détail |
| --- | --- | --- | --- |
| TEC-050 | 6h | 9h | Éclater `excel_import.py` (5 038 L) en package |
| TEC-058 | 2h | 1h | Typer les `except Exception` |

### Lot 8 — Chantiers longs

| Ticket | Est. initiale | Est. révisée | Détail |
| --- | --- | --- | --- |
| BIZ-056 | 3-4h | 2h | Table d'audit + middleware + 4 types d'événements |
| TEC-049 | 10-15h | 12-20h | Palier 34 % → 60 % couverture de test |

</details>

<details>
<summary>Détails des sujets fermés — cliquer pour développer</summary>

### CHR-001 — Stabiliser la méthode de triage du backlog

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Livré** : backlog utilisé comme support versionné avec statuts, priorités et mises à jour récurrentes.

### CHR-002 — Documentation utilisateur import/reset

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Livré** : documentation rédigée dans `doc/user/import-excel-et-reinitialisation.md`.

### BIZ-003 — Campagne de retest métier sur imports réels

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Livré** : rejeu réel confirmé sans écart bloquant, procédure ajustée pour exercices/compteurs.

### BIZ-004 — Historique d'import réversible

- **Dates** : `created=2026-04-12`, `started=2026-04-20`, `completed=2026-04-20`
- **Livré** : backend `runs`, `operations`, `effects` réversibles, API cycle `prepare → execute → undo/redo`, UI prévisualisation + historique. Stabilisation rapprochement paiement/facture intra-run.

### BIZ-005 — Politique de coexistence import / écritures existantes

- **Dates** : `created=2026-04-12`, `started=2026-04-19`, `completed=2026-04-19`
- **Livré** : politique explicitée dans `doc/dev/BIZ-005-politique-coexistence-imports.md`, trois diagnostics : `entry-existing`, `entry-covered-by-solde`, `entry-near-manual`.

### CHR-006 — Warnings de dépréciation FastAPI

- **Dates** : `created=2026-04-12`, `started=2026-04-21`, `completed=2026-04-21`
- **Livré** : `HTTP_422_UNPROCESSABLE_ENTITY` → `HTTP_422_UNPROCESSABLE_CONTENT`, zéro warning.

### CHR-007 — Source de vérité backlog vs issues GitHub

- **Dates** : `created=2026-04-12`, `completed=2026-04-13`
- **Livré** : convention actée — `doc/backlog.md` = source de vérité.

### BIZ-008 — Import Excel comme validation itérative de convergence

- **Dates** : `created=2026-04-12`, `started=2026-04-18`, `completed=2026-04-18`
- **Livré** : modes `convergence globale` et `validation moteur Gestion`, preview bidirectionnelle, script `scripts/run_excel_convergence_preview.py`. Documentation dans `doc/dev/BIZ-008-recette-convergence.md`.
- **Détail** : grille de contrôle par domaine (factures, paiements, banque, caisse, comptes pivots), politique d'écarts résiduels, périmètre asymétrique `Solde ↔ Excel` par exercice.

### BIZ-009 — Enrichir le plan comptable par défaut

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Livré** : seed enrichi avec comptes réels, sous-comptes historiques conservés inactifs.

### BIZ-010 — Stratégie de clôture des exercices historiques

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Livré** : exercices historiques ouverts pendant reprise, clôture administrative sans écritures de clôture.

### BIZ-011 — Exercice courant global

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Livré** : store global d'exercice + sélecteur partagé + filtrage métier par défaut.

### BIZ-012 — Liste des paiements : référence et édition

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Livré** : colonne Référence + bouton d'édition par ligne + dialogue `PUT /payments/{id}`.

### BIZ-013 — Journal de caisse : référence, détail et édition

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Livré** : référence visible, panneau de détail, édition directe, recalcul soldes après modification.

### BIZ-014 — Journal comptable : lisibilité et navigation

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Livré** : libellés comptes, références métier, tiers, détail, édition manuelles, navigation factures.

### BIZ-015 — Reset sélectif orienté reprise d'import

- **Dates** : `created=2026-04-13`, `started=2026-04-20`, `completed=2026-04-20`
- **Livré** : reset sélectif par type d'import + exercice avec prévisualisation, UI dans Paramètres, suppression des dépendances métier dérivées.

### BIZ-016 — Harmonisation i18n et microcopie UI

- **Dates** : `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14`
- **Livré** : clés i18n cohérentes sur Banque, Caisse, Salaires (compteurs, états vides, libellés).

### BIZ-017 — Formats de dates et périodes en français

- **Dates** : `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14`
- **Livré** : helper partagé pour mois en français, appliqué sur Salaires et Dashboard mensuel.

### BIZ-018 — Lisibilité des écrans de liste

- **Dates** : `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14`
- **Livré** : socle DataTable partagé (filtres texte/dates/intervalles/multi-sélection, compteurs, tri, saisie date FR/ISO).

### BIZ-022 — Gestion des utilisateurs, rôles et sécurité

- **Dates** : `created=2026-04-13`, `started=2026-04-13`, `completed=2026-04-19`
- **Livré** : cycle de vie complet : rôles métier, administration comptes, profil, changement MDP, réinitialisation admin, invalidation jetons.

### BIZ-023 — Matrice d'autorisations par rôle

- **Dates** : `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14`
- **Livré** : séparation Gestion/Comptabilité dans la navigation, guards frontend par domaine, renommage Gestionnaire/Comptable, permissions backend alignées.

### BIZ-036 — Carte « restant en retard » cliquable

- **Dates** : `created=2026-04-21`, `completed=2026-04-23`
- **Livré** : absorbé par BIZ-075 (KPI dashboard cliquables).

### BIZ-041 — Carte « non remis » cliquable

- **Dates** : `created=2026-04-21`, `completed=2026-04-23`
- **Livré** : absorbé par BIZ-075 (KPI dashboard cliquables).

### BIZ-042 — Bouton reset filtres tables

- **Dates** : `created=2026-04-21`, `completed=2026-04-23`
- **Livré** : bouton reset sur tous les filtres de toutes les tables.

### BIZ-043 — Combos comptes comptables couleur

- **Dates** : `created=2026-04-21`, `completed=2026-04-23`
- **Livré** : combos affichant numéro, nom et couleur des comptes suivis.

### TEC-045 — Rate limiting `/auth/login`

- **Dates** : `created=2026-04-22`, `completed=2026-04-23`
- **Livré** : middleware `slowapi` 5 req/min par IP, bypass configurable pour tests.

### TEC-046 — Refresh token cookie HttpOnly

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : cookie `HttpOnly`/`Secure`/`SameSite=Strict`, endpoint `POST /auth/logout`, intercepteur Axios `withCredentials: true`, 6 tests dédiés.

### TEC-047 — En-têtes de sécurité HTTP

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : middleware CSP, HSTS, X-Content-Type-Options, X-Frame-Options. `dark-mode-init.js` extrait pour CSP `script-src 'self'`.

### TEC-048 — Corriger les tests en échec

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : suite 739/739 au vert. Test API adapté pour `@lru_cache` (TEC-066).

### TEC-049 — Remonter la couverture de test

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : +44 tests (812 → 856), couverture 29% → 71%. Services critiques ≥ 90% : accounting_engine 92%, invoice 93%, payment 90%, fiscal_year ~95%, salary ~95%.

### TEC-050 — Refactorer `excel_import.py` en package

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : monolith 5 567 lignes éclaté en 16 sous-modules + `__init__.py` re-export. Aucune dépendance circulaire.

### TEC-051 — Numérotation des écritures thread-safe

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : `COUNT(*)` → `MAX(entry_number)` + lock, migration, tests de concurrence.

### TEC-052 — Désactiver `reset-db` en production

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : endpoint conditionné à `settings.debug`.

### BIZ-053 — Changement MDP obligatoire au premier login

- **Dates** : `created=2026-04-22`, `completed=2026-04-23`
- **Livré** : champ `must_change_password` (migration 0022), middleware 403, redirection frontend, 11 tests intégration + 2 tests frontend.

### CHR-054 — Séparer migrations du démarrage Uvicorn

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : `entrypoint.sh` avec `set -e`, Dockerfile mis à jour avec `ENTRYPOINT`.

### TEC-055 — CORS configurable pour la production

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : paramètre `cors_allowed_origins` dans les settings.

### BIZ-056 — Journal d'audit structuré

- **Dates** : `created=2026-04-22`, `completed=2026-04-23`
- **Livré** : modèle `AuditLog` + service `record_audit` + migration 0023. Événements : auth (login/logout/password), admin (user CRUD, reset_db, selective_reset). 14 tests.

### TEC-057 — TypeDecorator Decimal pour l'ORM

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : `DecimalType(TypeDecorator)` sur toutes les colonnes monétaires, ~63 casts `Decimal(str())` retirés.

### TEC-058 — Typer les exceptions de l'import Excel

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : `ImportFileOpenError`, `ImportSheetError` dans `_exceptions.py`, mapping typé dans routeur. 10 tests ajoutés.

### TEC-059 — Pagination bornée par défaut

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : `limit=100` / `max=1000` sur tous les endpoints de liste. Frontend et tests adaptés.

### TEC-060 — Retirer `create_all` de `init_db()`

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : `create_all` conservé uniquement dans `conftest.py`, Alembic seul en prod.

### CHR-061 — Docker HEALTHCHECK

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : `GET /api/health` (200), `HEALTHCHECK` dans Dockerfile, `healthcheck:` dans docker-compose.

### CHR-062 — Synchroniser les versions frontend / backend

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : `frontend/package.json` aligné sur `0.1.0`.

### TEC-063 — Retirer les noms personnels du plan comptable (RGPD)

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : noms remplacés par `Client litigieux 1/2`. Seed ne touche pas les données existantes.

### CHR-064 — Supprimer `stores/counter.ts`

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : fichier supprimé, aucune référence dans le code.

### TEC-065 — Éliminer `__allow_unmapped__` de Payment

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : attributs transients déplacés vers `PaymentRead` via `_to_payment_read()`.

### TEC-066 — Settings singleton `@lru_cache`

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : `@lru_cache(maxsize=1)` sur `get_settings()`, variable globale supprimée.

### TEC-067 — Gestionnaire d'erreurs global FastAPI

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : middleware `UnhandledExceptionMiddleware` → JSON 500 `{"detail": ..., "code": "INTERNAL_SERVER_ERROR"}`, log serveur. 5 tests.

### TEC-068 — Désactiver Swagger/ReDoc en production

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : `docs_url`, `redoc_url`, `openapi_url` conditionnés à `cfg.debug`.

### BIZ-069 — Endpoint de sauvegarde SQLite

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : `POST /api/settings/backup` avec `sqlite3.backup()` + rotation 5 fichiers.

### BIZ-070 — Page 404 dédiée

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : `NotFoundView.vue` avec icône, titre i18n, bouton retour. Catch-all router remplacé.

### BIZ-071 — Skeleton loaders

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : `<Skeleton>` PrimeVue sur les écrans de liste principaux.

### BIZ-072 — Fil d'Ariane (Breadcrumb)

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : composable `useBreadcrumb` + `<Breadcrumb>` PrimeVue via meta routes `label`/`breadcrumbParent`.

### BIZ-073 — Raccourcis clavier

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : composable `useKeyboardShortcuts` (Ctrl+N, Ctrl+S, Escape).

### BIZ-074 — Bandeau connexion perdue

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : composable `useNetworkStatus` + `AppOfflineBanner.vue` (events online/offline + intercepteur Axios).

### BIZ-075 — Dashboard KPI cliquables

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : KPI cliquables vers listes filtrées. Complète BIZ-036 et BIZ-041.

### BIZ-076 — Styles d'impression comptable

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : `@media print` sur journal, balance, grand livre, bilan, résultat. Sidebar/filtres/boutons masqués, en-tête imprimable.

### TEC-079 — Tests composables frontend

- **Dates** : `created=2026-04-23`, `completed=2026-04-24`
- **Livré** : 15 tests Vitest — `useDarkMode` (4), `useTableFilter` (8), `activeFilterLabels` (10). Suite 126/126 au vert.

### TEC-080 — Smoke test E2E Playwright

- **Dates** : `created=2026-04-23`, `completed=2026-04-24`
- **Livré** : `playwright.config.ts` (webServer auto-start, DB E2E dédiée). Smoke test : login → MDP obligatoire → dashboard → contacts → factures → paiements.

### TEC-081 — Tests d'intégration API manquants

- **Dates** : `created=2026-04-23`, `completed=2026-04-24`
- **Livré** : `test_accounting_rules_api.py` (11), `test_fiscal_year_api.py` (10), `test_salary_api.py` (+7), `test_dashboard_api.py` (+1). 52 tests intégration au vert.

### CHR-083 — Guide de migration Synology

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : guide FR+EN dans `doc/user/` couvrant mise à jour Docker, vérification post-migration, rollback.

### BIZ-084 — Notification expiration session

- **Dates** : `created=2026-04-23`, `completed=2026-05-03`
- **Livré** : composable `useSessionExpiry` (décode expiry JWT, avertissement T−5 min) + `AppSessionWarning.vue` avec bouton « Prolonger la session ».

### TEC-085 — Politique de complexité MDP

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : validateur `_validate_password_complexity` (8 chars, majuscule, chiffre). 14 tests unitaires.

</details>

---

## Lots terminés récents (v1.5 → v1.7.3) — repris de l'ancien backlog.md

| Lot | Nom | Version | Tickets | Terminé | Est. Copilot | Réel Copilot |
| --- | --- | --- | --- | --- | --- | --- |
| UX2 | Corrections UX contacts & factures | v1.7.3 | BIZ-203, BIZ-204, BIZ-205 | 2026-05-14 | ~110 min | — |
| FW | Import Word + Archivage + Export Excel | v1.7.2 | BIZ-190→197, TEC-192, CHR-194 | 2026-05-12 | ~395 min | ~2h50 |
| BK | Backup automatique | v1.7 | BIZ-173→184, BIZ-187, BIZ-188, BIZ-189 | 2026-05-11 | ~4h40 | ~2h+ (partiel) |
| TEC-185/BIZ-186 | Fix Chrome PDF + filigrane Payé | v1.6.3 | TEC-185, BIZ-186 | 2026-05-10 | ~40 min | — |
| REV2 | Refactoring technique différé | v1.6.2 | TEC-170, TEC-171, TEC-173 | 2026-05-07 | ~55 min | — |
| REV | Revue de code technique | v1.6.1 | TEC-160–165, 167–169, 172 (+ TEC-161, 163, 166 déjà faits) | 2026-05-06 | ~190 min | ~70 min |
| BIZ-172 | Paiements chèques incohérents | v1.6 | BIZ-172 | 2026-05-05 | ~45 min | — |
| BIZ-171 | Améliorations factures mobile | v1.6 | BIZ-171 | 2026-05-05 | ~35 min | — |
| BIZ-170 | Gestion bordereaux en attente | v1.6 | BIZ-170 | 2026-05-05 | ~60 min | ~45 min |
| BIZ-034 | Support multi-compte banque + bugfixes comptables | v1.5 | BIZ-034, fix virement, fix journal filtré, fix fiscal_year_id manuel | 2026-05-04 | — | — |
| CR2 | Correctifs & finitions post-MOB | v1.5 | TEC-157, TEC-158, TEC-159, BIZ-165, BIZ-166, BIZ-167, BIZ-168, CHR-078 | 2026-05-04 | ~95 min | ~30 min |
| Wizard | Wizard factures & Contacts | v1.2 | BIZ-144, BIZ-145, BIZ-147, BIZ-151 | 2026-05-02 | — | — |
| CR | Correctifs revue de code | v1.3.1 | TEC-133, TEC-134, TEC-135, TEC-136, TEC-137, TEC-138, TEC-139, TEC-140, TEC-141, TEC-155 | 2026-05-02 | — | — |
| DOC | Documentation utilisateur | v1.5 | BIZ-161, BIZ-162, BIZ-163 | 2026-05-03 | ~115 min | ~45 min |
| UI | Améliorations UI & saisie | v1.4 | BIZ-149, BIZ-150, BIZ-157, BIZ-158 | 2026-05-03 | ~65 min | ~30 min |
| MOB | Mode téléphone | v1.5 | BIZ-164 | 2026-05-03 | ~90 min | — |

<details>
<summary>Lot BK — Backup automatique (2026-05-11)</summary>

| Ticket | Titre | Est. | Réel |
| --- | --- | --- | --- |
| BIZ-173 | Migration Alembic + modèle BackupDestination | ~15 min | ~7 min |
| BIZ-174 | Schemas Pydantic backup | ~10 min | ~5 min |
| BIZ-175 | Service rclone (backup_destination_service) | ~25 min | ~9 min |
| BIZ-176 | Dockerfile — installation rclone | ~5 min | ~3 min |
| BIZ-177 | Scheduler APScheduler + lifespan main.py | ~30 min | ~14 min |
| BIZ-178 | Service restore (test-restore + restore distante) | ~15 min | ~9 min |
| BIZ-179 | Router backup.py (12 endpoints) | ~35 min | ~19 min |
| BIZ-180 | Frontend api/backup.ts | ~10 min | ~7 min |
| BIZ-181 | Frontend SettingsBackupPanel.vue | ~45 min | ~16 min |
| BIZ-182 | Frontend SettingsView + i18n fr/en | ~15 min | n/m |
| BIZ-183 | Tests unitaires backend | ~15 min | n/m |
| BIZ-184 | Tests intégration API backup | ~20 min | n/m |
| BIZ-187 | Type planification quotidien (HH:MM) + option snapshot-only | ~35 min | n/m |
| BIZ-188 | Option inclure tous les backups précédents | *(inclus BIZ-187)* | n/m |
| BIZ-189 | Fix : spinner visible si backup auto déclenché page ouverte | ~15 min | n/m |
| PR review (Copilot) | Corrections commentaires revue | — | ~35 min |
| **Total** | | **~4h40** | **~2h04 mesurés** (6 tickets n/m) |

</details>

<details>
<summary>Lot REV — Revue de code technique (2026-05-06)</summary>

| Ticket | Titre | Est. | Réel | Note |
| --- | --- | --- | --- | --- |
| TEC-160 | Fix race condition entry_number | ~15 min | ~10 min | Migration + unique index + retry |
| TEC-161 | Masquer clés API/SMTP | ~15 min | ~2 min | Déjà traité (schema excluait déjà les champs) |
| TEC-162 | Frontend .catch vides | ~30 min | ~8 min | 11 occurrences → console.error |
| TEC-163 | Optimiser fonds mensuels | ~20 min | ~2 min | Déjà efficace (2 queries, pas N) |
| TEC-164 | Rendre next_entry_number public | ~5 min | ~2 min | Fusionné avec TEC-160 |
| TEC-165 | max_length mot de passe | ~5 min | ~2 min | +2 lignes |
| TEC-166 | Tests accounting_engine | ~45 min | ~3 min | Tests déjà existants (8 classes) |
| TEC-167 | Allocation batch numéros | ~15 min | ~8 min | next_entry_numbers + refacto apply |
| TEC-168 | Cache Jinja2 Environment | ~5 min | ~2 min | @lru_cache |
| TEC-169 | max_length schemas bank | ~20 min | ~8 min | Field(max_length=…) |
| TEC-172 | CSRF X-Requested-With | ~15 min | ~8 min | Header check + frontend + tests |
| — | Quality gate + fixes | — | ~15 min | ruff, mypy, pytest, eslint, vue-tsc, vitest |
| **Total** | | **~190 min** | **~70 min** | Ratio 0,37 |

</details>

| Ticket | Titre | Est. | Réel |
| --- | --- | --- | --- |
| TEC-157 | i18n AppMobileCardList + CashView | ~10 min | ~3 min |
| TEC-158 | Tests intégration suggest_cheque_number (5 tests) | ~20 min | ~5 min |
| TEC-159 | Tests cheque_number_template settings API (4 tests) | ~15 min | ~4 min |
| BIZ-165 | Navigation prev/next preview factures client | ~10 min | ~5 min |
| CHR-078 | Squelette i18n anglais (en.ts) | ~15 min | ~3 min |
| CR-077 | Corrections revue Copilot PR #77 (8 threads) | ~25 min | ~20 min |
| **Total** | | **~95 min** | **~36 min** |

### Détail

- **TEC-157** : `AppMobileCardList.vue` — prop `emptyMessage` default migré vers `t('common.empty')` + import `useI18n`. `CashView.vue` — `'Écart :'` remplacé par `t('cash.count_diff')`. Clé `common.empty: 'Aucune donnée.'` ajoutée dans `fr.ts`.
- **TEC-158** : 5 tests dans `test_payments_api.py` : statut 200, string non vide, pas de date → aujourd'hui, incrément après un chèque existant, 401 sans auth, 403 readonly.
- **TEC-159** : 4 tests dans `test_settings_api.py` (dans `TestUpdateSettings`) : valeur par défaut `{date}.{seq}`, update valide, 422 sans `{seq}`, 422 avec placeholder inconnu.
- **BIZ-165** : `ClientInvoicesView.vue` — `historyIndex` ref, `openHistory` indexe dans `displayedInvoices`, barre nav ◀ N/total ▶ dans le dialog, `goToPrevHistory` / `goToNextHistory`, styles `.preview-nav-bar`.
- **CHR-078** : `frontend/src/i18n/en.ts` créé — sections `app`, `auth`, `common` traduits en anglais. Enregistré dans `index.ts` (messages: `{ fr, en }`).
- **CR-077** : Corrections des 8 threads de revue Copilot sur PR #77 — CSS dupliqué supprimé (`SupplierInvoicesView`), fuite Blob URL corrigée (`ClientInvoicesView`), bouton créance douteuse restreint à `type === 'client'` (`ContactHistoryContent`), commentaire `en.ts` corrigé, tests `suggest_cheque_number` renforcés (format exact + date today), 4 tests Vitest nav prev/next ajoutés (client + fournisseur). Version 1.4.7 → 1.4.8.

</details>

<details>
<summary>Lot MOB — Mode téléphone (2026-05-03)</summary>

| Ticket | Titre | Est. | Réel | Écart |
| --- | --- | --- | --- | --- |
| BIZ-164 (mobile) | Vues cartes + composant + breakpoint | ~50 min | — | — |
| BIZ-164 (depot) | Tuile dépôt espèces redesignée | ~15 min | — | — |
| BIZ-164 (stat) | Stat cards 2 colonnes mobile | ~5 min | — | — |
| BIZ-164 (cheque) | Suggestion auto n° chèque | ~20 min | — | — |
| **Total** | | **~90 min** | **—** | **—** |

### BIZ-164 — Mode téléphone & UX mobile
Migration Alembic `0049` : `cheque_number_template` dans `app_settings`. Endpoint `GET /api/payments/suggest_cheque_number`. Service `suggest_cheque_number` dans `settings.py`. Auto-suggestion dans `ClientInvoicesView`, `SupplierInvoicesView`, `QuickPaymentWizard`. Champ configurable dans `SettingsAssociationPanel`. Vues cartes mobile sur **toutes les listes** via `AppMobileCardList` (générique `T`) + `useBreakpoints` : Factures client/fournisseur (historiques), Contacts, Banque (transactions + dépôts), Règlements, Caisse, Salaires (3 tables), Employés, Comptabilité (Comptes, Balance, Bilan, Résultat, Règles, Journal, Grand-livre), Exercices, Utilisateurs. Dialogs full-width mobile. Stat grid 2 colonnes mobile.

</details>

<details>
<summary>Lot UI — Améliorations UI & saisie (2026-05-03)</summary>

| Ticket | Titre | Est. | Réel | Écart |
| --- | --- | --- | --- | --- |
| BIZ-158 | Limite API 1000 items + warning | ~30 min | ~18 min | −12 min |
| BIZ-149 | Auto-capitalisation intitulés facture | ~15 min | ~2 min | −13 min |
| BIZ-150 | Accepter la virgule comme séparateur décimal | ~10 min | ~7 min | −3 min |
| BIZ-157 | Pagination 50 items par défaut | ~10 min | ~3 min | −7 min |
| **Total** | | **~65 min** | **~30 min** | **−35 min** |

### BIZ-158 — Limite API 1000 items + warning si atteinte
`default=1000, le=1000` sur 6 routeurs (`invoice.py`, `payment.py`, `contact.py`, `bank.py` transactions + dépôts, `salary.py`). Bandeau `Message` PrimeVue severity `warn` dans chaque vue liste quand le résultat atteint 1 000 items. 4 tests mis à jour (renommage + assertions). Correction d'un bug de docstring introduit en cours de session.

### BIZ-149 — Auto-capitalisation des intitulés facture
Déjà implémenté (`@blur="capitalizeFirstLetter(line)"` dans `ClientInvoiceForm.vue`) — vérification rapide, ticket fermé.

### BIZ-150 — Accepter la virgule comme séparateur décimal
Champs `quantity` et `unit_price` dans `ClientInvoiceForm.vue` : `type="text" inputmode="decimal"` + fonction `normalizeDecimalInput()` (remplace `,` par `.` à la saisie, met à jour le modèle via `parseFloat`).

### BIZ-157 — Pagination 50 items par défaut
`:rows="50"` dans tous les composants Vue (anciennement 20). Remplacement global dans `frontend/src/`.

</details>

<details>
<summary>Lot CR — Correctifs revue de code (2026-05-02)</summary>

### TEC-133 — Access token en mémoire uniquement (XSS)
Token stocké dans un `ref` Pinia non persisté ; rechargement via `POST /api/auth/refresh` (cookie HttpOnly) ; `initFromStorage()` supprimé.

### TEC-134 — Atomicité audit log
`record_audit()` appelé avant `await db.commit()` dans `update_user`.

### TEC-135 — Race condition numérotation factures
Retry loop sur `IntegrityError` (3 tentatives) dans `invoice_service._next_number()`.

### TEC-136 — Chemins relatifs en base
`Invoice.file_path` / `Invoice.pdf_path` stockés en relatif ; résolution absolue uniquement à la lecture via `resolve_file_path()`.

### TEC-137 — Décodage JWT unique
Payload JWT mis en cache dans `request.state.jwt_payload` par le middleware ; `get_current_user` le réutilise.

### TEC-138 — Rate limiter : mémoire bornée
Purge des clés expirées toutes les 100 tentatives dans `rate_limiter.py`.

### TEC-139 — Tokens OpenAI en streaming
`stream_options={"include_usage": True}` + extraction de `chunk.usage` sur le dernier événement SSE.

### TEC-140 — Pagination audit log
`GET /api/settings/audit-logs` : `skip`, `limit`, `action`, `actor_id`, `from_date`, `to_date` ; vue Paramètres mise à jour.

### TEC-141 — Constante `USER_ROLES`
`frontend/src/constants/roles.ts` : source unique pour les chaînes de rôles.

### TEC-155 — Suppression `# type: ignore`
13 suppressions dans `backend/routers/invoice.py` éliminées ; annotations corrigées.

</details>

Tickets fermés hors lots récents : **BIZ-127**, **BIZ-128**, **BIZ-129**, **BIZ-130**, **BIZ-131**, **BIZ-132**, **TEC-156**, **BIZ-198**, **BIZ-199**, **BIZ-200**.

> Lots et tickets plus anciens → [backlog-archive.md](backlog-archive.md)

<details>
<summary>TEC-156 — Fix token auth chat (2026-05-03)</summary>

### TEC-156 — Fix token auth chat (localStorage → Pinia)

`streamChat` dans `api/chat.ts` lisait `localStorage.getItem('access_token')` — toujours `null` car le token est stocké uniquement en mémoire Pinia (mitigation XSS). Chaque `POST /api/chat` retournait 401. Corrigé en lisant `useAuthStore().accessToken`. Découvert lors du test du Lot DOC (2026-05-03).

</details>

<details>
<summary>BIZ-127 — Dialogue confirmation avant envoi e-mail facture (2026-05-02)</summary>

### BIZ-127 — Dialogue de confirmation avant envoi e-mail facture

- **Terminé** : 2026-05-02
- **Livré** : dialog de confirmation avec destinataire (lecture seule), sujet et corps éditables + aperçu PDF ; endpoint `GET /api/invoices/{id}/email-preview` ; `POST /api/invoices/{id}/send-email` accepte payload `{subject, body}` édité par l'utilisateur ; helpers `compose_subject()`/`compose_body()` extraits, `send_invoice_email` accepte `override_subject`/`override_body` ; audit log inclut le sujet ; 8 nouveaux tests unitaires.

</details>

<details>
<summary>BIZ-128 — Modèles d'e-mail configurables (2026-05-02)</summary>

### BIZ-128 — Modèles d'e-mail configurables dans les paramètres

- **Terminé** : 2026-05-02
- **Livré** : colonnes `email_subject_template` et `email_body_template` sur `app_settings` (migration 0037) ; section dédiée dans les paramètres SMTP ; variables `{invoice_number}`, `{description}`, `{association_name}`, `{invoice_ref}` ; `_SafeFormatMap` pour variables inconnues ; 7 nouveaux tests unitaires.

</details>

<details>
<summary>BIZ-130 — Confirmation de dépôt bancaire + métriques espèces/chèques (2026-05-02)</summary>

### BIZ-130 — Confirmation de dépôt bancaire + métriques espèces/chèques

- **Terminé** : 2026-05-02
- **Livré** :
  - Migration Alembic 0038 — colonnes `confirmed` (Boolean, default false) et `confirmed_date` (Date nullable) sur la table `deposits`
  - `bank_service.confirm_deposit()` — marque un dépôt comme confirmé (date = aujourd'hui) ; `list_deposits` accepte filtre `confirmed`
  - Endpoint `POST /api/bank/deposits/{id}/confirm` (write access) + audit log `bank.deposit.confirm`
  - Vue Banque : panneau « Dépôts en attente de confirmation » (visible si ≥ 1 dépôt non confirmé) — résumé nb chèques / nb encaissements + montant + bouton confirmer ; colonne « Statut » dans le tableau des dépôts avec filtre
  - Vue Paiements : deux métriques séparées « Chèques à remettre » et « Espèces à déposer » remplacent le compteur unique « Non remis »
  - 4 nouveaux tests d'intégration (`test_confirm_deposit`, déjà confirmé → 422, non trouvé → 404, filtre confirmed)

</details>

---
