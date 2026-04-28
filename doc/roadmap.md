<!-- markdownlint-disable MD024 MD033 -->
# Roadmap — Solde ⚖️

> Last updated: 2026-04-28 — active branch `develop` — current version: 1.1.0

---

## Version overview

| Version | Scope | Status |
| --- | --- | --- |
| **0.1** | Plan phases 1–7 (full application) | ✅ Completed |
| **0.2** | Technical audit lots 1–8 | ✅ Completed |
| **0.3** | UX audit lots A–D + standalone fixes | ✅ Completed |
| **0.4** | Lot F (tests) + process & quality gates | ✅ Completed |
| **0.5** | Lots E, G, I, K + documentation + P1 fixes | ✅ Completed |
| **0.6** | Lots L, M — employee management + security | ✅ Completed |
| **0.7** | Lots N, O, P, Q — UX, forms, quality | ✅ Completed |
| **0.8** | Lots R, S — supervision, i18n, doc restructure | ✅ Completed |
| **1.0** | Lots T — chatbot, email templates, credit notes — first stable release | ✅ Completed |
| **1.1** | Bank deposit workflow + 7 UX improvements | ✅ Completed |
| **1.2** | Multi-account bank + i18n English skeleton | ⬜ Planned |

Test suite: **999 backend + 131 frontend Vitest + 1 Playwright E2E — 0 failures.**

---

## v0.1 — Full application (plan.md)

All features from the initial `plan.md` are implemented across 7 phases (75 tasks).

<details>
<summary>Phase summary — click to expand</summary>

| Phase | Goal | Tasks |
| --- | --- | --- |
| 1. Foundations | Docker, FastAPI, SQLite, JWT auth, Vue.js scaffold | 9 |
| 2. Core management | Contacts, chart of accounts | 7 |
| 3. Invoicing | Client/supplier invoices, PDF, e-mail | 7 |
| 4. Payments & Treasury | Payments, cash, bank, deposits, OFX import, reconciliation | 14 |
| 5. Accounting | Rules engine, journal, balance, ledger, manual entries | 16 |
| 6. Advanced features | Year close, salaries, Excel import, dashboard | 14 |
| 7. Plan completion | Balance sheet, bad debt, CSV export, preview, OFX/QIF | 9 |

**Stack**: FastAPI + SQLAlchemy 2 async + SQLite WAL + Alembic + Vue.js 3 + PrimeVue 4 + Pinia + WeasyPrint (lazy).

</details>

---

## v0.2 — Technical audit (lots 1–8) ✅

Completed 2026-04-22. Refactoring, security hardening, test coverage, DevOps.

| Lot | Summary |
| --- | --- |
| 1 — Quick wins | Code cleanup (CHR-064, CHR-062, TEC-066, TEC-063) |
| 2 — Tests au vert | Fix 11 failing tests (TEC-048) |
| 3 — Security | HTTP headers, CORS, DB schema, entry numbering (TEC-047, TEC-052, TEC-055, TEC-060, TEC-051) |
| 4 — Backend quality | Decimal TypeDecorator, pagination, DTO (TEC-065, TEC-057, TEC-059) |
| 5 — Auth security | Rate limit, HttpOnly cookie, forced pwd change (TEC-045, BIZ-053, TEC-046) |
| 6 — DevOps | Entrypoint, healthcheck (CHR-054, CHR-061) |
| 7 — Refactoring | Excel import split, typed exceptions (TEC-050, TEC-058) |
| 8 — Long-running | Audit log, test coverage 29%→71% (BIZ-056, TEC-049) |

---

## v0.3 — UX audit (lots A–D) ✅

Completed 2026-04-23. UX improvements and new features.

| Lot | Summary |
| --- | --- |
| A — Backend rapide | Password complexity policy (TEC-085) |
| B — UX quick wins | 404 page, breadcrumb, offline banner, session expiry, filter reset (BIZ-070, BIZ-072, BIZ-074, BIZ-084, BIZ-042) |
| C — Dashboard interactif | Clickable KPIs, keyboard shortcuts (BIZ-075, BIZ-073) |
| D — Polish UI | Skeleton loaders, colored account combos (BIZ-071, BIZ-043) |

Standalone: error handler (TEC-067), Swagger disabled in prod (TEC-068), backup endpoint (BIZ-069), print styles (BIZ-076), migration guide (CHR-083).

---

## v0.4 — Tests & process ✅

Completed 2026-04-24. Test coverage, quality gates, project process.

| Lot | Summary |
| --- | --- |
| F — Tests | Composable tests, Playwright E2E smoke, integration API gaps (TEC-079, TEC-080, TEC-081) |

Also: backlog restructuring, copilot-instructions codification, all quality gates green.

---

## v0.5 — Contacts, refactoring & documentation ✅

Completed 2026-04-24.

Target: next release. Functional lots with detail, documentation and P1 fixes.

### Lot E — Contacts & import (~25 min)

Séparer clients et fournisseurs dans l'écran contacts, et permettre l'enrichissement
des adresses e-mail par import ponctuel.

| ID | Titre | Est. |
| --- | --- | --- |
| BIZ-035 | Onglets clients / fournisseurs | ~15 min |
| BIZ-040 | Import one-shot emails contacts | ~10 min |

**BIZ-035**: ajouter un `TabView` PrimeVue sur `ContactsView` avec onglets Clients /
Fournisseurs / Tous, filtré par `is_client` / `is_supplier`. Pas de changement backend.

**BIZ-040**: endpoint `POST /contacts/import-emails` acceptant un CSV ou un copier-coller
d'adresses pour enrichir les contacts existants par correspondance sur le nom.

### Lot G — Refactoring frontend (~30 min)

Éclater les 3 vues volumineuses en sous-composants < 500 lignes.

| ID | Titre | Est. |
| --- | --- | --- |
| TEC-077 | Refactoring vues volumineuses | ~30 min |

**TEC-077**: `ImportExcelView` (2 873 L) → panels preview/history/upload.
`BankView` (2 215 L) → panels journal/reconciliation/deposit.
`SettingsView` (1 077 L) → tabs association/SMTP/admin.

### Documentation & P1 fixes

| ID | Titre | Est. |
| --- | --- | --- |
| CHR-019 | README et documentation technique | ~10 min |
| CHR-021 | Manuel utilisateur illustré | ~20 min |
| BIZ-033 | Comparaison chèques inter-exercices | ~15 min |
| TEC-039 | Revalidation scénarios facture / email | ~10 min |
| CHR-020 | Documentation de contribution | ~5 min |

### P3 quick wins (v0.5)

| ID | Titre | Est. |
| --- | --- | --- |
| BIZ-037 | Profil via clic sur le nom | ~5 min |
| CHR-038 | Numéro de version dans l'UI | ~5 min |
| CHR-078 | Squelette i18n anglais | ~5 min |
| CHR-082 | Descriptions Swagger enrichies | ~10 min |

---

## v0.6 — Employee management & security ✅

Completed 2026-04-25.

| Lot | Summary |
| --- | --- |
| L — Employee management | Full employee + payroll module (BIZ-088, BIZ-089, BIZ-090) |
| M — Security | UnhandledExceptionMiddleware, SWAGGER_ENABLED flag, i18n audit prep (TEC-091, TEC-092, TEC-093) |

---

## v0.7 — UX & forms ✅

Completed 2026-04-26.

| Lot | Summary |
| --- | --- |
| N — UX & forms | Supplier invoices, email attachments, invoice email body, numbering templates, default prices, dashboard wizards (BIZ-094–BIZ-097, BIZ-119, BIZ-122, BIZ-123, BIZ-124) |
| O — Backend quality | Ruff/mypy pass, test coverage improvements (TEC-098, TEC-099, TEC-100) |
| P — Frontend quality | ESLint pass, vue-tsc, Vitest improvements (TEC-101, TEC-102, TEC-103, TEC-104) |
| Q — Post-merge recette | REC-001..REC-015 regressions fixed |

---

## v0.8 — Supervision, i18n & documentation ✅

Completed 2026-04-27.

| Lot | Summary |
| --- | --- |
| R — System supervision | System supervision screen, audit log viewer (BIZ-108, BIZ-109) |
| S — Documentation & i18n | i18n audit + missing keys (TEC-106), full doc restructure (CHR-020, CHR-021, CHR-079) |

---

## v1.0 — Chatbot IA, e-mail templates & credit notes ✅

Completed 2026-04-27. First stable production release.

| Lot | Summary |
| --- | --- |
| T — Chatbot IA + refactor Paramètres | AI assistant sidebar + help page + settings refactor (BIZ-125, BIZ-126) |

### BIZ-127 — Email confirmation dialog
Pre-send preview dialog with editable subject/body and embedded PDF preview.

### BIZ-128 — Configurable email templates
Admin-configurable subject and body templates for invoice emails (variables: `{invoice_number}`, `{description}`, `{association_name}`, `{invoice_ref}`).

### BIZ-129 — Credit notes (avoirs)
Full credit note support: `avoir` document type, separate `AV-YYYY-NNN` numbering, pre-filled reversed lines, dedicated PDF template, `credit_note_for_id` traceability.

---

## v1.1 — Bank deposit workflow + UX improvements ✅

Completed 2026-04-28.

| Lot | Summary |
| --- | --- |
| BIZ-130 — Bank deposit confirmation | Explicit confirmation workflow for deposits; `confirmed` field; pending deposits panel in Bank view; status column |
| BIZ-131 — Cash deposit model refactor | Cash payments marked `deposited=True` at creation; denomination-based cash deposits; entries generated at confirmation (migration 0039) |
| BIZ-132 — Cheque in-transit state | Intermediate `in_deposit` state before confirmation; select-all button; 3-state « Remis en banque » column; fix credit BankTransaction on cash confirmation (migration 0040) |
| Lot H-UX — 7 UX improvements | Settings read access for managers; payment dialog with invoice details; family fields on contacts (migration 0041); pre-filled invoice date; internal comments system (migrations 0042, 0043); PDF payment instructions; invoice edit lock |

---

## v1.2 — Multi-account bank & i18n ⬜

### BIZ-034 — Multi-account bank support

Introduce explicit multi-account support to distinguish current account and savings in data, imports and screens.

- Model `BankAccount` (label, IBAN, type), migration, FK on `BankTransaction`
- Filter by account in `BankView`, adapt OFX/CSV imports
- Prerequisite: business decision on granularity (2 fixed accounts vs N dynamic)

### CHR-078 — English i18n skeleton

Create `en.ts` with structural keys to prepare English localisation.

---

## Not yet planned
