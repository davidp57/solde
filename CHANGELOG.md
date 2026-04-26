# Changelog

<!-- markdownlint-disable MD024 MD036 -->

Toutes les modifications notables apportées à Solde ⚖️ sont documentées ici.

Le format suit [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Ce projet respecte le [Versionnage sémantique](https://semver.org/lang/fr/).

---

## [Non publié]

### Ajouté

- TEC-099 : Contrainte `ON DELETE CASCADE` sur la FK `payments.invoice_id → invoices.id` (migration Alembic `0030_payment_invoice_cascade`) — suppression d'une facture en base entraîne désormais la suppression en cascade des paiements associés, éliminant le risque d'enregistrements orphelins
- TEC-100 : `tests/unit/test_pdf_service.py` — 13 tests couvrant `render_invoice_html` (contenu HTML) et `generate_invoice_pdf` / `save_invoice_pdf` (WeasyPrint mocké via `sys.modules` pour éviter l'import natif GTK)
- TEC-100 : `tests/unit/test_email_service.py` — 11 tests couvrant STARTTLS, SSL, BCC optionnel, sujet du message, et gestion des erreurs SMTP/OS/auth
- TEC-101 : Composable `frontend/src/composables/useInvoiceMetrics.ts` — extrait `receivableMetrics` et `portfolioMetrics` de `ClientInvoicesView.vue`, avec export des helpers purs `remainingForInvoice`, `isOpenReceivableInvoice`, `isOverdueInvoice`
- TEC-102 : Utilitaire `frontend/src/utils/errorUtils.ts` — fonction `getErrorDetail(error, fallback)` qui extrait le message `detail` des erreurs FastAPI structurées
- TEC-103 : Debounce 300 ms sur le filtre global de `ClientInvoicesView.vue` via `globalFilterInput` ref + `setTimeout`/`clearTimeout` natif — évite les re-renders à chaque frappe sur de longues listes

### Modifié

- TEC-098 : `backend/services/accounting_entry_service.py` — suppression de `limit=100_000` ; `get_balance`, `get_resultat`, `get_bilan` utilisent désormais des agrégations SQL (`GROUP BY + SUM`) ; `get_grouped_journal` utilise une pagination SQL réelle (`OFFSET/LIMIT` poussés dans la requête SQLAlchemy, plus de slice Python)
- TEC-098 : `backend/services/export_service.py` — `export_journal_csv` passe `limit=None` pour lever le plafond de 100 000 lignes sans charger en mémoire
- TEC-102 : `BankClientPaymentDialog.vue`, `BankSupplierPaymentDialog.vue`, `BankLinkClientPaymentDialog.vue`, `BankLinkSupplierPaymentDialog.vue` — extraction d'erreur inline remplacée par `getErrorDetail()`
- TEC-104 : `CashView.vue` — type `CashDenomField` dédié élimine le cast `as unknown as Record<string, number>` dans le template ; `CashEntryFormState.date` déclaré `Date | string` élimine les deux casts `as unknown as Date`

### Ajouté

- BIZ-108 : Écran de supervision système (`/system`) — panneau état (version, taille DB, uptime, badge statut), panneau sauvegardes (création + liste), journaux applicatifs (filtres niveau + texte, couleur par niveau, défilement)
- BIZ-109 : Journal d'audit — endpoint `GET /api/settings/audit-logs` et panneau dédié dans l'écran système (tableau horodatage / acteur / action / cible / détail)
- BIZ-108 : Schémas Pydantic `SystemInfoRead`, `BackupFileRead`, `LogEntryRead`, `AuditLogRead` dans `backend/schemas/settings.py`
- BIZ-108 : Endpoints admin `GET /api/settings/system-info`, `GET /api/settings/backups`, `GET /api/settings/logs` avec parsing des fichiers de rotation
- BIZ-108 : Fonctions API TypeScript `getSystemInfoApi`, `listBackupsApi`, `getLogsApi`, `getAuditLogsApi` dans `frontend/src/api/settings.ts`

### Modifié

- Navigation : page « Employés » déplacée de la section Comptabilité vers la section Gestion
- Navigation : ajout de l'entrée « Supervision système » dans la section Administration (admins uniquement)

### Corrigé

- BIZ-108 : Ordre de lecture des fichiers de rotation inversé — `.log.1` (plus récent) était lu après `.log.2` (plus ancien), masquant les entrées récentes
- BIZ-108 : Filtre de niveau des journaux passé côté serveur — le filtre s'applique maintenant avant la limite de 500 lignes, rechargement automatique à chaque changement de filtre
- BIZ-109 : Labels des actions d'audit traduits en français dans l'écran de supervision (clés i18n imbriquées `system.action.*`)
- BIZ-109 : Horodatages affichés en heure locale — SQLite stockant les dates sans suffixe de fuseau, elles étaient interprétées comme heure locale plutôt qu'UTC (décalage −2h)

### Ajouté (fonctionnalités précédentes)

- BIZ-107 : Colonne « Dernière facture » dans le tableau des contacts (référence + date) — enrichissement backend avec sous-requête SQLAlchemy MAX(date) par contact
- BIZ-107 : Historique contact en Dialog centré (au lieu d'une navigation vers une page dédiée) — composant `ContactHistoryContent` partagé entre la vue pleine page et le dialog
- BIZ-107 : `ContactHistoryContent.vue` — composant extrait de `ContactDetailView`, réutilisable via prop `contactId` et événement `contact-loaded`
- BIZ-107 : `ContactHistoryDialog.vue` — enveloppe `ContactHistoryContent` dans un `<Dialog>` PrimeVue avec le nom du contact en titre

### Modifié

- BIZ-107 : `ContactDetailView.vue` — réécrit comme wrapper léger autour de `ContactHistoryContent`
- BIZ-107 : `ContactsView.vue` — bouton historique ouvre le dialog au lieu de naviguer, nouvelle colonne « Dernière facture »

### Corrigé

- TEC-110 (REC-016) : Fix SPA — `index.html` servi avec `Cache-Control: no-store, no-cache, must-revalidate` ; assets hachés `/assets/*` avec `immutable, max-age=1 an`. Élimine l'erreur `TypeError: error loading dynamically imported module` après un rebuild Docker (navigateur chargeait un `index.html` mis en cache référençant des hashes de chunks obsolètes)

 dans la page Paramètres — appelle `POST /api/settings/backup` et déclenche le téléchargement du fichier `.db` avec un nom horodaté (`solde_backup_YYYY-MM-DD-HH-MM-SS.db`) (CHR-019, REC-004)
- `doc/dev/exploitation.md` : section déploiement Portainer / NAS Synology — stack YAML, variables d'environnement, données persistantes, procédure de mise à jour (CHR-019, REC-004)
- Écran Salaires rendu accessible au rôle `secretaire` (Management) en plus des rôles `tresorier` et `admin` (REC-005)
- CRUD complet des règles comptables réservé aux admins : création, modification, suppression avec confirmation ; dialog formulaire avec sélecteur de déclencheur, lignes comptables éditables ; 26 libellés et descriptions métier en français par déclencheur (REC-008)

### Modifié

- `PUT /api/accounting/rules/{id}` : accès resserré de trésorier+admin à **admin uniquement**, cohérent avec `POST /` et `DELETE /{id}` (REC-008)

### Corrigé

- Docker : rechargement direct sur une route Vue retournait 404 — FastAPI sert désormais `index.html` en fallback pour toutes les routes hors `/api/**` (REC-003)
- Docker : `libgdk-pixbuf2.0-0` absent de Debian Trixie remplacé par `libgdk-pixbuf-xlib-2.0-0` — génération PDF WeasyPrint rétablie (REC-002)
- Docker : `pyproject.toml` absent du stage `frontend-builder`, causant un échec de build de l'image (REC-007)
- `.gitattributes` ajouté pour forcer LF sur `entrypoint.sh` et éviter les erreurs de syntaxe shell après checkout Windows (REC-003)

### Technique

- Version de l'application lue depuis `pyproject.toml` via `importlib.metadata` (backend) et regex Vite (frontend) — `APP_VERSION` supprimé de `.env` (REC-001, REC-006)

### UX & Formulaires

- BIZ-094 : Confirmation avant « Recréer le socle comptable » — dialog warn avec annulation (SettingsDangerZonePanel)
- BIZ-095 : Avertissement modifications non sauvegardées sur tous les formulaires — garde `@update:visible` + `onBeforeRouteLeave` (ClientInvoicesView, SupplierInvoicesView, ContactsView, EmployeesView, SalaryView)
- BIZ-096 : Feedback de validation champ par champ — parsing erreurs Pydantic 422 dans ClientInvoiceForm, SupplierInvoiceForm, ContactForm
- BIZ-097 : Accessibilité : `aria-label` sur tous les boutons icône, focus automatique sur le premier champ à l'ouverture des dialogs

### Performances

- TEC-105 : Fix N+1 dans `payment.list_payments()` — Invoice jointe dans la requête principale (1 query au lieu de N+1)
- TEC-105 : Dashboard — filtres `unpaid` et `overdue` déplacés en SQL (`WHERE total_amount > paid_amount`, `WHERE due_date < today`) au lieu d'un chargement en mémoire de toutes les factures
- TEC-105 : Index SQL ajouté sur `invoices.due_date` (migration 0028) — accélère les requêtes de factures en retard

### Sécurité

- TEC-091 : Logging serveur ajouté sur les routeurs `invoice`, `excel_import`, `settings` — les exceptions inattendues sont désormais tracées (`logger.exception`) avant relance
- TEC-092 : Validation du contenu réel des fichiers uploadés par magic bytes (PDF, JPEG, PNG, WebP) dans `upload_invoice_file` — le header `Content-Type` client ne suffit plus
- TEC-093 : Contraintes Pydantic sur les schémas `contact`, `invoice`, `salary`, `payment` — `max_length` sur tous les champs texte libres, `ge=0` sur les montants salaires, validation plage `hours` (0–744)

- `backend/models/contact.py` : enum `ContractType` (CDI/CDD) + 5 nouveaux champs sur `Contact` : `contract_type`, `base_gross`, `base_hours`, `hourly_rate`, `is_contractor` (BIZ-089)
- `backend/models/salary.py` : 3 champs CDD nullable : `brut_declared`, `conges_payes`, `precarite` (BIZ-089)
- `backend/models/invoice.py` : champ `hours` nullable (pour factures AE) (BIZ-089)
- `backend/alembic/versions/0025_add_employee_contract_fields.py` : migration des champs contrat sur la table `contacts` (BIZ-089)
- `backend/alembic/versions/0026_add_salary_cdd_fields.py` : migration des champs CDD sur la table `salaries` (BIZ-089)
- `backend/alembic/versions/0027_add_invoice_hours.py` : migration du champ `hours` sur la table `invoices` (BIZ-089)
- `backend/schemas/salary.py` : `SalaryPreviousRead` (données pré-CEA d'un salaire précédent) et `WorkforceCostRow` (vue coûts du personnel) (BIZ-089)
- `backend/services/salary_service.py` : `get_previous_salary` (dernier salaire d'un employé) et `get_workforce_cost` (consolide CDI + CDD + AE) (BIZ-089)
- `backend/routers/salary.py` : `GET /salaries/previous/{employee_id}` et `GET /salaries/workforce-cost` (BIZ-089)
- `frontend/src/api/contacts.ts` : champs contrat sur `Contact`, `ContactCreate`, `ContactUpdate` (BIZ-089)
- `frontend/src/api/accounting.ts` : champs CDD sur `SalaryRead`/`SalaryCreate` ; nouveaux types `SalaryPreviousRead` et `WorkforceCostRow` ; `getPreviousSalaryApi` et `getWorkforceCostApi` (BIZ-089)
- `frontend/src/views/EmployeesView.vue` : section « Contrat » dans le dialog — type CDI/CDD (conditionne les champs brut de base / taux horaire), flag auto-entrepreneur (BIZ-089)
- `frontend/src/views/SalaryView.vue` : formulaire restructuré en 3 étapes (calcul du brut, saisie CEA, notes) ; calcul automatique CDD (brut déclaré → CP → précarité → brut total) ; bouton « Reprendre le salaire précédent » ; panneau « Coûts du personnel » (CDI + CDD + AE) (BIZ-089)
- `backend/services/excel_import_types.py` : `NormalizedSalaryRow` étendu avec `brut_declared`, `conges_payes`, `precarite` (optionnels) (BIZ-090)
- `backend/services/excel_import_parsers.py` : `parse_salary_sheet` lit désormais les colonnes CDD (cols 2/3/4) du format détaillé de la feuille « Aide Salaires » — les lignes CDD obtiennent leurs 3 champs, les lignes CDI conservent `None` (BIZ-090)
- `backend/services/excel_import/_import_payments_salaries.py` : `_import_salaries_sheet` passe `brut_declared`, `conges_payes`, `precarite` au constructeur `Salary` lors de l'import (BIZ-090)

- `backend/models/invoice.py` : relation ORM `contact` ajoutée sur `Invoice` (nécessaire pour `selectinload` dans `get_workforce_cost`) (BIZ-089)
- `backend/routers/salary.py` : route `GET /salaries/workforce-cost` déplacée avant `GET /salaries/{salary_id}` — Starlette essayait de convertir "workforce-cost" en `int` → 422 (BIZ-089)
- `frontend/src/views/SalaryView.vue` : panneau « Coûts du personnel » refondu en tableau pivoté 5 colonnes (mois, CDI, CDD, Auto-E, total du mois) — agrégation `total_cost` par type par mois (BIZ-089)
- `frontend/src/components/ContactForm.vue` : toggle « Auto-entrepreneur / prestataire » (`is_contractor`) ajouté dans le formulaire contact — permet de marquer un fournisseur comme auto-E pour l'inclure dans la vue coûts du personnel (BIZ-089)
- `frontend/src/i18n/fr.ts` : clé `common.refresh` ajoutée ; `workforce_col_total` ajouté ; libellé `workforce_type_ae` abrégé en "Auto-E" (BIZ-089)

- `backend/models/contact.py` : valeur `EMPLOYE = "employe"` ajoutée à `ContactType` — les employés sont désormais des contacts d'un sous-type dédié (BIZ-088)
- `backend/alembic/versions/0024_add_employe_contact_type.py` : migration documentant la nouvelle valeur enum (colonne `VARCHAR(20)`, pas de DDL) (BIZ-088)
- `frontend/src/views/EmployeesView.vue` : nouvel écran de gestion des employés — liste (filtrable par nom/prénom/e-mail/téléphone, toggle actifs/inactifs), création, édition, activation/désactivation (BIZ-088)
- Route `/employees` ajoutée au router Vue, accessible aux rôles `tresorier` et `admin` (BIZ-088)
- Menu de navigation : entrée « Employés » dans la section Comptabilité, avant « Salaires » (BIZ-088)
- `frontend/src/views/SalaryView.vue` : `loadEmployees` filtre désormais sur `type=employe` — seuls les contacts de type employé apparaissent dans la liste de sélection (BIZ-088)

### Corrigé

- `backend/services/excel_import/_import_payments_salaries.py` et `import_reversible.py` : les contacts employés créés lors de l'import Excel utilisent désormais `ContactType.EMPLOYE` au lieu de `FOURNISSEUR` (BIZ-088)

- `doc/user/installation.md` : option A — image pré-construite depuis GHCR (`SOLDE_IMAGE=ghcr.io/davidp57/solde:latest`) et option B — build local ; sections FR + EN (CHR-019)
- `doc/dev/exploitation.md` : nouvelle section « Image deployment options » présentant GHCR vs build local + variable `SOLDE_IMAGE` ; `SWAGGER_ENABLED` ajouté au tableau de configuration (CHR-019, CHR-082)
- `backend/config.py` : paramètre `SWAGGER_ENABLED` — active Swagger UI (`/api/docs`) et ReDoc (`/api/redoc`) indépendamment de `DEBUG` (CHR-082)
- `.env.example` : entrée `SWAGGER_ENABLED=false` documentée (CHR-082)
- `backend/main.py` : `openapi_tags` avec descriptions pour les 12 groupes d'endpoints ; `/api/docs`, `/api/redoc` et `/api/openapi.json` activés si `debug` ou `swagger_enabled` est vrai (CHR-082)


- `.github/workflows/ci.yml` : workflow CI GitHub Actions (jobs `backend` + `frontend`) — ruff check + format, mypy, pytest sur toutes les branches actives ; ESLint, vue-tsc, vitest sur le frontend (CHR-086)
- `.github/workflows/docker.yml` : workflow Docker — build multi-stage + push image `ghcr.io/davidp57/solde` sur push `main` avec tags `latest` + `sha-<short>` et cache GitHub Actions (CHR-087)
- `docker-compose.yml` : commentaire indiquant comment substituer le `build:` par `image: ghcr.io/davidp57/solde:latest` pour déploiement NAS sans rebuild local (CHR-087)

- `frontend/src/views/ContactsView.vue` : onglets Tous / Clients / Fournisseurs via `Tabs` PrimeVue — filtrage frontend (`les_deux` visible dans les deux onglets), remplacement du `Select` type par les onglets (BIZ-035)
- `POST /api/contacts/import-emails` : endpoint d'import d'e-mails en masse pour enrichir les contacts existants par correspondance sur le nom (normalisation des accents, matching prénom+nom et nom seul) — schémas `ContactEmailImportRow` / `ContactEmailImportResult`, 9 nouveaux tests (BIZ-040)
- `frontend/src/views/ContactsView.vue` : bouton « Importer e-mails » + dialogue avec zone de texte collée (`Nom, email` par ligne) + affichage du bilan (mis à jour / non trouvés / déjà renseignés) (BIZ-040)
- `frontend/src/layouts/AppLayout.vue` : nom d'utilisateur (sidebar et topbar) cliquable via `RouterLink` vers `/profile` — suppression de l'entrée « Mon profil » du menu de navigation (BIZ-037)
- `frontend/src/layouts/AppLayout.vue` : numéro de version discret en bas de la sidebar, injecté depuis `package.json` via `vite.config.ts` `define.__APP_VERSION__` (CHR-038)

- `frontend/src/tests/composables/useDarkMode.spec.ts` : tests unitaires Vitest pour le composable `useDarkMode` — toggle, persistance dans localStorage, classe CSS `dark-mode` (TEC-079)
- `frontend/src/tests/composables/useTableFilter.spec.ts` : tests unitaires Vitest pour `applyFilter` et `useTableFilter` — filtrage par sous-chaîne insensible à la casse, réactivité, cas limites null/undefined (TEC-079)
- `frontend/src/tests/composables/activeFilterLabels.spec.ts` : tests unitaires Vitest pour `findSelectedFilterLabel` et `collectActiveFilterLabels` — matching, valeurs nulles, types numériques (TEC-079)
- `frontend/e2e/smoke.spec.ts` : smoke test E2E Playwright couvrant login → changement de mot de passe obligatoire → dashboard → contacts → factures clients → paiements (TEC-080)
- `frontend/playwright.config.ts` : configuration Playwright avec webServer auto-start (backend Uvicorn + frontend Vite) et DB E2E dédiée (TEC-080)
- `tests/integration/test_accounting_rules_api.py` : tests d'intégration complets pour l'API des règles comptables — CRUD, seed, auth, rôles (TEC-081)
- `tests/integration/test_fiscal_year_api.py` : tests d'intégration pour les endpoints pre-close-checks, open-next, close 404, auth/rôles (TEC-081)
- `tests/integration/test_salary_api.py` : tests complémentaires — get by id, update, delete not found, accès trésorier (TEC-081)
- `tests/integration/test_dashboard_api.py` : test d'authentification pour le graphique ressources (TEC-081)

- `frontend/src/components/ui/AppTableSkeleton.vue` : composant de skeleton réutilisable (grille de cellules PrimeVue `Skeleton`, props `rows`/`cols` avec valeurs par défaut 8×4) remplaçant les `ProgressSpinner` dans toutes les vues de liste au premier chargement (BIZ-071)
- `frontend/src/components/ui/AppAccountSelect.vue` : composant combo comptes comptables avec point coloré pour les 5 comptes de suivi (créances membres, fournisseurs, caisse, courant, chèques à déposer) via `AppAccountSelect` wrappant PrimeVue `Select` avec slots `#option` et `#value` (BIZ-043)
- `frontend/src/assets/main.css` : classes globales `.app-table-skeleton`, `.app-table-skeleton__row`, `.account-select-option`, `.account-select-dot` et variantes couleur par compte de suivi

### Modifié

- `frontend/src/views/DashboardView.vue` : remplacement du `ProgressSpinner` central par 7 `<Skeleton height="132px">` dans la grille KPI au chargement — cohérence visuelle avec le layout final (BIZ-071)
- `frontend/src/views/AccountingBilanView.vue` : remplacement du `ProgressSpinner` par `AppTableSkeleton :rows="10" :cols="3"` (BIZ-071)
- `frontend/src/views/ContactDetailView.vue` : remplacement du `ProgressSpinner` par une grille de 3 `Skeleton` de stat + `AppTableSkeleton` (BIZ-071)
- `frontend/src/views/ClientInvoicesView.vue` : skeleton sur la liste principale (`loading && !invoices.length`) et dans le dialogue historique (BIZ-071)
- `frontend/src/views/ContactsView.vue` + `PaymentsView.vue` : skeleton sur liste principale au premier chargement (`loading && !*.length`) (BIZ-071)
- `frontend/src/views/AccountingJournalView.vue` : skeleton liste + filtre compte remplacé par `AppAccountSelect` avec rechargement automatique à la sélection (BIZ-071, BIZ-043)
- `frontend/src/views/AccountingLedgerView.vue` : select compte remplacé par `AppAccountSelect` avec points colorés (BIZ-043)

- `frontend/src/composables/useKeyboardShortcuts.ts` : composable Vue 3 gérant les raccourcis clavier Ctrl/Cmd+N (nouveau), Ctrl/Cmd+S (sauvegarder) et Escape (fermer) avec gestion du focus (Ctrl+N ignoré dans les champs de saisie) et nettoyage automatique au démontage (BIZ-073)
- `frontend/src/components/ui/AppStatCard.vue` : prop optionnelle `to` (route Vue Router) rendant la carte KPI cliquable via `<RouterLink>` avec animation hover et focus-visible accessible (BIZ-075)
- `frontend/src/views/DashboardView.vue` : tous les KPI (solde banque, caisse, factures impayées/en retard, chèques non déposés, exercice courant, résultat) sont désormais cliquables vers les vues filtrées correspondantes (BIZ-075)
- `frontend/src/views/ClientInvoicesView.vue` + `PaymentsView.vue` : support des query params URL (`status=overdue`, `undeposited=1`) pour pré-filtrer les listes depuis le dashboard (BIZ-075)
- `frontend/src/views/ClientInvoicesView.vue` + `ContactsView.vue` : intégration de `useKeyboardShortcuts` pour Ctrl+N / Ctrl+S / Escape dans les vues avec dialogue (BIZ-073)
- `doc/user/migration.md` + `doc/user/migration.en.md` : guide de migration / montée de version bilingue FR + EN pour les déploiements Docker sur Synology NAS — couvre la préparation, la mise à jour, la vérification, le rollback et les bonnes pratiques (CHR-083)
- `frontend/src/assets/print.css` : styles `@media print` pour l'impression des vues comptables (journal, balance, grand livre, bilan, résultat) — masque la sidebar, les filtres et les boutons ; optimise les tables en noir et blanc A4 paysage pour impression AG (BIZ-076)
- `backend/main.py` : middleware ASGI `UnhandledExceptionMiddleware` interceptant toutes les exceptions non gérées pour renvoyer un JSON structuré `{"detail": ..., "code": "INTERNAL_SERVER_ERROR"}` au lieu d'un 500 HTML avec stack trace — log complet côté serveur (TEC-067)
- `backend/main.py` : `/api/docs`, `/api/redoc` et `/api/openapi.json` désormais désactivés quand `debug=False` — réduit la surface d'attaque en production (TEC-068)
- `backend/services/backup_service.py` + `POST /api/settings/backup` : endpoint admin de sauvegarde SQLite utilisant `sqlite3.backup()` avec rotation automatique (5 derniers backups), téléchargement direct du fichier en réponse (BIZ-069)
- `backend/schemas/auth.py` : politique de complexité de mot de passe — minimum 8 caractères, au moins une majuscule et un chiffre, appliquée sur la création utilisateur, le changement et le reset de mot de passe (TEC-085)

**Qualité / Sécurité (audit 2026-04-22)**

- `backend/routers/auth.py` : le refresh token est désormais transmis via un cookie `HttpOnly`, `Secure`, `SameSite=Strict` au lieu du corps JSON — `/auth/login` et `/auth/refresh` posent le cookie, nouvel endpoint `POST /auth/logout` (204) l'efface (TEC-046)
- Frontend : `refreshApi()` et `logoutApi()` utilisent le cookie automatiquement (`withCredentials: true`), le store auth ne stocke plus le refresh token en `localStorage` (TEC-046)
- `entrypoint.sh` : script d'entrée Docker dédié avec `set -e` — les migrations Alembic échouent explicitement au lieu d'être masquées par le `&&` shell (CHR-054)
- `GET /api/health` : endpoint de health check léger (200, `{"status": "ok"}`) + `HEALTHCHECK` Docker + `healthcheck:` docker-compose pour la supervision Synology (CHR-061)
- `backend/models/user.py` : champ `must_change_password` obligeant l'utilisateur à changer son mot de passe avant d'accéder à l'application — activé au bootstrap admin, à la réinitialisation de mot de passe par un administrateur, et désactivé automatiquement après changement effectif (BIZ-053)
- `backend/main.py` : middleware `MustChangePasswordMiddleware` bloquant (HTTP 403) toute requête API hors `/api/auth/` quand le JWT porte le flag `mcp=True` (BIZ-053)
- Frontend : redirection automatique vers la page Profil avec bannière d'avertissement lorsque `must_change_password` est actif ; le router guard empêche la navigation vers d'autres pages (BIZ-053)
- `backend/config.py` : `get_settings()` utilise désormais `@lru_cache` au lieu d'un pattern `global` mutable — plus idiomatique et thread-safe (TEC-066)
- `backend/main.py` : middleware `SecurityHeadersMiddleware` ajoutant `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security` et `Referrer-Policy` sur toutes les réponses (TEC-047)
- `backend/config.py` : paramètre `cors_allowed_origins` (liste, variable d'environnement `CORS_ALLOWED_ORIGINS`) permettant de configurer explicitement les origines CORS autorisées en production — wildcard `*` seulement en mode debug sans origines configurées (TEC-055)
- `frontend/public/dark-mode-init.js` : script d'initialisation du mode sombre extrait inline vers un fichier statique dédié pour respecter la politique `script-src 'self'` de la CSP (TEC-047)
- Endpoints de liste : paramètre `limit` désormais borné (`default=100`, `le=1000`) sur tous les routers de liste — caisse, banque, paiements, factures, contacts, salaires, écritures — pour limiter le volume de données retourné en une seule requête (TEC-059)
- `backend/models/types.py` : nouveau `TypeDecorator` `DecimalType` (wrapping `Numeric`) garantissant que SQLAlchemy renvoie toujours un `Decimal` pour les colonnes monétaires au lieu d'un `float` SQLite — élimine les quelque 60 casts `Decimal(str(obj.attr))` répartis dans les services (TEC-057)
- `backend/models/payment.py` : suppression de `__allow_unmapped__` et des attributs transients `invoice_number` / `invoice_type` — ces champs sont désormais calculés à la lecture dans `PaymentRead` via une requête ciblée sur `Invoice` (TEC-065)
- `backend/models/audit_log.py` : table `audit_logs` + service `record_audit` + enum `AuditAction` pour le journal d'audit structuré — traçabilité des connexions (succès/échec), déconnexions, changements de mot de passe, création/modification d'utilisateurs, réinitialisations de mot de passe admin, et opérations de reset base. Migration Alembic `0023` (BIZ-056)
- Tests : +44 tests unitaires (812 → 856) pour les services critiques — `fiscal_year_service` (pre_close_checks, report à nouveau), `contact` (historique, créance douteuse), `dashboard_service` (KPIs, alertes, graphiques), `salary_service` (update, filtre par mois), `accounting_rule_service` (CRUD, preview, template). Couverture globale backend ~71 % (TEC-049)

### Refactorisé

- `frontend/src/views/SettingsView.vue` → 24 lignes (depuis 1 077 L) : extraction de `SettingsAssociationSmtpPanel`, `SettingsSystemOpeningPanel`, `SettingsDangerZonePanel` dans `src/components/settings/` (TEC-077)
- `frontend/src/views/BankView.vue` → 917 lignes (depuis 2 215 L) : extraction de 7 composants de dialogue dans `src/components/bank/` — `BankNewTransactionDialog`, `BankImportStatementDialog`, `BankClientPaymentDialog`, `BankLinkClientPaymentDialog`, `BankSupplierPaymentDialog`, `BankLinkSupplierPaymentDialog`, `BankNewDepositDialog` — chaque dialogue est auto-suffisant (chargement interne, émet `@saved`) (TEC-077)
- `frontend/src/views/ImportExcelView.vue` → 1 191 lignes (depuis 2 873 L) : extraction de `ImportExcelFormPanel`, `ImportExcelShortcutsPanel`, `ImportExcelPreviewPanel`, `ImportExcelResultPanel` dans `src/components/import/` — la vue orchestre, les composants gèrent l'affichage et les opérations locales (TEC-077)

**Qualité / Sécurité (audit 2026-04-22)**

- `backend/services/excel_import.py` : monolith de 5 567 lignes éclaté en package `backend/services/excel_import/` avec 16 sous-modules thématiques (`_constants`, `_salary`, `_invoices`, `_loaders`, `_comparison`, `_comparison_loaders`, `_comparison_domains`, `_entry_groups`, `_sheet_wrappers`, `_orchestrator`, `_import_contacts_invoices`, `_import_payments_salaries`, `_import_cash_bank`, `_import_entries`, `_preview_existing`, `_preview_sheets`) — refactoring purement structurel, interfaces publiques inchangées, zéro dépendance circulaire (TEC-050)
- `backend/services/excel_import/_exceptions.py` : introduction de `ImportFileOpenError` et `ImportSheetError` en remplacement des `except Exception` généralisés — `_ImportSheetFailure(RuntimeError)` remplacé par alias vers `ImportSheetError`, orchestrateur avec catch séparés par type, routeur avec mapping HTTP typé (TEC-058)

### Corrigé

**Import — chèques inter-exercices (BIZ-033)**

- `backend/services/excel_import/excel_import_parsers.py` : parsing de la colonne « Encaissé » corrigé — `deposited_idx` ne se résolvait plus sur « Date encaissement » quand « encaisse » est sous-chaîne de ce libellé
- `backend/services/excel_import/_loaders.py` : nouvelle fonction `_load_existing_payments_deposit_map` pour retrouver le statut de remise des paiements existants
- `backend/services/import_reversible.py` : nouvelle opération `update_payment_deposit_status` — lors de l'import d'un fichier ultérieur, un paiement existant avec `deposited=False` est mis à jour vers `deposited=True` au lieu d'être silencieusement ignoré comme doublon exact

**Dashboard — corrections KPI et paiements non remis**

- `backend/services/dashboard_service.py` : KPI « chèques non remis » filtre désormais uniquement les paiements `CLIENT` en `chèque` ou `espèces`, excluant correctement les remises fournisseurs
- `frontend/src/views/ClientInvoicesView.vue` : filtre « en retard » calculé côté client ; limite portée à 1 000 ; `skipDateFilter` actif quand le paramètre URL `status=overdue` est présent
- `frontend/src/views/DashboardView.vue` : carte « Factures impayées » dirige désormais vers la liste avec `?unpaid=1`
- `frontend/src/views/PaymentsView.vue` : la liste des paiements non remis ignore le filtre de période exercice (un chèque inter-exercices peut s'étaler sur deux années)

**Import — bouton import séquentiel de test**

- `frontend/src/components/import/ImportExcelShortcutsPanel.vue` + `ImportExcelView.vue` : bouton « Tout importer dans l'ordre » dans le panneau de raccourcis de test — enchaîne `gestion-2024 → comptabilite-2024 → gestion-2025 → comptabilite-2025` avec fenêtre de comparaison auto-calculée par fichier, toast par étape et arrêt au premier échec

**Qualité / Sécurité (audit 2026-04-22)**

- `frontend/src/stores/counter.ts` : suppression du fichier de scaffolding Vue non utilisé (CHR-064)
- `frontend/package.json` : version alignée sur `0.1.0` pour correspondre au backend (CHR-062)
- `backend/models/accounting_account.py` : remplacement des noms de personnes réelles dans le plan comptable par défaut par des libellés génériques (`Client litigieux 1`, `Client litigieux 2`) — conformité RGPD (TEC-063)
- `tests/integration/test_import_api.py` : adaptation du test `test_test_import_shortcuts_list_and_run_configured_file` pour utiliser `unittest.mock.patch` au lieu d'accéder directement au singleton `_settings` supprimé (TEC-066)
- `backend/routers/settings.py` : endpoint `POST /settings/reset-db` désormais protégé — retourne HTTP 403 si `settings.debug` est `False`, évitant une remise à zéro accidentelle en production (TEC-052)
- `backend/database.py` : suppression de `Base.metadata.create_all` de `init_db()` — le schéma est exclusivement géré par les migrations Alembic ; `init_db()` ne configure plus que les PRAGMAs SQLite (TEC-060)
- `backend/services/accounting_engine.py` : `_next_entry_number` utilise désormais `SELECT MAX(entry_number)` au lieu de `SELECT COUNT(*)` pour éviter les collisions de numéros après suppressions ou imports partiels (TEC-051)

**Documentation projet**

- `README.md` recentré comme point d'entrée synthétique bilingue `FR + EN` avec renvoi vers les guides détaillés
- Nouvelle documentation technique `doc/dev/exploitation.md` rédigée en anglais pour l'exploitation Docker, la configuration, les volumes, les sauvegardes et les opérations courantes
- Nouvelle documentation développeur `doc/dev/contribuer.md` rédigée en anglais pour la mise en route locale, les commandes qualité, les conventions de développement et le workflow de contribution
- Nouvelle documentation utilisateur / installation disponible en `FR + EN` avec index bilingue `doc/user/README.md`, guide d'installation `doc/user/installation.md` et versions anglaises des guides utilisateur déjà rédigés

**Import Excel réversible**

- Journal d'import réversible persistant avec `import_runs`, `import_operations` et `import_effects`
- Nouveaux endpoints API pour préparer, exécuter, annuler et rejouer un import ou une opération unitaire
- Historique des imports dédié dans l'interface, séparé de l'écran de préparation
- Prévisualisation détaillée des opérations préparées, de leurs effets prévus et des données source Excel associées

**Gestion des utilisateurs**

- Documentation de cadrage `doc/dev/gestion-utilisateurs-et-permissions.md` pour clarifier la cible produit des rôles et la matrice simplifiée des permissions
- Administration des comptes réservée à l'administrateur avec liste, création, activation/désactivation et changement de rôle
- Espace `Mon profil` permettant à chaque utilisateur authentifié de consulter son compte, de mettre à jour son e-mail et de changer son mot de passe
- Procédure de réinitialisation d'accès par l'administrateur avec mot de passe temporaire pour le contexte auto-hébergé

**Administration des reprises d'import**

- Reset sélectif de reprise dans `Paramètres` avec prévisualisation puis suppression confirmée d'un périmètre `Gestion` ou `Comptabilite` borné à un exercice
- Plan de suppression construit à partir des traces d'import (`import_logs` legacy et `import_runs` réversibles) et enrichi, côté `Gestion`, par les dépendances métier dérivées créées ensuite dans Solde
- Documentation utilisateur consolidée pour expliquer la place respective de l'historique réversible, du reset sélectif et de la réinitialisation complète

**Frontend — filtre générique**

- Composable `useTableFilter` + `applyFilter` (`composables/useTableFilter.ts`) : filtre client-side fuzzy sur tous les champs d'un tableau
- Champ de recherche générique ajouté dans les 11 écrans avec DataTable : Paiements, Exercices, Règles comptables, Plan comptable, Journal, Balance, Salaires, Factures clients, Factures fournisseurs, Banque (transactions + remises), Caisse (journal + comptages)
- i18n : clé `common.filter_placeholder` → « Rechercher… »

**Frontend — mode sombre**

- `useDarkMode.ts` : watcher déplacé au niveau module (singleton) pour éviter les problèmes de lifecycle component
- `main.css` : `body` reçoit `background: var(--p-surface-ground)` et `color: var(--p-text-color)` avec transition douce
- `index.html` : script inline synchrone pour appliquer la classe `.dark-mode` avant le rendu (suppression du flash blanc au chargement)
- `index.html` : titre corrigé « Solde ⚖️ », `lang="fr"`

**Frontend — système d’interface partagé**

- `AppPage.vue`, `AppPageHeader.vue`, `AppPanel.vue`, `AppStatCard.vue` : primitives communes pour homogénéiser les pages, les en-têtes, les panneaux et les cartes de synthèse
- `main.css` : langage visuel partagé pour les mises en page, les métriques, les en-têtes de contenu et les dialogues de formulaire

### Modifié

**Édition métier des factures, paiements et imports**

- Une facture `sent` non réglée reste modifiable, mais toute modification régénère désormais ses écritures comptables auto-générées au lieu de laisser des écritures obsolètes en base
- Une facture déjà consommée (`paid`, ou plus généralement hors cas `draft` / `sent` non réglée) ne peut plus être modifiée directement via l'API
- Les paiements deviennent quasi immuables après création : seules les corrections mineures sans impact structurel (`référence`, `notes`, `n° de chèque`) restent éditables depuis l'écran `Paiements`, et la suppression standard est désormais bloquée en attendant un vrai flux d'annulation métier
- Le rejeu strict des imports réversibles reste désormais explicitement protégé même après retouche manuelle d'un objet importé via l'API, y compris quand l'instance SQLAlchemy a été expirée entre-temps

**Paiements et trésorerie**

- Les règlements clients en `chèque` et `espèces` se saisissent désormais depuis la facture client et son historique, avec un parcours dédié pour enregistrer date, montant, mode, référence et note
- Le journal `Caisse` affiche explicitement les mouvements issus d'un paiement client, et les bordereaux bancaires filtrent les paiements selon le type de remise choisi

**Authentification et permissions**

- Les rôles techniques existants restent inchangés côté API, mais leur présentation est clarifiée côté produit pour préparer l'administration des comptes sans casser les autorisations existantes

**Outillage**

- `dev.ps1` : remplacement de `Start-Process pwsh` (2 fenêtres séparées) par `Start-Job` — backend et frontend tournent dans la même session PowerShell, Ctrl+C arrête les deux proprement

**Frontend — modernisation de l’interface**

- Refonte des vues principales avec une présentation plus aérée et cohérente : tableau de bord, contacts, détail contact, factures clients et fournisseurs, paiements, banque, caisse, import Excel, exercices, salaires et écrans comptables (journal, balance, grand livre, résultat, bilan, règles, plan comptable)
- Harmonisation des dialogues et formulaires métier avec une structure commune (introduction, sections, aides contextuelles) pour les comptes comptables, contacts, factures, salaires, dépôts bancaires, imports, opérations de caisse et saisie manuelle d’écritures
- L'écran d'import Excel a été réorganisé autour d'une synthèse courte, d'onglets dédiés (`Détails`, `Synthèse complète`, `Avertissements`) et d'une table d'opérations filtrable

**Frontend — mode sombre (dark mode)**

- `AppLayout.vue`, `LoginView.vue`, `NavMenu.vue`, `SettingsView.vue` : fonds et couleurs rendus réactifs via `v-bind()` CSS couplé à des `computed` Vue (les tokens `--p-surface-N` du thème Aura sont absolus, non réactifs au mode)
- `AppLayout.vue` : suppression de l'en-tête de sidebar « ⚖️ Solde ⚖️ » (redondant avec le titre de la page)
- `NavMenu.vue` : couleur et fond de l'élément de navigation actif adoucis en dark mode (`rgba(52,211,153,0.12)` + texte `primary-300`)
- `SettingsView.vue` : fond de la « Zone de danger » adouci en dark mode (`rgba(239,68,68,0.08)`)

### Corrigé

**Paiements et trésorerie**

- Un règlement en `espèces` crée désormais immédiatement une entrée en caisse, tandis que la remise d'espèces en banque sort explicitement la somme de la caisse au moment du dépôt
- Un règlement par `chèque` reste en attente d'une remise manuelle en banque au lieu d'être assimilé à un dépôt automatique

**Backend**

- invalidation des anciens jetons JWT après changement ou réinitialisation de mot de passe pour éviter qu'une ancienne session reste active
- `excel_import.py` : support des feuilles Caisse (`caisse`/`cash`) et Banque (`banque`/`bank`/`relev`) dans l'import Excel de gestion ; déduplication des numéros de factures dans le même batch ; création automatique du contact si absent (plutôt que saut de ligne silencieux)
- sécurité et robustesse revues après commentaires de PR : secret JWT obligatoire hors dev/test, conversion propre des erreurs d'édition manuelle en réponses HTTP, metadata Alembic complétée pour l'autogénération
- factures clients mixtes `cs+a` : quand la feuille `Factures` expose des montants distincts `cours` et `adhésion`, l'import historique crée les lignes de facture correspondantes et la génération comptable ventile désormais les produits sur les comptes dédiés au lieu d'un seul produit global
- import réversible BIZ-004 stabilisé : un paiement préparé peut maintenant se rapprocher d'une facture du même classeur déjà planifiée dans le run, même si l'ordre des onglets est défavorable, et l'exécution facture/paiement ne déclenche plus d'erreurs async sur les snapshots enregistrés

**Frontend — bugfixes interface**

- `index.html` : correction de `<\/script>` → `</script>` (artefact d'échappement introduit lors de la création du fichier)
- `main.ts` : enregistrement de `ConfirmationService` manquant — toutes les views utilisant `useConfirm()` (Contacts, Factures, Paiements, Exercices, Salaires) crashaient au chargement
- `DashboardView.vue` : imports PrimeVue manquants (`Card`, `ProgressSpinner`, `Message`, `Select`) — la vue du tableau de bord était vide
- `AccountingBilanView.vue` : imports PrimeVue manquants (`Button`, `Card`, `Column`, `DataTable`, `ProgressSpinner`, `Select`) — la vue était vide
- `api/client.ts` : `baseURL` corrigé de `/api` à `''` — les appels API généraient des URLs en double (`/api/api/...`)
- `api/client.ts` : la file d'attente de refresh JWT propage désormais aussi les échecs, évitant des requêtes pendantes infiniment en cas de refresh refusé
- `api/bank.ts`, `api/cash.ts`, `api/payments.ts` : préfixe `/api/` ajouté aux chemins (cohérence avec le nouveau `baseURL`)
- `i18n/fr.ts` : clés `user.role.*` corrigées en minuscules (`admin`, `tresorier`, `secretaire`, `readonly`) pour correspondre aux valeurs renvoyées par le backend

### Ajouté

**Backend (Phase 7 — Complétion du plan)**

- `ContactHistory` schéma + `get_contact_history()` service + `GET /contacts/{id}/history`
- `POST /contacts/{id}/mark-douteux` : génère les écritures 411xxx → 416xxx pour créances douteuses
- `BilanRead` schéma + `get_bilan()` service + `GET /accounting/entries/bilan` : bilan simplifié actif/passif
- `export_service.py` : `export_journal_csv`, `export_balance_csv`, `export_resultat_csv`, `export_bilan_csv` (UTF-8 BOM, séparateur `;`, montants en format fr)
- 4 endpoints `GET /accounting/entries/{journal,balance,resultat,bilan}/export/csv`
- `PreviewResult` + `preview_gestion_file` + `preview_comptabilite_file` dans `excel_import.py` (dry-run sans DB)
- `POST /import/excel/{gestion,comptabilite}/preview` : estimation du nombre de lignes avant import
- `RulePreviewRequest/Entry` schémas + `preview_rule()` service (simulation sans commit)
- `POST /accounting/rules/{id}/preview` : prévisualisation des écritures générées par une règle
- `parse_ofx()` + `parse_qif()` dans `bank_import.py` (SGML/XML OFX, multi-format dates QIF)
- `POST /bank/transactions/import-ofx` + `import-qif`
- `Dockerfile` : ajout des bibliothèques WeasyPrint (pango, cairo, gdk-pixbuf)
- 19 nouveaux tests (5 fichiers) — 342 tests au total

**Frontend (Phase 7)**

- `accounting.ts` : types `BilanRead`, `ContactHistory`, `RulePreviewEntry`, `PreviewResult` + fonctions `getBilanApi`, `getExportCsvUrl`, `getContactHistoryApi`, `markCreanceDouteuse`, `previewRuleApi`, `previewGestionFileApi`, `previewComptabiliteFileApi`, `importOFXApi`, `importQIFApi`
- `AccountingBilanView.vue` : bilan actif/passif avec filtre exercice + bouton export CSV
- `ContactDetailView.vue` : fiche contact avec historique factures/paiements + action mark-douteux
- `ContactsView.vue` : bouton historique (pi-history) vers la fiche contact
- `AccountingJournalView.vue` : bouton export CSV journal
- `ImportExcelView.vue` : bouton preview (dry-run) avant import
- Router : routes `/accounting/bilan` et `/contacts/:id/history`
- NavMenu : entrée Bilan (pi-chart-line)
- i18n `fr.ts` : clés `bilan.*`, `contact_history.*`, `rule_preview.*`, `bank_import.*`, `import.preview*`

**Backend (Phase 6 — Fonctions avancées)**

- Modèle `Salary` + migration `0010` : salaire mensuel par employé (brut, charges salariales/patronales, PAS, net, total_cost)
- Schémas `SalaryCreate/Update/Read` (validateur YYYY-MM) + `SalarySummaryRow`
- `salary_service.py` : CRUD + `get_monthly_summary` + hook `generate_entries_for_salary`
- Router `/api/salaries` : GET / POST /{id} PUT /{id} DELETE /{id} GET /summary
- `TriggerType` enrichi : `SALARY_GROSS`, `SALARY_EMPLOYER_CHARGES`, `SALARY_PAYMENT` ; 3 règles par défaut ajoutées (641000/421000, 645100/431100, 421000/512100)
- `generate_entries_for_salary` dans `accounting_engine.py` : 3 jeux d'écritures automatiques
- `fiscal_year_service.py` enrichi : `pre_close_checks` (balance, orphelins) et `open_new_fiscal_year` avec report à nouveau (comptes actif/passif à solde non nul)
- Endpoints `/pre-close-checks` (GET) et `/open-next` (POST 201) sur le router fiscal_year
- `dashboard_service.py` : `get_dashboard` (solde banque/caisse, factures impayées/en retard, paiements à remettre, exercice courant, résultat, alertes) et `get_monthly_chart`
- Router `/api/dashboard` : GET / et GET /chart/monthly
- `excel_import.py` service : parseur openpyxl flexible pour `Gestion YYYY.xlsx` (contacts, factures, paiements) et `Comptabilité YYYY.xlsx` (écritures) — détection auto des colonnes, idempotence
- Router `/api/import/excel/gestion` et `/api/import/excel/comptabilite` (limite 10 Mo)
- `main.py` + `database.py` + `conftest.py` : enregistrement des nouveaux modèles et routers
- 22 nouveaux tests (4 fichiers) — 323 tests au total, 78 % couverture

**Frontend (Phase 6)**

- `DashboardView.vue` : KPIs temps réel (cards PrimeVue) + tableau mensuel charges/produits
- `SalaryView.vue` : liste CRUD des salaires + résumé mensuel agrégé + dialog de saisie
- `ImportExcelView.vue` : upload fichier Excel (gestion ou comptabilité) + affichage du rapport d'import
- `api/accounting.ts` : types et fonctions pour salary, dashboard, import Excel, pre-close-checks, open-next
- i18n `fr.ts` : clés `salary.*`, `dashboard.*`, `import.*` + `accounting.fiscalYear.pre_close_*`, `open_next_*`
- Router : routes `/salaries` et `/import/excel`
- NavMenu : entrées Salaires (pi-id-card) et Import Excel (pi-file-excel)

**Backend (Phase 5 — Comptabilité)**

- Modèle `FiscalYear` : exercice comptable avec statuts `open/closing/closed`
- Modèle `AccountingEntry` : écriture en partie double (numéro, date, compte, libellé, débit, crédit, exercice, source)
- Modèle `AccountingRule` + `AccountingRuleEntry` : règles configurables par déclencheur (`TriggerType` — 14 valeurs), libellés avec templates `{{key}}`
- Migrations Alembic `0007` (fiscal_years), `0008` (accounting_entries), `0009` (accounting_rules)
- Schémas Pydantic v2 : `FiscalYearCreate/Read`, `AccountingEntryRead`, `ManualEntryCreate`, `BalanceRow`, `LedgerEntry/Read`, `ResultatRead`, `AccountingRuleRead/Update`
- `accounting_engine.py` : moteur de génération d'écritures basé sur les règles — `generate_entries_for_invoice/payment/deposit`, `seed_default_rules` (13 règles par défaut issues du plan.md)
- `fiscal_year_service.py` : CRUD exercices, clôture (calcul résultat → écriture CLOTURE → statut CLOSED)
- `accounting_entry_service.py` : journal (filtres date/compte/source/exercice), balance, grand livre avec solde glissant, compte de résultat, saisie manuelle équilibrée
- `accounting_rule_service.py` : liste, lecture et mise à jour des règles
- Hooks automatiques dans `invoice.py` (status → SENT), `payment.py` (create_payment) et `bank_service.py` (create_deposit)
- Routeurs `/api/accounting/entries/*`, `/api/accounting/rules/*`, `/api/accounting/fiscal-years/*` enregistrés dans `main.py`
- 93 nouveaux tests (3 fichiers unitaires + 1 intégration) — 87 % couverture globale (301 tests au total)

**Frontend (Phase 5)**

- Types et fonctions API dans `accounting.ts` : journal, balance, grand livre, résultat, saisie manuelle, règles, exercices
- `AccountingJournalView.vue` : journal filtrable + dialog saisie manuelle
- `AccountingBalanceView.vue` : balance agrégée par compte avec totaux débit/crédit/solde
- `AccountingLedgerView.vue` : grand livre par compte avec solde glissant
- `AccountingResultatView.vue` : compte de résultat charges/produits, excédent ou déficit
- `AccountingRulesView.vue` : liste des règles avec activation/désactivation, pré-remplissage
- `FiscalYearView.vue` : liste des exercices, création, clôture avec confirmation
- Routes `/accounting/journal`, `/balance`, `/ledger`, `/resultat`, `/rules`, `/fiscal-years`
- Clés i18n `accounting.journal.*`, `accounting.balance.*`, `accounting.ledger.*`, `accounting.resultat.*`, `accounting.rules.*`, `accounting.fiscalYear.*` dans `fr.ts`
- NavMenu mis à jour avec les 7 nouvelles entrées comptabilité

---

## [0.4.0] — Phase 4 — Paiements & Trésorerie

- Modèle `Payment` : paiement par facture, méthode (espèces/chèque/virement), suivi dépôt en banque
- Modèle `CashRegister` + `CashCount` : journal de caisse avec solde glissant, comptage physique par coupure
- Modèle `BankTransaction` + `Deposit` + table d'association `deposit_payments`
- Migrations Alembic `0005` (payments) et `0006` (caisse + banque)
- Schémas Pydantic v2 : `PaymentCreate/Update/Read`, `CashEntryCreate/Read`, `CashCountCreate/Read`, `BankTransactionCreate/Update/Read`, `DepositCreate/Read`
- Service `payment.py` : CRUD complet, refresh automatique du statut facture (PARTIAL/PAID) à chaque opération
- Service `cash_service.py` : ajout écriture caisse avec solde recalculé, comptage physique, solde actuel
- Service `bank_service.py` : transactions bancaires, rapprochement, bordereaux de remise multi-paiements
- Service `bank_import.py` : import CSV Crédit Mutuel (séparateur `;`, montants en locale française)
- Routeurs `/api/payments/`, `/api/cash/`, `/api/bank/` enregistrés dans `main.py`
- 208 tests (12 nouveaux fichiers de tests) — 84 % de couverture globale

**Frontend (Phase 4)**

- `api/payments.ts`, `api/cash.ts`, `api/bank.ts` : clients API typés
- `PaymentsView.vue` : liste globale des paiements, filtre "à remettre en banque"
- `CashView.vue` : journal de caisse + interface comptage par coupure (onglets)
- `BankView.vue` : relevé bancaire, import CSV, bordereaux de remise, bouton de lettrage
- Routes `/payments`, `/cash`, `/bank` enregistrées dans le router
- Clés i18n `payments.*`, `cash.*`, `bank.*` ajoutées dans `fr.ts`

- Modèle `Invoice` + `InvoiceLine` : numéro `YYYY-C-NNNN` / `YYYY-F-NNNN`, type (`client` | `fournisseur`), label, statuts (draft→sent→paid/partial/overdue/disputed), lignes multi
- Migration Alembic `0004` : tables `invoices` + `invoice_lines`
- Service factures : numérotation auto séquentielle par type et année, calcul total, transitions de statut avec validation, duplication, soft-delete (draft uniquement)
- Exceptions typées : `InvoiceStatusError`, `InvoiceDeleteError`
- Routeur `/api/invoices/` : CRUD REST, `PATCH /{id}/status`, `POST /{id}/duplicate`, `DELETE /{id}`, `GET /{id}/pdf`, `POST /{id}/send-email`, `POST /{id}/file` (upload)
- Upload fichier facture fournisseur : validation MIME (PDF/JPEG/PNG/WebP), limite 10 MB, nom UUID (anti-path-traversal)
- Service `pdf_service.py` : WeasyPrint (import paresseux), template Jinja2 `invoice.html` (logo, coordonnées, lignes, mention Loi 1901)
- Service `email_service.py` : smtplib STARTTLS/SSL-SSL, PDF en pièce jointe, transition draft→sent automatique
- 145 tests pytest (unitaires + intégration) — 79 % de couverture

**Frontend (Phase 3)**

- `api/invoices.ts` : toutes les fonctions CRUD + status + duplicate + pdf + email + upload
- `ClientInvoicesView.vue` : liste filtrée (statut, année), actions PDF/email/dupliquer/supprimer
- `ClientInvoiceForm.vue` : formulaire avec lignes dynamiques et total calculé
- `SupplierInvoicesView.vue` : liste avec dialog upload fichier joint
- `SupplierInvoiceForm.vue` : formulaire montant direct + référence fournisseur
- Routes `/invoices/client` et `/invoices/supplier`
- Clés i18n complètes : `invoices.*` (statuts, labels, actions)
- Menu navigation : Factures clients (`pi-file`) + Factures fournisseurs (`pi-file-import`)

---

**Backend (Phase 2)**

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
