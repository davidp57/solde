<!-- markdownlint-disable MD033 -->
# Backlog — Solde ⚖️

Backlog produit pour Solde ⚖️ — gestion comptable associative.
Quand le travail démarre sur un sujet, créer une branche `feature/` depuis `develop`.
Quand un sujet est livré, mettre à jour `CHANGELOG.md` et passer le ticket en ✅ Fait ici.

---

## Lots actifs

### Lot H — Architecture multi-compte (~45 min) — v0.6

| ID | Titre | Prio | Est. | Créé | Démarré | Terminé |
| --- | --- | --- | --- | --- | --- | --- |
| BIZ-034 | Support multi-compte banque | P2 | ~45 min | 2026-04-21 | | |

### Lot O — Qualité technique backend (~2h) — v0.7

| ID | Titre | Prio | Est. | Créé | Démarré | Terminé |
| --- | --- | --- | --- | --- | --- | --- |
| TEC-098 | Journal comptable : remplacer limit=100 000 par pagination SQL | P1 | ~45 min | 2026-04-25 | | |
| TEC-099 | Cascade FK manquante Payment → Invoice (+ migration Alembic) | P2 | ~15 min | 2026-04-25 | | |
| TEC-100 | Tests manquants : pdf_service, email_service, bank_import | P2 | ~1h | 2026-04-25 | | |

### Lot P — Qualité technique frontend (~1h15) — v0.7

| ID | Titre | Prio | Est. | Créé | Démarré | Terminé |
| --- | --- | --- | --- | --- | --- | --- |
| TEC-101 | Refactoring ClientInvoicesView.vue (~1 100 L) | P2 | ~45 min | 2026-04-25 | | |
| TEC-102 | Utilitaire getErrorDetail() mutualisé (bank dialogs) | P3 | ~10 min | 2026-04-25 | | |
| TEC-103 | Debounce sur filtres texte en temps réel | P3 | ~10 min | 2026-04-25 | | |
| TEC-104 | Casts TypeScript non sûrs dans CashView.vue | P2 | ~10 min | 2026-04-25 | | |

## Hors lots

| ID | Titre | Prio | Est. | Créé | Démarré | Terminé |
| --- | --- | --- | --- | --- | --- | --- |
| CHR-021 | Manuel utilisateur illustré | P1 | ~20 min | 2026-04-13 | 2026-04-13 | |
| BIZ-107 | Contacts : colonne dernière facture + historique en panneau latéral | P2 | ~1h30 | 2026-04-26 | | |
| BIZ-108 | Écran de supervision technique (état système, sauvegardes, audit) | P2 | ~2h30 | 2026-04-26 | | |
| TEC-106 | Audit et complétion des clés i18n manquantes | P2 | ~30 min | 2026-04-25 | | |
| CHR-020 | Documentation de contribution | P3 | ~5 min | 2026-04-13 | 2026-04-21 | |
| CHR-078 | Squelette i18n anglais | P3 | ~5 min | 2026-04-23 | | |

---

## Détails

### BIZ-107 — Contacts : colonne dernière facture + historique en panneau latéral

**Colonne « Dernière facture »** dans `ContactsView` :
- Côté backend : ajouter un champ calculé `last_invoice_ref: str | None` et `last_invoice_date: date | None` dans `ContactRead` (requête SQL avec subquery ou jointure + ORDER BY date DESC LIMIT 1, distingué client/fournisseur).
- Côté frontend : nouvelle colonne « Dernière facture » dans la DataTable, filtrable et triable.

**Historique contact en panneau latéral** (remplace la navigation vers `ContactDetailView`) :
- Remplacer le `$router.push('/contacts/:id/history')` par l'ouverture d'un `<Drawer>` PrimeVue (position `right`, largeur ~700px, fond modal flouté).
- Le contenu du drawer = contenu actuel de `ContactDetailView` (factures + paiements du contact, avec leurs dialogs de détail).
- La route `/contacts/:id/history` reste accessible pour accès direct par URL mais n'est plus utilisée en navigation interne.
- Avantage : filtre/tri de la liste préservé au retour.

**Fichiers à modifier** : `backend/schemas/contact.py`, `backend/services/contact.py`, `backend/routers/contact.py`, `frontend/src/views/ContactsView.vue`, `frontend/src/views/ContactDetailView.vue` (ou nouveau composant `ContactHistoryDrawer.vue`).

---

### BIZ-108 — Écran de supervision technique (état système, sauvegardes, audit)

Nouvelle route admin `/system` → `SystemView.vue` avec 3 panneaux :

**Panneau État système** :
- Version de l'application (depuis `cfg.app_version`)
- Taille de la base SQLite (`os.path.getsize` sur `data/solde.db`)
- Timestamp de démarrage du serveur
- Résultat du dernier health check (badge vert/rouge)
- Endpoint backend : enrichir `GET /api/health` ou créer `GET /api/settings/system-info` (admin only)

**Panneau Sauvegardes** :
- Liste des sauvegardes existantes dans `data/backups/` (nom, taille, date) → `GET /api/settings/backups`
- Bouton « Sauvegarder maintenant » (existant dans `SettingsBackupPanel.vue`, à déplacer ou dupliquer)
- Téléchargement d'une sauvegarde : **à valider** — endpoint `GET /api/settings/backups/{filename}` admin-only avec validation stricte du nom de fichier (pas de path traversal)

**Panneau Journal d'audit** :
- Tableau paginé des `AuditLog` : action, acteur, horodatage, détail → `GET /api/settings/audit-logs` (paginated, filtrable)
- Endpoint à créer (la table `audit_logs` existe mais n'est pas exposée)

**Fichiers à créer/modifier** : `backend/routers/settings.py` (+3 endpoints), `frontend/src/views/SystemView.vue`, `frontend/src/router/index.ts` (route `/system`), `frontend/src/layouts/AppLayout.vue` (entrée menu admin).

---

### TEC-106 — Audit et complétion des clés i18n manquantes

Plusieurs clés i18n ne sont pas renseignées dans `fr.ts` et s'affichent brutes en production (ex. `common.active` dans la vue Employés).
- Parcourir toutes les vues et composants pour identifier les appels `t('...')` sans traduction correspondante dans `src/i18n/fr.ts`.
- Ajouter les traductions manquantes.
- Vérifier aussi les clés orphelines (dans `fr.ts` mais plus utilisées dans le code).

### CHR-020 — Documentation de contribution

`doc/dev/contribuer.md` centralise setup local, `dev.ps1`, checks backend/frontend,
conventions et workflow Git. Reste à valider sur un vrai cycle setup → checks → PR.

### CHR-021 — Manuel utilisateur illustré

Manuel FR pas à pas couvrant les parcours métier essentiels. Structure posée, socle
textuel consolidé. Reste : enrichissement visuel (captures annotées homogènes).
Séquence : lot 1 (connexion, contacts, facture, paiement) → lot 2 (achat, caisse,
banque) → lot 3 (import Excel, comptabilité, FAQ) → lot 4 (captures, stabilisation).

### BIZ-034 — Support multi-compte banque

Distinguer compte courant et compte épargne dans les données, imports et écrans.
Décisions métier nécessaires avant implémentation.

### CHR-078 — Squelette i18n anglais

Créer `en.ts` avec les clés structurelles pour préparer la localisation anglaise.

---

### TEC-098 — Journal comptable : remplacer limit=100 000 par pagination SQL

`backend/services/accounting_entry_service.py` utilise `limit=100_000` dans cinq fonctions (`get_balance`, `get_ledger`, `get_resultat`, `get_bilan`, `get_grouped_journal`) et charge jusqu'à 100 000 lignes en mémoire Python avant d'effectuer un skip/limit Python dans `get_grouped_journal`. `export_service.py` a le même pattern (L43). Sur une association active sur plusieurs exercices, ce plafond peut saturer la RAM de 384 MB allouée.

**Correctif** :
- `get_balance`, `get_ledger`, `get_resultat`, `get_bilan` : remplacer le `limit=100_000` par une agrégation SQL (GROUP BY + SUM) là où seuls les totaux sont nécessaires, ou par une pagination SQL réelle quand la liste de lignes est retournée à l'API.
- `get_grouped_journal` (L597–628) : pousser le `OFFSET`/`LIMIT` dans la requête SQLAlchemy, supprimer le slice Python.
- `export_service.py` : idem — ne charger que les lignes nécessaires à l'export.

**Fichiers à modifier** : `backend/services/accounting_entry_service.py`, `backend/services/export_service.py`.

---

### TEC-099 — Cascade FK manquante Payment → Invoice (+ migration Alembic)

`backend/models/payment.py` ligne 29 : `ForeignKey("invoices.id")` sans `ondelete="CASCADE"`. Si une facture est supprimée directement en base (migration, script, bug), les paiements associés deviennent orphelins avec `invoice_id` pointant vers un enregistrement inexistant, corrompant les rapprochements.

Le service `invoice.py` protège actuellement la suppression applicative, mais la contrainte DB est absente.

**Correctif** :
1. Modifier `payment.py` : `ForeignKey("invoices.id", ondelete="CASCADE")`
2. Créer migration Alembic `0030_payment_invoice_cascade.py` : `DROP CONSTRAINT` + `ADD CONSTRAINT` avec `ON DELETE CASCADE` (SQLite : recréer la table).

**Fichiers à modifier** : `backend/models/payment.py`, nouvelle migration `backend/alembic/versions/0030_payment_invoice_cascade.py`.

---

### TEC-100 — Tests manquants : pdf_service, email_service, bank_import

Trois services sans aucune couverture de test :
- `backend/services/pdf_service.py` — génération PDF facture (WeasyPrint)
- `backend/services/email_service.py` — envoi SMTP (aiosmtplib)
- `backend/services/bank_import.py` — parsing fichier OFX

**Objectif** : atteindre ≥ 80 % de couverture sur chacun.

**Approche** :
- `pdf_service` : mock WeasyPrint, tester que le HTML rendu contient les champs clés (référence, montant, contact)
- `email_service` : mock `smtplib.SMTP`, tester les cas succès, BCC optionnel, SMTP non configuré
- `bank_import` : utiliser `data/comptes.ofx` comme fixture, tester le parsing des transactions, dates, montants, solde d'ouverture

**Fichiers à créer** : `tests/unit/test_pdf_service.py`, `tests/unit/test_email_service.py`, `tests/unit/test_bank_import.py`.

---

### TEC-101 — Refactoring ClientInvoicesView.vue (~1 100 L)

`frontend/src/views/ClientInvoicesView.vue` compte environ 1 100 lignes (hors périmètre de TEC-077 qui ciblait `ImportExcelView`, `BankView`, `SettingsView`). La vue mélange : logique de liste/filtre, calculs de métriques portefeuille, gestion des dialogs, calls API directs.

**Correctif** :
1. Extraire `composables/useInvoiceMetrics.ts` — les computed `receivableMetrics` et `portfolioMetrics` qui filtrent de grands tableaux à chaque changement.
2. Extraire les dialogs (création, édition, envoi email, annulation) vers des sous-composants dédiés (`ClientInvoiceCreateDialog.vue`, etc.) ou les regrouper dans un composable `useInvoiceDialogs`.
3. Les appels API directs restent dans la vue pour l'instant (store dédié hors scope).

**Cible** : vue principale < 500 L, composable métriques < 100 L.

**Fichier source** : `frontend/src/views/ClientInvoicesView.vue`.

---

### TEC-102 — Utilitaire getErrorDetail() mutualisé (bank dialogs)

Le pattern d'extraction de message d'erreur API :
```typescript
(error as { response?: { data?: { detail?: unknown } } }).response?.data?.detail
```
est répété dans au moins 4 composants (`BankSupplierPaymentDialog.vue`, `BankLinkClientPaymentDialog.vue`, `BankLinkSupplierPaymentDialog.vue`, et d'autres). Toute évolution de la structure d'erreur impose de modifier N fichiers.

**Correctif** : créer `frontend/src/utils/errorUtils.ts` avec :
```typescript
export function getErrorDetail(error: unknown): string {
  if (error && typeof error === 'object' && 'response' in error) { ... }
  return 'Erreur inconnue'
}
```
Remplacer toutes les occurrences inline par un appel à `getErrorDetail(error)`.

---

### TEC-103 — Debounce sur filtres texte en temps réel

`ClientInvoicesView.vue` dispose d'un filtre global (`globalFilter`) qui déclenche un re-rendu de la DataTable PrimeVue à chaque frappe, sans debounce. Sur de grandes listes (> 200 factures), cela peut provoquer des freezes perceptibles.

**Correctif** : remplacer le binding direct `v-model="globalFilter"` par une valeur intermédiaire `globalFilterInput` avec un watcher `watchDebounced(globalFilterInput, (v) => { globalFilter.value = v }, { debounce: 200 })` via `@vueuse/core`. Appliquer le même pattern aux autres vues disposant d'un filtre texte inline si nécessaire.

---

### TEC-104 — Casts TypeScript non sûrs dans CashView.vue

`frontend/src/views/CashView.vue` contient trois casts `as unknown as` dans du code de production :
- L487 : `(countForm as unknown as Record<string, number>)[denom.field]` — contournement du typage du formulaire de comptage de caisse
- L891, L900 : `entryForm.value.date as unknown as Date` — le champ `date` est déclaré `string` dans le type du formulaire mais PrimeVue DatePicker renvoie un `Date`

**Correctif** :
- L487 : typer explicitement `countForm` comme `Record<string, number>` ou créer une interface dédiée `CashCountForm`.
- L891/L900 : déclarer `date` comme `Date | null` dans le type du formulaire ou utiliser `toIsoDate(new Date(entryForm.value.date))` avec une assertion propre.

**Fichier à modifier** : `frontend/src/views/CashView.vue`.

---

## Lots terminés

| Lot | Nom | Version | Tickets | Terminé |
| --- | --- | --- | --- | --- |
| 1 | Quick wins P3 | v0.2 | CHR-064, CHR-062, TEC-066, TEC-063 | 2026-04-22 |
| 2 | Tests au vert | v0.2 | TEC-048 | 2026-04-22 |
| 3 | Sécurité sans impact structurel | v0.2 | TEC-047, TEC-052, TEC-055, TEC-060, TEC-051 | 2026-04-22 |
| 4 | Qualité backend sans impact API | v0.2 | TEC-065, TEC-057, TEC-059 | 2026-04-22 |
| 5 | Sécurité auth (full-stack) | v0.2 | TEC-045, BIZ-053, TEC-046 | 2026-04-22 |
| 6 | DevOps Docker | v0.2 | CHR-054, CHR-061 | 2026-04-22 |
| 7 | Refactoring structurel | v0.2 | TEC-050, TEC-058 | 2026-04-22 |
| 8 | Chantiers longs | v0.2 | BIZ-056, TEC-049 | 2026-04-22 |
| A | Backend rapide | v0.3 | TEC-085 | 2026-04-23 |
| B | UX quick wins | v0.3 | BIZ-070, BIZ-072, BIZ-074, BIZ-084, BIZ-042 | 2026-04-23 |
| C | Dashboard interactif | v0.3 | BIZ-075, BIZ-073 | 2026-04-23 |
| D | Polish UI | v0.3 | BIZ-071, BIZ-043 | 2026-04-23 |
| F | Tests | v0.4 | TEC-079, TEC-080, TEC-081 | 2026-04-24 |
| G | Refactoring frontend | v0.5 | TEC-077 | 2026-04-24 |
| I | Polish UI & contacts | v0.5 | BIZ-035, BIZ-037, CHR-038, BIZ-040 | 2026-04-24 |
| J | CI GitHub Actions | v0.5 | CHR-086, CHR-087 | 2026-04-24 |
| K | Documentation & Swagger | v0.5 | CHR-019, CHR-082 | 2026-04-24 |
| L | Gestion employés | v0.6 | BIZ-088 | 2026-04-25 |
| M | Sécurité applicative | v0.6 | TEC-091, TEC-092, TEC-093 | 2026-04-25 |
| N | UX & formulaires | v0.7 | BIZ-094, BIZ-095, BIZ-096, BIZ-097 | 2026-04-25 |
| Q | Recette post-merge N | v0.7 | voir doc/recette.md (REC-001..REC-015) | 2026-04-26 |

Tickets fermés hors lots : TEC-067, TEC-068, BIZ-069, BIZ-076, CHR-083, BIZ-036, BIZ-041, BIZ-033, BIZ-088, BIZ-089, BIZ-090, TEC-105, TEC-039.
Tickets fermés pré-audit : CHR-001, CHR-002, BIZ-003 – BIZ-018, BIZ-022 – BIZ-023.

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

## Légende

| Préfixe | Signification |
| --- | --- |
| BIZ-NNN | Fonctionnalité métier — valeur utilisateur directe |
| TEC-NNN | Technique — qualité, refactoring, tests, sécurité technique |
| CHR-NNN | Maintenance — outillage, documentation, CI, DevOps |

| Priorité | Signification |
| --- | --- |
| P1 | Important — fort impact métier, risque ou besoin opérationnel |
| P2 | Utile — amélioration à programmer |
| P3 | Confort, finition ou dette technique optionnelle |

| Statut | Signification |
| --- | --- |
| Bac d'entrée | Besoin capturé, pas encore arbitré |
| ⬜ Prêt | Besoin clarifié, prêt à être pris |
| 🔄 En cours | Implémentation en cours sur une branche active |
| ✅ Fait | Sujet livré — détail dans `CHANGELOG.md` |
