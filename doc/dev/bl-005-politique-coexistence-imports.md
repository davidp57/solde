# BL-005 — Coexistence Policy Between Imports and Existing Entries

## Objective

Make the current coexistence rules explicit between:

- `Gestion` imports;
- `Comptabilite` imports;
- business objects already present in Solde;
- accounting entries already generated automatically;
- accounting entries created manually.

This document formalizes the policy currently implemented in code so that historical replay and Excel/Solde convergence do not rely on implicit or contradictory decisions.

## Guiding principles

1. Business safety takes priority over automation.
2. An import must never silently rewrite an existing object or entry without an explicit and safe rule.
3. In accounting, only exact duplicates are deduplicated automatically.
4. A business-level matching ambiguity must be blocked or left for manual review, never resolved arbitrarily.
5. Coexistence with `MANUAL` entries is allowed as long as there is no exact duplicate.

## Adopted policy

### Summary view

| Case | Preview | Real import | Adopted decision |
|---|---|---|---|
| File already imported with the same hash | blocked | blocked | reject exact re-import |
| Exact duplicate of an existing `Gestion` object | ignored | ignored | do not recreate the same business object |
| Exact duplicate of an existing accounting line | ignored | ignored | do not recreate the same accounting line |
| Accounting group already covered by Solde-generated entries | global warning + ignored lines | ignored lines | keep Solde as the already-sufficient source for that group |
| Existing `MANUAL` entries in the period without exact duplicates | allowed | allowed | import the new lines in addition |
| Ambiguous business matching | blocked | blocked | require human resolution |
| Safe clarification of an existing client invoice from `Comptabilite` | ignored as a new entry + business clarification | clarification applied | enrich the existing object without duplicating entries |
| Near duplicate but not exact | only implicit signal through delta or normal behavior | imported as a new entry | do not auto-merge an ambiguous case |

## Detailed rules by case family

### 1. File-level idempotence

- A file already imported successfully, identified by the same hash, is rejected.
- This rule applies to both `Gestion` and `Comptabilite`.
- The visible diagnostic category is `already-imported`.

### 2. `Gestion` imports

#### Contacts, invoices, salaries already present

- If the object already exists according to the currently retained business signature, the row is ignored.
- The import does not attempt to merge, complete, or overwrite the existing object.

#### Payments, bank, cash already present

- If the business comparison signature already exists in Solde, the row is ignored.
- The goal is to avoid functional duplicates, not only technical row duplicates.

#### Ambiguous `Gestion` cases

- If a client contact is ambiguous, the invoice is blocked.
- If a payment cannot be matched safely, it is blocked.
- If several candidates exist for the same reconciliation, it is blocked.

### 3. `Comptabilite` imports

#### Exact duplicate of an accounting line

- A `Journal` line already present with the same signature `(date, account, normalized label, debit, credit)` is ignored.
- This deduplication is intentionally strict.

#### Group already covered by Solde

- If a group of entries is already represented by a Solde-generated group (`invoice`, `payment`, `deposit`, `salary`, `gestion`, `cloture`), it is ignored line by line.
- Preview adds a global coexistence warning to indicate that part of the Excel journal overlaps with entries already produced in Solde.
- This warning is non-blocking.

#### Existing `MANUAL` entries

- The mere presence of `MANUAL` entries does not prevent a `Comptabilite` import.
- If a new accounting line is not an exact duplicate, it is imported as a new `MANUAL` entry.
- The adopted rule is to avoid over-blocking historical imports because of existing manual bookkeeping while keeping strict deduplication.
- When an imported line shares the same date, account, and amounts as a `MANUAL` entry without being an exact duplicate on the label, Solde emits a non-blocking proximity warning to invite manual review.

#### Clarification of an existing client invoice

- If `Comptabilite` entries correspond to a client invoice already present in Solde, Solde does not create duplicate manual accounting entries.
- If the existing invoice can be clarified safely from those entries, the clarification is applied.
- Otherwise, the lines are ignored as already covered by the current data.

### 4. Near duplicates and ambiguous differences

- A near duplicate that is not exact is not merged automatically.
- Typical example: same date, same account, same amount, but a different label without enough proof that it is the same entry.
- In that case the policy remains conservative: it is preferable to keep two entries than to delete or merge incorrectly.

## Current operational translation in diagnostics

Stable categories that are currently visible or derivable include:

- `already-imported` for exact file re-import attempts;
- `entry-existing` for an accounting line already present;
- `entry-covered-by-solde` for an accounting line already covered by a business group or existing Solde operation;
- `entry-near-manual` for an accounting line close to an existing `MANUAL` entry but not strictly identical;
- `existing-row-in-solde` for a `Gestion` line already represented in Solde;
- `comptabilite-coexistence` for the global warning about coexistence with auto-generated entries;
- ambiguity or matching-failure categories such as `invoice-ambiguous-contact`, `payment-unmatched`, and similar blocked cases.

## What BL-005 establishes now

BL-005 establishes the following as the current product target:

- coexistence with existing data is allowed when the case is safe and non-destructive;
- automatic deduplication is limited to exact duplicates or groups explicitly recognized as already covered by Solde;
- there is no principle-level block based solely on the presence of `MANUAL` entries;
- a non-blocking signal is emitted when an imported line is close to an existing `MANUAL` entry without being strictly identical;
- no existing data is ever overwritten silently;
- matching becomes blocked as soon as it turns ambiguous at business level.

## Possible follow-up work outside this initial scope

- decide whether other kinds of near-duplicates should later be surfaced explicitly for manual review beyond the already covered `MANUAL` case.