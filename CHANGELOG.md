# Changelog

Toutes les modifications notables apportées à Solde ⚖️ sont documentées ici.

Le format suit [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Ce projet respecte le [Versionnage sémantique](https://semver.org/lang/fr/).

---

## [Non publié]

### Ajouté

- `doc/user/migration.md` + `doc/user/migration.en.md` : guide de migration / montée de version bilingue FR + EN pour les déploiements Docker sur Synology NAS — couvre la préparation, la mise à jour, la vérification, le rollback et les bonnes pratiques (BL-083)

**Qualité / Sécurité (audit 2026-04-22)**
- `backend/routers/auth.py` : le refresh token est désormais transmis via un cookie `HttpOnly`, `Secure`, `SameSite=Strict` au lieu du corps JSON — `/auth/login` et `/auth/refresh` posent le cookie, nouvel endpoint `POST /auth/logout` (204) l'efface (BL-046)
- Frontend : `refreshApi()` et `logoutApi()` utilisent le cookie automatiquement (`withCredentials: true`), le store auth ne stocke plus le refresh token en `localStorage` (BL-046)
- `entrypoint.sh` : script d'entrée Docker dédié avec `set -e` — les migrations Alembic échouent explicitement au lieu d'être masquées par le `&&` shell (BL-054)
- `GET /api/health` : endpoint de health check léger (200, `{"status": "ok"}`) + `HEALTHCHECK` Docker + `healthcheck:` docker-compose pour la supervision Synology (BL-061)
- `backend/models/user.py` : champ `must_change_password` obligeant l'utilisateur à changer son mot de passe avant d'accéder à l'application — activé au bootstrap admin, à la réinitialisation de mot de passe par un administrateur, et désactivé automatiquement après changement effectif (BL-053)
- `backend/main.py` : middleware `MustChangePasswordMiddleware` bloquant (HTTP 403) toute requête API hors `/api/auth/` quand le JWT porte le flag `mcp=True` (BL-053)
- Frontend : redirection automatique vers la page Profil avec bannière d'avertissement lorsque `must_change_password` est actif ; le router guard empêche la navigation vers d'autres pages (BL-053)
- `backend/config.py` : `get_settings()` utilise désormais `@lru_cache` au lieu d'un pattern `global` mutable — plus idiomatique et thread-safe (BL-066)
- `backend/main.py` : middleware `SecurityHeadersMiddleware` ajoutant `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security` et `Referrer-Policy` sur toutes les réponses (BL-047)
- `backend/config.py` : paramètre `cors_allowed_origins` (liste, variable d'environnement `CORS_ALLOWED_ORIGINS`) permettant de configurer explicitement les origines CORS autorisées en production — wildcard `*` seulement en mode debug sans origines configurées (BL-055)
- `frontend/public/dark-mode-init.js` : script d'initialisation du mode sombre extrait inline vers un fichier statique dédié pour respecter la politique `script-src 'self'` de la CSP (BL-047)
- Endpoints de liste : paramètre `limit` désormais borné (`default=100`, `le=1000`) sur tous les routers de liste — caisse, banque, paiements, factures, contacts, salaires, écritures — pour limiter le volume de données retourné en une seule requête (BL-059)
- `backend/models/types.py` : nouveau `TypeDecorator` `DecimalType` (wrapping `Numeric`) garantissant que SQLAlchemy renvoie toujours un `Decimal` pour les colonnes monétaires au lieu d'un `float` SQLite — élimine les quelque 60 casts `Decimal(str(obj.attr))` répartis dans les services (BL-057)
- `backend/models/payment.py` : suppression de `__allow_unmapped__` et des attributs transients `invoice_number` / `invoice_type` — ces champs sont désormais calculés à la lecture dans `PaymentRead` via une requête ciblée sur `Invoice` (BL-065)
- `backend/models/audit_log.py` : table `audit_logs` + service `record_audit` + enum `AuditAction` pour le journal d'audit structuré — traçabilité des connexions (succès/échec), déconnexions, changements de mot de passe, création/modification d'utilisateurs, réinitialisations de mot de passe admin, et opérations de reset base. Migration Alembic `0023` (BL-056)
- Tests : +44 tests unitaires (812 → 856) pour les services critiques — `fiscal_year_service` (pre_close_checks, report à nouveau), `contact` (historique, créance douteuse), `dashboard_service` (KPIs, alertes, graphiques), `salary_service` (update, filtre par mois), `accounting_rule_service` (CRUD, preview, template). Couverture globale backend ~71 % (BL-049)

### Refactorisé

**Qualité / Sécurité (audit 2026-04-22)**
- `backend/services/excel_import.py` : monolith de 5 567 lignes éclaté en package `backend/services/excel_import/` avec 16 sous-modules thématiques (`_constants`, `_salary`, `_invoices`, `_loaders`, `_comparison`, `_comparison_loaders`, `_comparison_domains`, `_entry_groups`, `_sheet_wrappers`, `_orchestrator`, `_import_contacts_invoices`, `_import_payments_salaries`, `_import_cash_bank`, `_import_entries`, `_preview_existing`, `_preview_sheets`) — refactoring purement structurel, interfaces publiques inchangées, zéro dépendance circulaire (BL-050)
- `backend/services/excel_import/_exceptions.py` : introduction de `ImportFileOpenError` et `ImportSheetError` en remplacement des `except Exception` généralisés — `_ImportSheetFailure(RuntimeError)` remplacé par alias vers `ImportSheetError`, orchestrateur avec catch séparés par type, routeur avec mapping HTTP typé (BL-058)

### Corrigé

**Qualité / Sécurité (audit 2026-04-22)**
- `frontend/src/stores/counter.ts` : suppression du fichier de scaffolding Vue non utilisé (BL-064)
- `frontend/package.json` : version alignée sur `0.1.0` pour correspondre au backend (BL-062)
- `backend/models/accounting_account.py` : remplacement des noms de personnes réelles dans le plan comptable par défaut par des libellés génériques (`Client litigieux 1`, `Client litigieux 2`) — conformité RGPD (BL-063)
- `tests/integration/test_import_api.py` : adaptation du test `test_test_import_shortcuts_list_and_run_configured_file` pour utiliser `unittest.mock.patch` au lieu d'accéder directement au singleton `_settings` supprimé (BL-066)
- `backend/routers/settings.py` : endpoint `POST /settings/reset-db` désormais protégé — retourne HTTP 403 si `settings.debug` est `False`, évitant une remise à zéro accidentelle en production (BL-052)
- `backend/database.py` : suppression de `Base.metadata.create_all` de `init_db()` — le schéma est exclusivement géré par les migrations Alembic ; `init_db()` ne configure plus que les PRAGMAs SQLite (BL-060)
- `backend/services/accounting_engine.py` : `_next_entry_number` utilise désormais `SELECT MAX(entry_number)` au lieu de `SELECT COUNT(*)` pour éviter les collisions de numéros après suppressions ou imports partiels (BL-051)

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
- import réversible BL-004 stabilisé : un paiement préparé peut maintenant se rapprocher d'une facture du même classeur déjà planifiée dans le run, même si l'ordre des onglets est défavorable, et l'exécution facture/paiement ne déclenche plus d'erreurs async sur les snapshots enregistrés

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
