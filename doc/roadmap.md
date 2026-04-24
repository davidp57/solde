<!-- markdownlint-disable MD024 MD033 -->
# Roadmap — Solde ⚖️

> Last updated: 2026-04-24 — active branch `develop`

---

## Version overview

| Version | Scope | Status |
| --- | --- | --- |
| **0.1** | Plan phases 1–7 (full application) | ✅ Completed |
| **0.2** | Technical audit lots 1–8 | ✅ Completed |
| **0.3** | UX audit lots A–D + standalone fixes | ✅ Completed |
| **0.4** | Lot F (tests) + process & quality gates | ✅ Completed |
| **0.5** | Lots E, G + documentation + P1 fixes | 🔄 In progress |
| **0.6** | Lot H — multi-account bank | ⬜ Planned |

Test suite: **913 backend (~71% coverage) + 126 frontend Vitest + 1 Playwright E2E — 0 failures.**

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
| 1 — Quick wins | Code cleanup (BL-064, BL-062, BL-066, BL-063) |
| 2 — Tests au vert | Fix 11 failing tests (BL-048) |
| 3 — Security | HTTP headers, CORS, DB schema, entry numbering (BL-047, BL-052, BL-055, BL-060, BL-051) |
| 4 — Backend quality | Decimal TypeDecorator, pagination, DTO (BL-065, BL-057, BL-059) |
| 5 — Auth security | Rate limit, HttpOnly cookie, forced pwd change (BL-045, BL-053, BL-046) |
| 6 — DevOps | Entrypoint, healthcheck (BL-054, BL-061) |
| 7 — Refactoring | Excel import split, typed exceptions (BL-050, BL-058) |
| 8 — Long-running | Audit log, test coverage 29%→71% (BL-056, BL-049) |

---

## v0.3 — UX audit (lots A–D) ✅

Completed 2026-04-23. UX improvements and new features.

| Lot | Summary |
| --- | --- |
| A — Backend rapide | Password complexity policy (BL-085) |
| B — UX quick wins | 404 page, breadcrumb, offline banner, session expiry, filter reset (BL-070, BL-072, BL-074, BL-084, BL-042) |
| C — Dashboard interactif | Clickable KPIs, keyboard shortcuts (BL-075, BL-073) |
| D — Polish UI | Skeleton loaders, colored account combos (BL-071, BL-043) |

Standalone: error handler (BL-067), Swagger disabled in prod (BL-068), backup endpoint (BL-069), print styles (BL-076), migration guide (BL-083).

---

## v0.4 — Tests & process ✅

Completed 2026-04-24. Test coverage, quality gates, project process.

| Lot | Summary |
| --- | --- |
| F — Tests | Composable tests, Playwright E2E smoke, integration API gaps (BL-079, BL-080, BL-081) |

Also: backlog restructuring, copilot-instructions codification, all quality gates green.

---

## v0.5 — Contacts, refactoring & documentation 🔄

Target: next release. Functional lots with detail, documentation and P1 fixes.

### Lot E — Contacts & import (~25 min)

Séparer clients et fournisseurs dans l'écran contacts, et permettre l'enrichissement
des adresses e-mail par import ponctuel.

| ID | Titre | Est. |
| --- | --- | --- |
| BL-035 | Onglets clients / fournisseurs | ~15 min |
| BL-040 | Import one-shot emails contacts | ~10 min |

**BL-035**: ajouter un `TabView` PrimeVue sur `ContactsView` avec onglets Clients /
Fournisseurs / Tous, filtré par `is_client` / `is_supplier`. Pas de changement backend.

**BL-040**: endpoint `POST /contacts/import-emails` acceptant un CSV ou un copier-coller
d'adresses pour enrichir les contacts existants par correspondance sur le nom.

### Lot G — Refactoring frontend (~30 min)

Éclater les 3 vues volumineuses en sous-composants < 500 lignes.

| ID | Titre | Est. |
| --- | --- | --- |
| BL-077 | Refactoring vues volumineuses | ~30 min |

**BL-077**: `ImportExcelView` (2 873 L) → panels preview/history/upload.
`BankView` (2 215 L) → panels journal/reconciliation/deposit.
`SettingsView` (1 077 L) → tabs association/SMTP/admin.

### Documentation & P1 fixes

| ID | Titre | Est. |
| --- | --- | --- |
| BL-019 | README et documentation technique | ~10 min |
| BL-021 | Manuel utilisateur illustré | ~20 min |
| BL-033 | Comparaison chèques inter-exercices | ~15 min |
| BL-039 | Revalidation scénarios facture / email | ~10 min |
| BL-020 | Documentation de contribution | ~5 min |

### P3 quick wins (v0.5)

| ID | Titre | Est. |
| --- | --- | --- |
| BL-037 | Profil via clic sur le nom | ~5 min |
| BL-038 | Numéro de version dans l'UI | ~5 min |
| BL-078 | Squelette i18n anglais | ~5 min |
| BL-082 | Descriptions Swagger enrichies | ~10 min |

---

## v0.6 — Multi-account bank ⬜

### Lot H — Architecture multi-compte (~45 min)

Introduire un support multi-compte explicite pour la banque afin de distinguer
compte courant et compte épargne dans les données, imports et écrans.

| ID | Titre | Est. |
| --- | --- | --- |
| BL-034 | Support multi-compte banque | ~45 min |

**BL-034**: modèle `BankAccount` (label, IBAN, type), migration, FK sur `BankTransaction`,
filtre par compte dans `BankView`, adaptation imports OFX/CSV.
Prérequis : décisions métier sur la granularité (2 comptes fixes ou N comptes dynamiques).

---

## Not yet planned

Items with roadmap visibility but no target version yet. None currently — all open
tickets are assigned to v0.5 or v0.6.
