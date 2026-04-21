# BL-026 — Framing Quantified Validation for Excel Imports

## Objective

Validate, on the real `2024` and `2025` replay, that the figures visible in Solde match the source Excel files:

- on the `Gestion` side;
- on the `Comptabilité` side;
- fiscal year by fiscal year;
- with an explicit and reusable reconciliation method.

This document frames the validation method. It does not yet define a generic automated reconciliation engine.

## Facts verified in code

### Imports and replay order

- The application does expose four test shortcuts for `Gestion 2024`, `Gestion 2025`, `Comptabilité 2024`, and `Comptabilité 2025`.
- Existing documentation already recommends the following replay order:
  1. `Gestion 2024`
  2. `Gestion 2025`
  3. `Comptabilité 2024`
  4. `Comptabilité 2025`
- That order remains the basis for `BL-026` validation, because some payment matchings only become stable after importing the previous fiscal year.

### Usable Solde sources

#### Primary accounting sources

The following screens and endpoints can be used directly as primary sources for fiscal-year validation because they accept an explicit `fiscal_year_id`:

- `Journal`
- `Balance`
- `Bilan`
- `Résultat`
- `Grand livre`

#### Primary management sources

The following screens and endpoints are usable as primary management sources, but through date or calendar-year filtering rather than `fiscal_year_id`:

- `Factures clients`
- `Factures fournisseurs`
- `Paiements`
- `Banque`
- `Caisse`
- `Salaires`

Consequence: for the `Gestion` side, validation must use the exact fiscal-year date perimeter, not only the file name `2024` or `2025`.

#### Secondary sources only

The following elements are useful as quick checks or sanity checks, but must not be treated as primary evidence for `BL-026`:

- `Dashboard`, because its KPIs are not filtered by fiscal year;
- import result banners, because they reflect the import operation rather than the final consolidated state of the application;
- import preview, because it describes a file before writing, not the final persisted result.

## Retained validation principle

The ticket aims at readable and defensible quantified validation. The retained principle is therefore:

1. compare source Excel data and Solde final state first, not only import counters;
2. reason by real fiscal year and by business domain;
3. use accounting statements as primary evidence on the accounting side;
4. use date-filtered lists and totals as primary evidence on the management side;
5. record every delta explicitly together with a cause hypothesis.

## Comparison perimeter

### 1. `Gestion`

For each fiscal year, compare at minimum:

- the count and total of `factures clients`;
- the count and total of `factures fournisseurs` if the file generates them;
- the count and total of `paiements`;
- the count and total of `caisse` movements;
- the count and total of `banque` movements;
- `salaires` if the fiscal year contains a corresponding sheet;
- a few targeted sensitive business reconciliation cases: deposited or not deposited payments, supplier invoices rebuilt from `FF-*` references, ignored initial-balance movements.

### 2. `Comptabilité`

For each fiscal year, compare at minimum:

- the number of `Journal` entries;
- total `debit` and total `credit` in the `Journal`;
- `Balance` by account with control over total `debit`, `credit`, and `balance`;
- `Bilan` (`total assets`, `total liabilities`, `result`);
- `Résultat` (`expenses`, `income`, net result);
- a reduced set of `grands livres` on sensitive accounts for detailed verification when a delta appears.

## Evidence matrix to produce

| Domain | Excel source | Solde source | Scope | Evidence type |
|---|---|---|---|---|
| Client invoices | `Factures` sheet from `Gestion` | `Factures clients` screen + `GET /invoices` API | fiscal year by dates | count, total, samples |
| Supplier invoices | `Banque` / `Caisse` sheets when `FF-*` reconstruction applies | `Factures fournisseurs` screen + `GET /invoices` API | fiscal year by dates | count, total, sensitive references |
| Payments | `Paiements` sheet from `Gestion` | `Paiements` screen + `GET /payments` API | fiscal year by dates | count, total, deposited/not deposited |
| Cash | `Caisse` sheet from `Gestion` | `Caisse` screen + `GET /cash/entries` API | fiscal year by dates | count, net total, ignored cases |
| Bank | `Banque` sheet from `Gestion` | `Banque` screen + `GET /bank/transactions` API | fiscal year by dates | count, net total, ignored cases |
| Salaries | salary sheet when present | `Salaires` screen | fiscal year by dates/months | count, totals |
| Journal | `Journal` sheet from `Comptabilité` | `journal-grouped` screen/API | fiscal year by `fiscal_year_id` | count, debit, credit |
| Trial balance | `Journal` sheet aggregated by account | `balance` screen/API | fiscal year by `fiscal_year_id` | per account + totals |
| Balance sheet | transformed `Journal` sheet | `bilan` screen/API | fiscal year by `fiscal_year_id` | assets, liabilities, result |
| Income statement | transformed `Journal` sheet | `resultat` screen/API | fiscal year by `fiscal_year_id` | expenses, income, result |
| Ledger | detailed `Journal` sheet | `ledger/{account}` screen/API | fiscal year by `fiscal_year_id` | targeted control when a delta remains |

## Recommended validation sequence

### Step 1 — lock the fiscal-year perimeter

Before any comparison, capture the real date bounds of the fiscal years present in Solde.

Rule: always compare against the real fiscal-year dates, not against a calendar-year assumption inferred from the file name.

### Step 2 — validate management data against final imported state

For each fiscal year:

1. filter management screens or APIs on the exact fiscal-year date range;
2. capture visible counters and totals;
3. rebuild the same figures from Excel;
4. note any delta;
5. classify each delta as:
   - expected import behavior;
   - data divergence;
   - probable bug;
   - business or source ambiguity.

### Step 3 — validate accounting per fiscal year

For each fiscal year:

1. capture `Journal` figures;
2. verify `total debit = total credit`;
3. capture the full `Balance`;
4. capture `Bilan` and `Résultat`;
5. if a delta persists, open one or more targeted `Grands livres` to isolate the responsible account.

### Step 4 — produce a validation report

For each fiscal year, produce a single report with:

- what was compared;
- Excel figures;
- Solde figures;
- status (`compliant`, `justified delta`, `delta to fix`, `to clarify`);
- useful remarks for the next steps of the ticket.

## Expected report format

The target validation format is the following.

### Fiscal year `...`

| Domain | Excel | Solde | Status | Comment |
|---|---|---|---|---|
| Client invoices | ... | ... | ... | ... |
| Supplier invoices | ... | ... | ... | ... |
| Payments | ... | ... | ... | ... |
| Cash | ... | ... | ... | ... |
| Bank | ... | ... | ... | ... |
| Journal | ... | ... | ... | ... |
| Trial balance | ... | ... | ... | ... |
| Balance sheet | ... | ... | ... | ... |
| Income statement | ... | ... | ... | ... |

## Watch points

- Do not use `Dashboard` as the main evidence per fiscal year.
- Do not compare only the counters returned by import: the target is the final persisted Solde state.
- For management data, prefer exact date filters to global comparisons on unbounded lists.
- Auto-generated entries coming from management flows and imported accounting entries must be read together in final accounting statements if the goal is to compare Solde against the full Excel reality.
- Rows explicitly ignored by import policy (`Total`, `initial balance`, zero entry, and so on) must be known before classifying a delta as a bug.

## Recommended next step

Prepare a first validation capture on the fiscal year currently being replayed by the user, with a partially filled report template as soon as imports are completed.