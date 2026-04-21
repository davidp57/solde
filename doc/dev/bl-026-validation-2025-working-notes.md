# BL-026 / 2025 Validation Working Notes

## Purpose

This note keeps a short, maintainable list of already explained deltas found during the ongoing
validation of `Gestion 2025` and `Comptabilité 2025` against Solde.

It is intentionally lightweight and should be updated whenever a new delta is either:

- explained and considered expected;
- traced back to source Excel data;
- traced back to Solde behavior;
- still open and requiring follow-up.

## Scope

- Fiscal year under validation in Solde: `2025-08-01 -> 2026-07-31`
- Main source files: `Gestion 2025.xlsx`, `Comptabilité 2025.xlsx`
- Status: `working note`, not a final validation report

## Explained Deltas

### 1. Client invoice missing from the 2025 screen because of a wrong source date

- Symptom: Solde showed `182` client invoices in the `2025` fiscal-year screen while Excel had
  `183`, with the same apparent numbering bounds.
- Root cause: invoice `2026-0039` exists in Solde but carries `2025-02-27` as invoice date, so it
  falls outside the `2025-08-01 -> 2026-07-31` screen filter.
- Classification: `source Excel data issue`
- Impact on validation: not a missing import; it is a date-perimeter issue.

### 2. Skipped invoice number does not correspond to a missing invoice

- Symptom: numbering looked discontinuous around `2026-0056`.
- Root cause: `2026-0056` does not exist in Solde and does not exist in the user's accounting
  either.
- Classification: `source numbering gap`
- Impact on validation: not an import delta.

### 3. Inter-fiscal-year cheques create misleading payment deltas

- Symptom: some cheque payments appeared inconsistent between `Gestion` and `Comptabilité` for
  fiscal year `2025`.
- Root cause: some cheques were received or accounted for before `2025-08-01`, but deposited during
  fiscal year `2025`. Solde stores the payment on `payment.date` and the later bank event on
  `deposit_date`, while accounting can expose the carry-over through opening balances and later
  cheque deposits.
- Classification: `business convention / validation convention issue`
- Impact on validation: raw payment totals can diverge even when the underlying behavior is correct.
- Follow-up link: `BL-033`.

### 4. Duplicate bank lines created duplicate client virements in Solde

- Symptom: Solde showed `183` client payments for fiscal year `2025` while the Excel `Paiements`
  sheet showed `181` after excluding the two pre-fiscal-year cheque cases.
- Root cause: the extra payments were not missing from the `Paiements` sheet; instead, the `Banque`
  sheet contained duplicated payment lines for invoices `2025-0202` and `2026-0023`. Solde created
  two virement payments for each of those invoices.
- Confirmed pairs:
  - invoice `2025-0202`: Excel `Paiements` line on `2025-11-06`; Solde payments on `2025-11-06`
    and `2025-11-10`
  - invoice `2026-0023`: Excel `Paiements` line on `2026-02-18`; Solde payments on `2026-02-03`
    and `2026-02-18`
- Classification: `source Excel data issue`
- Impact on validation: explains the `183 vs 181` delta on the payment screen.

## Open Deltas

- None recorded yet in this working note. Add new items here when they are not yet explained.

## Update Rule

Whenever a new delta appears during the `2025` validation:

1. record the observed symptom;
2. state whether the source is `Excel`, `Solde`, or `comparison convention`;
3. keep the explanation short and falsifiable;
4. move the item to `Explained Deltas` once confirmed;
5. keep unresolved items in `Open Deltas` until closed.