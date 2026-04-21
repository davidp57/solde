# Historical Excel Import Contract

## Purpose

Explicitly describe what the Excel import currently considers:

- accepted;
- ignored;
- blocking;
- ambiguous.

This document acts as a working reference as long as the rules are not yet fully extracted into a dedicated business-policy layer.

## `Gestion`

### Contacts

Accepted:
- recognized sheet with a `Nom` column;
- optional `Prénom` column;
- optional `Email` column.

Ignored:
- in-file duplicate for the same contact;
- contact already present in the database.

Blocking:
- recognized row with a missing `Nom` value.

Ambiguous:
- no explicit case at the moment.

### Invoices

Accepted:
- recognized sheet with date, client, and amount;
- invoice number is optional and a technical identifier is generated if missing;
- reuse of an existing contact only when there is a unique normalized exact match on the client name.

Ignored:
- in-file duplicate on the same invoice number;
- invoice already present in the database.

Blocking:
- missing client;
- missing, zero, or invalid amount;
- missing required columns.

Ambiguous:
- several existing contacts match exactly the same normalized client name; the file is then explicitly blocked.

### Payments

Accepted:
- payment whose invoice reference resolves unambiguously;
- or payment without invoice reference but uniquely matchable through the contact;
- in reversible mode, a `Gestion` preview may match a payment against an invoice already present in the database or against an invoice prepared earlier in the same run, even if the `Paiements` sheet appears before the `Factures` sheet in the workbook.

Ignored:
- no explicit case at the moment.

Blocking:
- missing, zero, or invalid amount;
- simultaneous absence of invoice reference and contact;
- payment that cannot be matched to an imported invoice or one already present in the database.

Ambiguous:
- several candidate invoices from a partial reference;
- several candidate invoices through the contact.

### Cash

Accepted:
- recognized sheet with a date and an interpretable monetary movement.

Ignored:
- no explicit case at the moment.

Blocking:
- invalid or missing date;
- movement or amount cannot be interpreted.

Ambiguous:
- no explicit case at the moment.

### Bank

Accepted:
- recognized sheet with a date and an interpretable amount.

Ignored:
- no explicit case at the moment.

Blocking:
- invalid or missing date;
- missing, zero, or invalid amount.

Ambiguous:
- no explicit case at the moment.

## `Comptabilite`

### Journal

Accepted:
- recognized `Journal` sheet with usable account and debit/credit data;
- coexistence allowed with entries already generated from the management flows;
- automatic attachment to the fiscal year covering the entry date when such a year exists.

Ignored:
- reporting sheets (`Grand Livre`, `Balance`, etc.);
- `Journal (saisie)`;
- any `Journal` row where both debit and credit are zero;
- exact duplicate of an existing accounting entry on the signature `(date, account, normalized label, debit, credit)`.

Blocking:
- missing account;
- uninterpretable amounts;
- exact re-import of a file already imported successfully.

Ambiguous:
- no explicit case at the moment.

## Cross-cutting rules

Accepted:
- only recognized and valid sheets contribute to import counters;
- the user-visible import now follows a two-step `prepare -> execute` cycle: persisted preview builds ordered operations with an `apply` / `ignore` / `block` decision, then execution replays only applicable operations;
- the main operational traceability now lives in `import_runs`, `import_operations`, and `import_effects`; older `import_logs` remain useful for legacy history and serialized summaries;
- `undo` / `redo` are strict: an operation or run can only be replayed if the current state of the affected objects still matches the expected one.

Ignored:
- auxiliary sheets, TODO sheets, reporting sheets, and data-entry helper sheets.

Blocking:
- any error detected on a recognized sheet blocks the full import;
- any exact re-import of a file already imported successfully is rejected;
- fiscal years, the chart of accounts, and accounting rules are never created automatically by the import;
- coexistence with existing entries remains allowed: in accounting, only exact duplicates are ignored line by line.

Ambigu :
- tout rapprochement métier donnant plusieurs candidats doit être bloqué, jamais résolu arbitrairement.

## Limites connues

- Une partie de l'orchestration preview/import reste dans `excel_import.py`, mais les décisions métier stables et les diagnostics normalisés sont désormais centralisés.
- Les cas de lignes ignorables sûres restent plus avancés sur `Contacts` et `Factures` que sur les autres feuilles.
- L'historique unifié mélange désormais deux niveaux de traçabilité : les nouveaux runs réversibles détaillés et les anciens `import_logs` non réversibles, qui restent affichés pour conserver la continuité du support.
