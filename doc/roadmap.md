<!-- markdownlint-disable MD024 MD033 -->
# Roadmap — Solde ⚖️

> Last updated: 2026-05-11 — active branch `develop` — current version: 1.7.0 (PR open)

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
| **1.2** | Bank reconciliation accounting entries, lot I-BNK, lot J (wizard + contacts) | ✅ Completed |
| **1.3** | Supplier invoice preview, cash count UX, dashboard deposits, multi-email contacts, blocked client, supplier cash payments | ✅ Released 2026-05-02 |
| **1.4** | Lot CR (security), Lot UI (UX & API), Lot DOC (help page), TEC-156 (chat auth fix) | ✅ Released 2026-05-03 |
| **1.5** | Lot MOB (mobile UI), Lot BIZ-034 (dual-account banking), cheque numbering, navigation UX, contacts sort | ✅ Released 2026-05-04 |
| **1.6** | BIZ-170 (pending deposits management), BIZ-171 (mobile invoice UX), BIZ-172 (admin: fix inconsistent cheques) | ✅ Released 2026-05-05 |
| **1.6.1** | Lot REV — technical code review (TEC-160–169, TEC-172) | ✅ Merged 2026-05-06 |
| **1.6.2** | Lot REV2 — standardize API errors, remove service commits, split bank router (TEC-170, TEC-171, TEC-173) | ✅ Merged 2026-05-07 |
| **1.6.3** | TEC-185 (Chrome PDF fix), BIZ-186 (paid watermark on PDF) | ✅ Released 2026-05-10 |
| **1.7** | Lot BK — automated backup (BIZ-173–184) | 🔧 In progress (PR #85) |
| **1.8** | Lot RF — UI/UX redesign (dashboard, invoices, admin) + dark mode + responsive | ⬜ Planned |

Test suite: **1090 backend + 148 frontend Vitest — 0 failures.**

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

## v1.2 — Bank reconciliation accounting, lot I-BNK & lot J ✅

Released: 2026-05-02

### BIZ-141 — Accounting entries on bank reconciliation

Automatic double-entry generation when reconciling a bank transaction:

- Categories `BANK_FEE`, `SOCIAL_CHARGE`, `GRANT`, `INTERNAL_TRANSFER` trigger predefined accounting rules
- Individual reconcile button, "Reconcile all" and "Reconcile before…" all trigger accounting entries
- Source `bank_transaction` traceable in the general journal

### Lot I-BNK — Bank UX improvements

- **BIZ-133** — Category edit: click the pencil icon in the Category column to change a detected category
- **BIZ-134** — Reconcile column: replaced opaque icon with "Rapproché" tag (green) or inline "Rapprocher" button
- **BIZ-135** — Bulk reconciliation: "Tout rapprocher" and "Rapprocher avant…" buttons in the bank toolbar

### Lot J — Quick invoice wizard & contacts

- **BIZ-144** — Quick invoice wizard: confirmation step shows the contact name (`{Prénom} NOM`)
- **BIZ-145** — Email button in wizard confirmation: stays open, email dialog overlays, "E-mail envoyé" badge after send
- **BIZ-147** — Multi-email contacts: up to 2 extra email addresses per contact; email dialog handles multiple recipients with checkboxes; table `contact_emails` (migration 0047)
- **BIZ-151** — Blocked client: `blocked` toggle on client/mixed contacts; red badge in contact list; strict creation block (HTTP 422 + frontend guard)

### Technical — Supplier invoice preview (BIZ-139)

Preview dialog accessible from the eye icon in the supplier invoice list — key info, payment history, embedded PDF/image attachment; prev/next navigation in the current filtered list.

### Technical — Various fixes

- Docker timezone `Europe/Paris` (TEC-152)
- pytest log isolation + SQLAlchemy log downgrade (TEC-153)
- Backup robustness: cleanup on failure, absolute path (TEC-154)
- Cross-browser PDF preview: `<object type="application/pdf">` (TEC-146)
- OFX FITID never stored in `Payment.reference` or displayed in UI

---

## v1.3.1 — Lot CR — security & code quality fixes ✅

Released 2026-05-02.

| ID | Fix |
| --- | --- |
| TEC-133 | Access token stored in memory only (XSS mitigation; `localStorage` removed) |
| TEC-134 | Audit atomicity: `record_audit()` called before `db.commit()` |
| TEC-135 | Invoice numbering race condition: retry loop on `IntegrityError` (3 attempts) |
| TEC-136 | File paths stored as relative in DB; resolved to absolute at read time |
| TEC-137 | JWT payload decoded once per request (cached in `request.state`) |
| TEC-138 | Rate limiter: bounded memory via periodic cleanup every 100 attempts |
| TEC-139 | OpenAI streaming tokens counted (`stream_options={"include_usage": True}`) |
| TEC-140 | Audit log endpoint: server-side pagination + filters (action, actor, dates) |
| TEC-141 | `USER_ROLES` constant — single source of truth for role strings |
| TEC-155 | Removed 13 `# type: ignore[return-value]` in invoice router |

---

## v1.4 — Lot UI — UX & API improvements ⬜

### BIZ-149 — Auto-capitalisation des intitulés facture

First letter of invoice line descriptions auto-capitalised on input.

### BIZ-150 — Heures décimales : accepter « . » et « , »

Both `.` and `,` accepted as decimal separator for the hours field; normalised to `.` before save.

### BIZ-157 — Pagination 50 items par défaut

All DataTables default from 20 to 50 rows per page.

### BIZ-158 — Limite API 1000 items + warning si atteinte

Business endpoints (invoices, payments, contacts, bank transactions & deposits, salary) raised from `limit=100` to `limit=1000`. A visible `Message` warning is displayed in the UI when the returned row count equals the limit, explaining that filters may be incomplete.

### BIZ-034 — Multi-account bank support

Introduce explicit multi-account support to distinguish current account and savings in data, imports and screens.

- Model `BankAccount` (label, IBAN, type), migration, FK on `BankTransaction`
- Filter by account in `BankView`, adapt OFX/CSV imports
- Prerequisite: business decision on granularity (2 fixed accounts vs N dynamic)

### CHR-078 — English i18n skeleton

Create `en.ts` with structural keys to prepare English localisation.

---

## v1.5 — Multi-account banking, mobile UI, cheque numbering, navigation UX ✅ Released 2026-05-04

### BIZ-034 — Dual-account banking (courant + épargne)
Full support for two bank accounts (current + savings). Transactions and deposits are tagged with their account. Balance filter, savings stat card on dashboard, OFX multi-account import with ACCTID auto-resolution, Excel cut-off to avoid duplicates.

### BIZ-164 — Mobile phone mode
Card-based mobile UI for all major list views (invoices, contacts, bank, payments, cash, salaries…). Responsive dialog sizing. Stat cards in 2-column grid on mobile. Auto-suggest cheque number (`YYYYMMDD.NN`) when payment method is cheque (also configurable template in settings).

### BIZ-165 — Factures client : navigation Précédent / Suivant
Previous/Next navigation bar in the client invoice history dialog, matching the supplier invoice preview.

### BIZ-166 — Contacts : onglet clients par défaut + tri récence
Clients tab active by default in the Contacts view. Contacts sorted by recency of last invoice (< 6 months first), then alphabetical.

### BIZ-167, BIZ-168 — Fixes UX navigation factures fournisseur
Bottom navigation bar added to supplier invoice preview dialog. "Marquer créance douteuse" button hidden for supplier contacts.

*Technical:* lots CR2 (TEC-157 to TEC-159), MOB (BIZ-164), CHR-078 (English i18n skeleton), Alembic migrations 0049–0051.

### BIZ-161 — Changelog utilisateur dans la page Aide
Rendre `doc/user/changelog-user.md` accessible depuis la page `/aide` via un onglet « Nouveautés » ou une section dédiée. Endpoint backend `GET /api/help/changelog`, rendu HTML côté Vue.

### BIZ-162 — Liens fonctionnels dans le manuel en ligne
Corriger la résolution des ancres et liens relatifs dans le rendu Markdown du manuel sur `/aide`, de façon que les liens internes (`#section`) et les liens entre pages du manuel fonctionnent.

### BIZ-163 — Index des activités dans le manuel (« en tant que… »)
Ajouter une section d'index dans le manuel utilisateur listant les cas d'usage par rôle (secrétaire, trésorier, administrateur) sous la forme « En tant que X, je veux… » avec des liens vers les sections correspondantes.

---

## v1.8 — Lot RF — UI/UX redesign + dark mode ⬜ Planned

Source: `design_handoff_solde_refonte-v2/` (Claude Design handoff, supersedes v1, adds the responsive track). Not a cosmetic theme — a rework of **information hierarchy**, **consolidation of duplicated components**, and **mobile/tablet/desktop adaptation**, within the Solde identity (Manrope, emerald, slate surfaces). Delivery order advised by the designer: shared `InvoiceWorkspace` first (removes the most duplication), then dark mode (theme store + tokens), then dashboard and admin screens, finally the cross-cutting responsive layer. See backlog Lot RF for the full ticket breakdown.

### Invoices — shared workspace (TEC-193, TEC-194, BIZ-206)
`ClientInvoicesView` and `SupplierInvoicesView` currently duplicate KPIs, toolbar, `DataTable`, the `statusSeverity` helper, and the payment dialog. New `InvoiceWorkspace.vue` (props: type, columns, contextual primary action + overflow `⋯` menu, funnel KPI) backs both screens, with a shared `InvoiceStatusBadge`, quick-filter segments, advanced filters collapsed, and a table footer with selection total.

### Dark mode (TEC-195, TEC-196)
Pinia `theme` store (light/dark, `localStorage` `solde-theme`, respects `prefers-color-scheme`) with a sun/moon toggle in the topbar. Light + dark CSS tokens (Aura dark preset), tighter radii (panels 16px, cards 12px). Token-driven, so redesigned screens inherit dark mode automatically.

### Dashboard (BIZ-207, TEC-198)
Hierarchy by required action instead of 9 equal KPI cards: page header with subtitle + actions, **net treasury hero** (figure + delta pill + sparkline + bank/cash breakdown), shared `AppWorklist` "À traiter", quick actions, four calm non-clickable reference figures, and a single products/charges chart. Single fiscal-year context (topbar selector only). Optional backend enrichment (TEC-198) for treasury delta, reconciliation count, and member count.

### Administration — Users & System (BIZ-208, BIZ-209)
Users: live role matrix (per-role user counts), quick role filters, "vous" badge, shared role badge. System: status banner on top, anomalies as a worklist, isolated destructive **restore** (two-step `RESTAURER` confirmation), colored INFO/WARN/ERROR log terminal, audit log.

### Responsive — mobile / tablet / desktop (TEC-199, TEC-200)
Three breakpoints: desktop (≥1200px, full 240px sidebar, ~1320px centered content), tablet (768–1199px, 72px icon rail, 2-column grids), mobile (<768px, bottom tab bar + drawer, stacked table cards, KPI grids in 1–2 columns, primary action as a thumb-anchored FAB). Touch targets ≥44px; cramped row icon-buttons become a mobile action sheet. Builds on the existing mobile pattern (`AppMobileCardList` + `useBreakpoints`, lot MOB) rather than duplicating it; dark mode applies identically (same tokens).

*Shared:* `AppWorklist` component (TEC-197) reused by dashboard and System. *Release:* CHR-195 (quality gate, docs, dark-mode user doc, version bump).

---

## Not yet planned
