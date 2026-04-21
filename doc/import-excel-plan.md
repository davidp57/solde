# Hardening Plan for Historical Excel Import

> Working document used to track this effort, maintained in the repository.
>
> Last updated: 2026-04-20
>
> Active branch: `feat-enhance-excel-import`

## Objective

Make historical Excel imports (`Gestion 2025.xlsx` and `Comptabilite 2025.xlsx`) :

- strict: no silent or ambiguous import;
- diagnosable: preview must explain exactly what will be imported, ignored, or blocked;
- consistent: preview and import must share the same rules;
- safe: the final import must be blockable or cancelable cleanly in case of inconsistency.

## Update rule

This file must be updated after every significant slice of work, with at least:

- the status of the tickets below;
- the validations that were actually run;
- the next recommended action;
- the still-blocking open questions.

## Current state

### Macro view

- [x] IMP-00 — Profile real Excel files
- [x] IMP-01 — Strict import contract
- [x] IMP-02 — Faithful and diagnostic preview
- [x] IMP-03 — Shared normalization layer
- [x] IMP-04 — Global business validation before persistence
- [x] IMP-05 — Safe import transaction
- [x] IMP-06 — Clarified management/accounting coexistence
- [x] IMP-07 — Import idempotence and traceability
- [x] IMP-08 — Stronger result reporting and observability
- [x] IMP-09 — Stronger test coverage
- [x] IMP-10 — Hardened confirmation UX
- [x] IMP-11 — Replay on real files and operational procedure
- [x] IMP-12 — Reversible import history and two-phase execution

### Progress summary

- [x] Profiling of real source workbooks completed.
- [x] Preview hardened with explicit sheet classification, detailed diagnostics, exclusion of auxiliary/reporting sheets, and visible blocking when nothing is importable.
- [x] Frontend aligned with those detailed diagnostics, including recognized, ignored, unsupported sheets, detected/missing columns, and warnings/errors.
- [x] Shared normalization layer in place for `Factures`, `Paiements`, `Caisse`, and `Banque` management sheets.
- [x] `Gestion` import order made business-oriented and independent from workbook tab order.
- [x] `Contacts` sheet moved into the same normalized layer.
- [x] First global validation safeguard in place: a file with a recognized but invalid sheet is now refused before any partial write.
- [x] Additional transactional safeguard in place: a late import error also rolls back entries that were already flushed.
- [x] Invalid rows from normalized management sheets are no longer silently ignored: they now surface as blocking preview/import errors.
- [x] Payments that cannot be matched to an imported invoice or one already present in the database are now blocked before persistence.
- [x] `Gestion` preview now reuses the same business validation for payment matching as the real import.
- [x] Ambiguous payment matches no longer depend on the first SQL hit: they are now detected and blocked explicitly.
- [x] Accounting entries now also go through shared preview/import normalization, with explicit row-level errors.
- [x] In-file duplicates detected in `Contacts` / `Factures` now surface as ignored rows with warnings instead of silent skips.
- [x] `Contacts` and `Factures` already present in the database are now announced as ignored rows from preview onward, with counters aligned with the real import.
- [x] The preview/import report now distinguishes `ignored_rows`, `blocked_rows`, global warnings, and per-sheet details.
- [x] Accounting import is now blocked if auto-generated entries coming from management flows already exist in the database.
- [x] A first hash-based idempotence safeguard is in place to block exact re-import of a file already imported successfully, with database logging.
- [x] The import log now also keeps trace of objects created during the import, beyond counters only.
- [x] Preview UI now distinguishes a state of `no importable new data` from a truly blocking error state.
- [x] `Factures` total rows, descriptive opening rows in `Banque`, initial-balance rows in `Caisse`, and `Journal` rows with zero debit/credit are now treated as safe ignored rows.
- [x] Real exports were replayed in preview on the migrated local database: `Comptabilite 2024.xlsx` and `Comptabilite 2025.xlsx` are importable in preview, and the real false positives identified in `Gestion` are now handled as safe ignored rows.
- [x] The real `Gestion 2024.xlsx -> Gestion 2025.xlsx` chain was executed successfully on the local database: the 2024 import recreates missing historical invoices, the 2025 preview turns green again, then the 2025 import succeeds and the exact re-import is correctly blocked again by hash.
- [x] A first core of shared business rules was extracted into `backend/services/excel_import_policy.py` to centralize stable messages and already validated ignore/dedup decisions.
- [x] `ImportResult` and `PreviewResult` containers were extracted into `backend/services/excel_import_results.py`, with dedicated unit validation.
- [x] Pure parsing/normalization helpers and sheet classification were extracted respectively into `backend/services/excel_import_parsing.py` and `backend/services/excel_import_classification.py`, with no observed functional regression.
- [x] Sheet-structure helpers (header detection, safe reading, column lookup, description composition) were extracted into `backend/services/excel_import_sheet_helpers.py`, still with no observed functional regression.
- [x] Preview/diagnostic helpers (preview-sheet building, warning/error aggregation, candidate-contact counting) were extracted into `backend/services/excel_import_preview_helpers.py`, still with no observed functional regression.
- [x] Payment matching was extracted into `backend/services/excel_import_payment_matching.py` (candidates, deduplication, resolution by reference/contact, DB candidate loading), still with no observed functional regression.
- [x] DB state and traceability helpers (file hash, re-import lookup, loading already present keys, accounting coexistence safeguard, import logging) were extracted into `backend/services/excel_import_state.py`, still with no observed functional regression.
- [x] Backend diagnostics are now structured in API output (`error_details` / `warning_details`, global and per sheet) while preserving existing text messages for UI compatibility.
- [x] Sheet parsers and their normalized types were extracted into `backend/services/excel_import_parsers.py` and `backend/services/excel_import_types.py`, with dedicated unit coverage per sheet type.
- [x] The `excel_import_policy` layer now also centralizes stable reasons for `Contacts` / `Factures` rows already present in the database, business deduplication by row type, and preview warnings for ignored/unrecognized sheets.
- [x] The `excel_import_policy` layer now also centralizes stable row-validation messages and the minimal required-column contract by sheet type, reused by shared parsers.
- [x] The `excel_import_policy` layer now also centralizes stable formatting of row issues / missing columns / payment blocks, reused by preview and import, together with a first stable categorization exposed through `error_details` / `warning_details`.
- [x] The first stable categorization of structured diagnostics now also covers recognized but incomplete sheets (`*-missing-columns`) and generic row-validation errors by type (`*-validation-error`) when no more precise code is available.
- [x] Preview/database reconciliation for `Contacts` / `Factures` already present in the database is now also handled through dedicated helpers in `excel_import_policy.py` instead of being rebuilt locally in `excel_import.py`.
- [x] The business decision to block or accept a payment depending on the matching result is now shared through `excel_import_policy.py`, with explicit distinction between preview (acceptable workbook match) and import (persistable target required).
- [x] Repeated construction of ignored preview sheets or unrecognized structures now also goes through dedicated helpers in `excel_import_preview_helpers.py` instead of being rebuilt locally in `excel_import.py`.
- [x] Finalization of a recognized/incomplete preview sheet now also goes through `append_finalized_sheet_preview(...)` instead of locally assembling `status`, `blocked_rows`, and the `missing-columns` error inside `excel_import.py`.
- [x] The stable fast-detection contract for preview headers by management sheet type is now centralized through `detect_gestion_preview_header(...)` instead of being encoded through local branches in `excel_import.py`.
- [x] Global finalization of `preview.can_import` after DB validations is now shared through `finalize_preview_can_import(...)` instead of being repeated in management and accounting previews.
- [x] The stable message for Excel workbook open failure is now shared through `append_preview_open_error(...)` instead of being rebuilt locally in management and accounting previews.
- [x] Stable messages for workbook open failure and backend import error are now shared through `ImportResult` instead of being rebuilt locally in `excel_import.py`.
- [x] The preview branch `kind is None` is now shared through `append_reasoned_ignored_sheet_preview(...)` instead of locally recomputing `status` and the optional warning in management and accounting previews.
- [x] `invoice -> contact` resolution is now strictly shared between preview and import: unique normalized exact match accepted, no match means creation, multiple matches mean explicit block.
- [x] The last global structured diagnostics now also expose stable categories (`already-imported`, `comptabilite-coexistence-blocked`, `import-error`).
- [x] Frontend UX now requires a valid preview before any import, resets that confirmation when the file type changes, keeps the preview visible during import, and requires explicit acknowledgement of warnings before execution.
- [x] Global validation before persistence is complete for the business cases explicitly covered by the current contract.
- [x] The import chain visible in the UI now relies on persisted reversible runs, with two-phase `prepare -> execute`, detailed per-operation effects, and dedicated history.
- [x] `Gestion` preparation can now resolve a payment against an invoice already planned in the same run, independently of the order of `Factures` / `Paiements` tabs in the workbook.

### Latest completed slice

- [x] Extraction of shared normalized parsers for `Factures` and `Paiements`.
- [x] Alignment of preview/import on the case where payments are found through the contact when the invoice reference is missing.
- [x] Regression on sheet order fixed: `Paiements` before `Factures` no longer breaks the import.
- [x] Extension of the same approach to `Caisse` and `Banque` sheets.
- [x] Header detection made accent-insensitive to avoid `Entrée` / `Entree`, `Débit` / `Debit`, and similar mismatches.
- [x] Shared normalization added for `Contacts`, including when the `Prénom` column is missing.
- [x] Import blocked before persistence if preview detects errors on a recognized sheet.
- [x] Global rollback validated when a later sheet fails after intermediate flushes.
- [x] Explicit row-level errors surfaced on `Factures`, `Paiements`, `Contacts`, `Caisse`, and `Banque` instead of silent skips.
- [x] Shared preview/import business validation added to block payments without a matchable invoice.
- [x] Management preview connected to the database to also reflect matches made possible through invoices already present.
- [x] Payment resolution refactored to distinguish `unique`, `ambiguous`, and `not-found` cases.
- [x] Blocking added for ambiguous matches through partial invoice reference or contact with multiple candidate invoices.
- [x] Shared normalized parser added for accounting `Journal` entries.
- [x] Invalid accounting rows are no longer silently ignored in preview/import.
- [x] Explicit distinction between imported, ignored, and blocked rows added to backend results and the UI.
- [x] Preview/database reconciliation added to also mark `Contacts` / `Factures` already present as ignored rows before import.
- [x] Coexistence safeguard added: accounting preview/import refused if auto-generated management entries already exist.
- [x] Minimal import log added with file hash, status, file name, and serialized summary.
- [x] Exact re-import blocked on management and accounting when a hash was already imported successfully.
- [x] The serialized import-log summary now includes the list of objects created during the import.
- [x] Safeguards added for real patterns observed in historical exports: ignored total/summary rows, signed amounts accepted in `Caisse`, zero `Journal` entries ignored.
- [x] Real dry-run replayed after local migration `0011`: the undated cash-deposit forecast is now ignored, and the last ambiguous payments in `Gestion 2025.xlsx` are resolved by importing the previous fiscal year `Gestion 2024.xlsx` first.
- [x] Real import of `Gestion 2024.xlsx` validated on local database (`46` contacts, `263` invoices, `268` payments, `102` cash movements, `210` bank transactions created; `2` ignored rows, `0` blocks).
- [x] DB-aware preview of `Gestion 2025.xlsx` replayed after 2024 import: green (`14` estimated contacts, `183` invoices, `183` estimated payments; `0` blocking error).
- [x] Real import of `Gestion 2025.xlsx` validated on local database (`14` contacts, `183` invoices, `183` payments, `75` cash movements, `145` bank transactions created; `12` ignored rows, `0` blocks), then exact re-import correctly refused by the hash safeguard.
- [x] Extraction of an `excel_import_policy` layer to share ignore rules (`Total`, `initial balance`, cash-deposit forecast, descriptive bank balance, zero journal entry), payment-matching messages, and deduplication.
- [x] Regression covered by a new unit suite `tests/unit/test_excel_import_policy.py` (`8` passing tests) plus the unchanged import integration suite (`35` passing tests).
- [x] Extraction of an `excel_import_results` module to isolate preview/import return structures, secured by `tests/unit/test_excel_import_results.py` (`2` passing tests).
- [x] Extraction of an `excel_import_parsing` module to isolate pure conversions and normalizations, secured by `tests/unit/test_excel_import_parsing.py` (`8` passing tests).
- [x] Extraction of an `excel_import_classification` module to isolate sheet recognition and content detection, secured by `tests/unit/test_excel_import_classification.py` (`6` passing tests).
- [x] Extraction of an `excel_import_sheet_helpers` module to isolate sheet structure and row/column reading, secured by `tests/unit/test_excel_import_sheet_helpers.py` (`6` passing tests).
- [x] Extraction of an `excel_import_preview_helpers` module to isolate preview/diagnostic helpers, secured by `tests/unit/test_excel_import_preview_helpers.py` (`5` passing tests).
- [x] Extraction of an `excel_import_payment_matching` module to isolate payment-matching types and helpers, secured by `tests/unit/test_excel_import_payment_matching.py` (`8` passing tests).
- [x] Extraction of an `excel_import_state` module to isolate DB state, idempotence, and import logging, secured by `tests/unit/test_excel_import_state.py` (`6` passing tests).
- [x] Structuring of preview/import diagnostics in `excel_import_results`, with API exposure covered by `tests/unit/test_excel_import_results.py` (`3` passing tests) and the import integration suite (`35` passing tests).
- [x] Extraction of an `excel_import_parsers` module and an `excel_import_types` module to isolate per-sheet business parsers and normalized rows, secured by `tests/unit/test_excel_import_parsers.py` (`6` passing tests).
- [x] Hardened frontend import flow: main button disabled until a valid preview exists, acknowledgement required in presence of warnings, and automatic invalidation of preview if the file type changes.
- [x] IMP-01 progressed with extraction into `excel_import_policy` of stable `already exists` reasons, preview warnings for ignored/unrecognized sheets, and `Contacts` / `Factures` dedup helpers reused in preview and import.
- [x] IMP-01 progressed with extraction into `excel_import_policy` of stable row-validation messages (`missing amount`, `invalid date`, `missing account`, and so on) and the minimal required-column contract by sheet type, now consumed by `excel_import_parsers`.
- [x] IMP-01 progressed with extraction into `excel_import_policy` of stable formatting for row issues / ignored issues / blocked issues still assembled in `excel_import.py`, plus a first stable `category` inside structured diagnostics from `excel_import_results`.
- [x] IMP-01 progressed with extension of that stable `category` to recognized but incomplete sheets and to row-validation errors that were not precisely mapped, now brought back to business categories by sheet type.
- [x] IMP-01 progressed with extraction into `excel_import_policy` of DB-aware preview rules for `Contacts` / `Factures` already present, reused by `excel_import.py` before marking rows as ignored.
- [x] IMP-01 progressed with extraction into `excel_import_policy` of the post-matching payment block/accept decision, reused both in DB-aware preview and in real import.
- [x] IMP-01 progressed with extraction into `excel_import_preview_helpers` of repeated ignored-sheet / unrecognized-structure preview builders, reused in management and accounting previews.
- [x] IMP-01 progressed with extraction into `excel_import_preview_helpers` of the shared finalization of recognized / incomplete preview sheets (`append_finalized_sheet_preview`), reused in management and accounting previews.
- [x] IMP-01 progressed with centralization inside `excel_import_policy` of stable signatures for fast preview-header detection by management sheet type, reused by `excel_import.py`.
- [x] IMP-01 progressed with extraction into `excel_import_preview_helpers` of global finalization for `preview.can_import = preview.can_import and not preview.errors`, reused in management and accounting previews.
- [x] IMP-01 progressed with extraction into `excel_import_preview_helpers` of the stable Excel-open failure message, reused in management and accounting previews.
- [x] IMP-01 progressed with centralization inside `excel_import_results` of stable `Impossible d'ouvrir le fichier` and `Erreur import ...` messages, reused by management imports, accounting imports, and sheet imports.
- [x] IMP-01 progressed with extraction into `excel_import_preview_helpers` of the shared `kind is None` branch, now reused in management and accounting previews with common computation of `status` and optional warning.
- [x] IMP-06 is now closed: coexistence with `MANUAL` accounting entries is explicitly allowed, while only auto-generated entries coming from management flows block accounting preview/import.
- [x] IMP-07 is now closed in its initial perimeter: the first traceability layer did rely on `import_logs` + `created_objects`, but that base was later superseded by BL-004 and the reversible log `import_runs` / `import_operations` / `import_effects`.
- [x] IMP-05 is now closed: locally caught flush errors inside sheet imports also trigger abort of the global import, counter reset, and a `failed` log.
- [x] IMP-04 is now closed: the remaining known ambiguities are now explicitly blocked before persistence, including `invoice -> contact` resolution when several existing contacts match exactly.
- [x] IMP-01 is now closed: stable business decisions and their structured diagnostics are now centralized, including strict `invoice -> contact` resolution and the remaining global categories.
- [x] PR review 4 absorbed: invoices without a valid date are now blocked explicitly, the preview status banner appears only after a real preview, and the document header no longer claims to be `uncommitted`.
- [x] IMP-12 delivered a reversible `import_runs` / `import_operations` / `import_effects` engine, new `prepare`, `execute`, `undo`, `redo` endpoints, dedicated UI history, and targeted backend/frontend tests.
- [x] IMP-12 was stabilized with correct resolution of payments that point to invoices only prepared in the same run and with async fixes on invoice/payment execution.

### Known passing validations

- [x] `pytest tests/integration/test_import_api.py`: 35 passing tests.
- [x] `pytest tests/unit/test_excel_import_policy.py tests/unit/test_excel_import_results.py tests/unit/test_excel_import_parsing.py tests/unit/test_excel_import_parsers.py tests/unit/test_excel_import_classification.py tests/unit/test_excel_import_sheet_helpers.py tests/unit/test_excel_import_preview_helpers.py tests/unit/test_excel_import_payment_matching.py tests/unit/test_excel_import_state.py tests/integration/test_import_api.py`: 91 passing tests.
- [x] `pytest tests/unit/test_excel_import_policy.py`: 16 passing tests.
- [x] `pytest tests/unit/test_excel_import_policy.py tests/unit/test_excel_import_results.py`: 23 passing tests.
- [x] `pytest tests/unit/test_excel_import_policy.py tests/unit/test_excel_import_results.py`: 25 passing tests.
- [x] `pytest tests/unit/test_excel_import_policy.py tests/unit/test_excel_import_parsers.py`: 22 passing tests.
- [x] `pytest tests/unit/test_excel_import_policy.py`: 23 passing tests.
- [x] `pytest tests/unit/test_excel_import_policy.py`: 26 passing tests.
- [x] `pytest tests/unit/test_excel_import_policy.py`: 28 passing tests.
- [x] `pytest tests/unit/test_excel_import_preview_helpers.py`: 7 passing tests.
- [x] `pytest tests/unit/test_excel_import_preview_helpers.py`: 9 passing tests.
- [x] `pytest tests/unit/test_excel_import_preview_helpers.py`: 11 passing tests.
- [x] `pytest tests/unit/test_excel_import_preview_helpers.py`: 12 passing tests.
- [x] `pytest tests/unit/test_excel_import_preview_helpers.py`: 14 passing tests.
- [x] `pytest tests/unit/test_excel_import_results.py`: 6 passing tests.
- [x] `pytest tests/unit/test_excel_import_policy.py tests/unit/test_excel_import_results.py tests/unit/test_excel_import_preview_helpers.py`: 54 passing tests.
- [x] `pytest tests/integration/test_import_api.py -k "existing_contact or existing_invoice or auxiliary_sheets"`: 4 passing tests.
- [x] `pytest tests/integration/test_import_api.py -k "missing_required_invoice_data or block_payment_without_match or block_row_with_missing_account or block_row_with_invalid_amounts"`: 4 passing tests.
- [x] `pytest tests/integration/test_import_api.py -k "missing_required_invoice_data or block_payment_without_match or existing_contact or existing_invoice"`: 5 passing tests.
- [x] `pytest tests/integration/test_import_api.py -k "missing_required_invoice_data or block_payment_without_match or existing_contact or existing_invoice or recognized_sheet_is_invalid"`: 6 passing tests.
- [x] `pytest tests/integration/test_import_api.py -k "existing_contact or existing_invoice"`: 3 passing tests.
- [x] `pytest tests/integration/test_import_api.py -k "block_payment_without_match or ambiguous_invoice_reference or ambiguous_contact_match or matched_against_existing_invoice"`: 4 passing tests.
- [x] `pytest tests/integration/test_import_api.py -k "auxiliary_sheets or recognized_sheet_is_invalid"`: 2 passing tests.
- [x] `pytest tests/integration/test_import_api.py -k "auxiliary_sheets or recognized_sheet_is_invalid or estimates_contacts_from_invoices_and_payments or accept_contacts_sheet_without_prenom"`: 4 passing tests.
- [x] `pytest tests/integration/test_import_api.py -k "auxiliary_sheets or estimates_contacts_from_invoices_and_payments or recognized_sheet_is_invalid"`: 3 passing tests.
- [x] `pytest tests/integration/test_import_api.py -k "import_gestion_empty_sheet or import_comptabilite_empty_sheet or preview_and_import_gestion_accept_contacts_sheet_without_prenom or preview_and_import_comptabilite_ignore_zero_amount_rows"`: 4 passing tests.
- [x] `pytest tests/integration/test_import_api.py -k "auxiliary_sheets or recognized_sheet_is_invalid or estimates_contacts_from_invoices_and_payments"`: 3 passing tests.
- [x] `pytest tests/integration/test_import_api.py -k "generated_gestion_entries_exist or existing_manual_entries"`: 2 passing tests.
- [x] `pytest tests/integration/test_import_api.py -k "late_sheet_crashes or flush_error_is_caught_locally or generated_gestion_entries_exist or existing_manual_entries"`: 4 passing tests.
- [x] `pytest tests/integration/test_import_api.py -k "ambiguous_existing_contact or generated_gestion_entries_exist or blocks_reimport_of_same_file"`: 4 passing tests.
- [x] `pytest tests/integration/test_import_api.py -k "ambiguous_existing_contact or missing_required_invoice_data"`: 2 passing tests.
- [x] `npm --prefix frontend run type-check`.
- [x] `npm --prefix frontend run test:unit -- --run src/tests/views/ImportExcelView.spec.ts`.
- [x] Auxiliary sheets ignored.
- [x] `Journal (saisie)` ignored.
- [x] Contact estimation present in preview.
- [x] Payments found through the contact.
- [x] Independence from workbook tab order.
- [x] Preview/import consistency on `Caisse` with `Entrée` / `Sortie` columns.
- [x] Preview/import consistency on `Banque` with `Débit` / `Crédit` columns.
- [x] Preview/import consistency on `Contacts` with a `Nom` column and no `Prénom` column.
- [x] Partial imports blocked when a recognized sheet is invalid.
- [x] Rollback of already flushed creations when a late error occurs during import.
- [x] Invalid invoice rows blocked with row-number diagnostics.
- [x] Unmatchable payments blocked with shared preview/import diagnostics.
- [x] Payment-only import accepted when an existing invoice in the database enables the match.
- [x] Ambiguous invoice references blocked.
- [x] Ambiguous matches blocked when a contact carries several candidate invoices.
- [x] Accounting rows with missing account blocked.
- [x] Accounting rows with invalid amounts blocked.
- [x] `Factures` total rows surfaced as ignored.
- [x] Signed amounts accepted in `Caisse` under the single `Montant` format, while keeping the block if the date is missing.
- [x] Descriptive opening rows in `Banque` surfaced as ignored.
- [x] `Journal` rows with zero debit/credit surfaced as ignored.
- [x] Undated cash-deposit forecasts in `Caisse` surfaced as ignored when they correspond to a future bank deposit.
- [x] In-file invoice duplicates surfaced as ignored rows with a detailed report.
- [x] Contacts already present in the database surfaced as ignored rows from preview onward.
- [x] Invoices already present in the database surfaced as ignored rows from preview onward.
- [x] Exact re-import of already imported management files blocked, with attempts logged.
- [x] Exact re-import of already imported accounting files blocked.
- [x] Accounting import blocked when auto-generated management entries already exist.
- [x] Traceability of created objects verified in the import log.
- [x] Real preview of `Gestion 2024.xlsx` green (`46` estimated contacts, `263` invoices, `268` payments, `0` error).
- [x] Real preview of `Comptabilite 2025.xlsx` green (`930` estimated entries, `10` ignored rows, `0` error).
- [x] Real preview of `Comptabilite 2024.xlsx` green (`1385` estimated entries, `20` ignored rows, `0` error).
- [x] Real preview of `Gestion 2025.xlsx` green after prior import of `Gestion 2024.xlsx` (`14` estimated contacts, `183` invoices, `183` payments, `0` error).
- [x] Real import of `Gestion 2024.xlsx` succeeded on local database.
- [x] Real import of `Gestion 2025.xlsx` succeeded on local database.
- [x] Exact re-import of `Gestion 2025.xlsx` blocked again by hash after success of the first import.

## Work backlog

### IMP-00 — Profile real Excel files

- [x] Ticket completed
- Goal: understand real tabs, headers, column variants, and parasitic sheets.
- [x] Profiling of `Gestion 2025.xlsx` completed.
- [x] Profiling of `Comptabilite 2025.xlsx` completed.
- [x] Business sheets and auxiliary/reporting sheets identified.

### IMP-01 — Define the strict import contract

- [x] Ticket completed
- Goal: formalize what is accepted, ignored, blocking, deductible, or ambiguous.
- [x] Formalize a first version of the contract in `doc/dev/import-excel-contract.md`.
- [x] Centralize acceptance, ignore, and block rules in a dedicated business layer.
- [x] Extract a first core of shared rules into `backend/services/excel_import_policy.py`.
- [x] Move stable business rules and their diagnostics out of scattered import functions, leaving only residual orchestration in `excel_import.py`.
- [x] Centralize stable reasons for `Contacts` / `Factures` already present in the database and preview warnings for ignored/unrecognized sheets.
- [x] Centralize `Contacts` / `Factures` business deduplication inside the policy layer.
- [x] Centralize stable row-validation messages and the minimal required-column contract by sheet type.
- [x] Centralize stable formatting of row diagnostics (`ignored` / `blocked` / missing columns / payment blocks) and start a structured `category` compatible with the current API.
- [x] Extend that structured `category` to validation errors still too generic and to `missing-columns` cases by sheet type.
- [x] Move DB-aware preview logic for detecting already present `Contacts` / `Factures` out of `excel_import.py`.
- [x] Move out of `excel_import.py` the shared business decision that turns a payment-matching result into a preview or import block.
- [x] Move out of `excel_import.py` repeated construction of ignored-sheet / unrecognized-structure previews.
- [x] Explicitly define currently known ambiguous cases and their handling strategy.

### IMP-02 — Make preview faithful and diagnostic

- [x] Ticket completed
- Goal: make preview a reliable reflection of real import.
- [x] Explicit classification of management/accounting sheets.
- [x] Exclusion of help, TODO, reporting, and `Journal (saisie)` sheets.
- [x] Per-sheet diagnostics (`status`, `kind`, detected/missing columns, warnings, errors).
- [x] Backend-side `can_import` computation.
- [x] Clear frontend display.

### IMP-03 — Introduce a shared normalization layer

- [x] Ticket completed
- Goal: parse sheets into normalized structures reused both by preview and import.
- [x] `Factures`: shared normalization into invoice rows.
- [x] `Paiements`: shared normalization into payment rows.
- [x] `Caisse`: shared normalization into cash movements.
- [x] `Banque`: shared normalization into bank transactions.
- [x] `Contacts`: shared normalization into contact rows.
- [x] Management import in business order `contacts -> invoices -> payments -> cash -> bank`.
- [x] Accounting `Journal`: shared normalization into entry rows.

### IMP-04 — Add global business validation before persistence

- [x] Ticket completed
- Goal: clearly distinguish:
- [x] Block the full import if preview already detects a recognized invalid sheet.
- [x] Valid rows.
- [x] Ignorable rows.
- [x] Blocking errors.
- [x] Ambiguities requiring arbitration.
- [x] Surface blocking row-level errors for normalized management sheets.
- [x] Block payments without a matchable invoice before any persistence.
- [x] Block ambiguous matches instead of arbitrarily picking a candidate.
- [x] Extend the same principle to invalid accounting-entry rows.
- [x] Distinguish a first batch of safe ignorable rows (`Contacts` / `Factures` duplicated inside the file) from blocking errors.
- [x] Extend that batch to `Contacts` / `Factures` already present in the database, with preview/import alignment.
- [x] Extend that batch to safe total/summary rows really observed (`Factures`, `Banque`, `Caisse`, `Journal`).
- [x] Extend that batch to `Caisse` cash-deposit forecasts without a date when they represent an explicit future bank deposit.
- [x] Start moving those rules and their stable messages into a dedicated `excel_import_policy` layer.
- Target: produce a usable report before any significant flush to the database.

### IMP-05 — Guarantee a safe import transaction

- [x] Ticket completed
- Goal: avoid inconsistent partial imports.
- [x] Cleanly block import when a blocking error is detected in preview/shared validation.
- [x] Guarantee absence of partially persisted data if a later sheet fails.
- [x] Also propagate locally caught flush errors from sheet imports so the global orchestrator stops, resets counters, and logs the import as `failed`.

### IMP-06 — Clarify coexistence between management and accounting

- [x] Ticket completed
- Goal: avoid duplicates or inconsistencies between:
- [x] Define a first practical source of truth: if auto-generated entries from management already exist, they take precedence over a global accounting import.
- [x] Define a first allowed case: accounting import is authorized only if no auto-generated entries from management exist yet.
- [x] Define a first anti-duplicate safeguard on entries: explicit preview/import block for accounting when generated entries are present.
- [x] Clarify the target strategy if manual entries already coexist with a future accounting import.

### IMP-07 — Manage import idempotence and traceability

- [x] Ticket completed
- Goal: be able to answer two questions:
- [x] Know whether a file has already been imported.
- [x] Know which data was created by which import.
- [x] Add an import log, hash, or file signature.
- [x] Add anti-reinjection safeguards.
- [x] Log created objects inside the import summary.
- [x] Establish a first traceability base with `import_logs` + `created_objects`, later superseded by the reversible BL-004 log (`import_runs` / `import_operations` / `import_effects`).

### IMP-08 — Improve result reporting and observability

- [x] Ticket completed
- Goal: provide a final report more useful than a simple counter.
- [x] Structure errors.
- [x] Structure warnings by sheet.
- [x] Add a summary by created or ignored object type.
- [x] Expose in the UI per-sheet detail with imported, ignored, blocked rows and warnings.
- [x] Expose global and per-sheet structured diagnostics through the API while preserving existing text messages for compatibility.

### IMP-09 — Strengthen test coverage

- [x] Ticket completed
- [x] Import integration suite covering several important regressions.
- [x] 35 passing tests on `tests/integration/test_import_api.py`.
- [x] 6 passing tests on `tests/unit/test_excel_import_classification.py`.
- [x] 8 passing tests on `tests/unit/test_excel_import_parsing.py`.
- [x] 6 passing tests on `tests/unit/test_excel_import_parsers.py`.
- [x] 8 passing tests on `tests/unit/test_excel_import_payment_matching.py`.
- [x] 6 passing tests on `tests/unit/test_excel_import_state.py`.
- [x] 16 passing tests on `tests/unit/test_excel_import_policy.py`.
- [x] 3 passing tests on `tests/unit/test_excel_import_results.py`.
- [x] 6 passing tests on `tests/unit/test_excel_import_sheet_helpers.py`.
- [x] 5 passing tests on `tests/unit/test_excel_import_preview_helpers.py`.
- [x] Add tests on `Contacts`.
- [x] Add blocking-validation tests.
- [x] Add rollback tests.
- [x] Add no-reimport / idempotence tests.
- [x] Add tests on ignored rows already present in the database.
- [x] Add tests on real patterns observed in historical exports (`Total`, `initial balance`, signed amounts, zero `Journal`).

### IMP-10 — Harden import confirmation UX

- [x] Ticket completed
- [x] Confirmation button blocked when `can_import` is false.
- [x] Much more readable preview.
- [x] Distinguish in preview a state with no importable new data from a truly blocking state.
- [x] Require a valid preview before any import from the main action.
- [x] Invalidate confirmed preview if the file type changes.
- [x] Keep preview visible during import to confirm in context.
- [x] Require explicit warning acknowledgement before import.

### IMP-11 — Replay on real files and operational procedure

- [x] Ticket completed
- Goal: test the full chain on real historical exports and document a reliable replay procedure.
- [x] Test the full chain on real historical exports according to the retained operational path (`Gestion` as primary source).
- [x] Replay real preview on `Gestion 2025.xlsx` and `Comptabilite 2025.xlsx`.
- [x] Reduce real blocking cases to genuinely ambiguous or incomplete data only.
- [x] Verify that importing the previous fiscal year removes business ambiguities from the current one.
- [x] Execute the real `Gestion 2024.xlsx -> Gestion 2025.xlsx` chain successfully.
- [x] Verify exact re-import blocking after a successful real import.
- [x] Document an import checklist.
- [x] Document the recommended order.
- [x] Document post-import checks.
- [x] Document the fallback strategy.
- [x] Centralize that first procedure in `doc/dev/import-excel-procedure.md`.

### IMP-12 — Reversible import history and two-phase execution

- [x] Ticket completed
- Goal: make imports readable, replayable, and cancelable without restoring the full database for every attempt.
- [x] Persist a prepared import run before execution, with ordered operations and their `apply` / `ignore` / `block` decision.
- [x] Expose the `prepare -> execute -> undo/redo` cycle through the API at full-import and single-operation levels.
- [x] Log detailed effects of each operation on impacted business objects.
- [x] Display in the UI a short summary, a filterable table of prepared operations, warnings, and a dedicated page for import history.
- [x] Keep support compatibility with older `import_logs` through a unified history.
- [x] Stabilize `Gestion` preparation so it accepts a payment matched against an invoice only planned in the same run.
- [x] Cover the reversible engine, history, and critical regressions with targeted backend/frontend tests.

## Files currently involved

- `backend/services/excel_import.py`
- `backend/services/excel_import_classification.py`
- `backend/services/excel_import_parsing.py`
- `backend/services/excel_import_policy.py`
- `backend/services/excel_import_preview_helpers.py`
- `backend/services/excel_import_results.py`
- `backend/services/excel_import_sheet_helpers.py`
- `backend/services/import_reversible.py`
- `backend/routers/excel_import.py`
- `backend/models/import_log.py`
- `backend/models/import_run.py`
- `backend/alembic/versions/0011_add_import_logs.py`
- `backend/alembic/versions/0020_add_reversible_import_runs.py`
- `doc/dev/import-excel-contract.md`
- `doc/dev/import-excel-procedure.md`
- `frontend/src/api/accounting.ts`
- `frontend/src/tests/views/ImportHistoryView.spec.ts`
- `frontend/src/tests/views/ImportExcelView.spec.ts`
- `frontend/src/tests/views/NavMenu.spec.ts`
- `frontend/src/views/ImportHistoryView.vue`
- `frontend/src/views/ImportExcelView.vue`
- `frontend/src/i18n/fr.ts`
- `tests/unit/test_excel_import_classification.py`
- `tests/unit/test_excel_import_parsing.py`
- `tests/unit/test_excel_import_policy.py`
- `tests/unit/test_excel_import_preview_helpers.py`
- `tests/unit/test_excel_import_results.py`
- `tests/unit/test_excel_import_sheet_helpers.py`
- `tests/integration/test_import_api.py`

## Recommended resume point

The next useful slice is no longer about confirmation UX, which is now locked on the frontend side, but about the structural areas still open in the import engine.

Recommended order:

1. [ ] formalize global validation rules by sheet type in a dedicated business layer;
2. [ ] extend stable categorization beyond the already covered set (`existing`, `duplicate`, `missing-columns`, payment errors, sheet warnings, `*-validation-error`) toward the last remaining free-form messages;
3. [ ] clarify the target coexistence strategy with possible manual entries before opening real `Comptabilite` import;
4. [ ] decide whether the UI rendering of reversible runs still needs enrichment (filters, exports, diagnostics) or whether the current level is sufficient for day-to-day support.

## Open questions

- What exact policy do we want for accounting import if auto-generated management entries already exist?
- Do we want to keep a partial-import mode with warnings, or move to a strictly blocking mode as soon as a recognized sheet is inconsistent?
- Do we want to keep the dual history `reversible runs + legacy import_logs` over time, or plan a full migration of older logs toward a more homogeneous format?

## Summary log

### 2026-04-20

- BL-004 added a persistent reversible import log with `import_runs`, `import_operations`, and `import_effects`.
- The import API now exposes a two-phase `prepare -> execute -> undo/redo` cycle, complemented by a unified `runs + import_logs` history.
- The import UI was reorganized around a short summary, dedicated tabs, a filterable operations table, and a separate history page.
- `Gestion` preparation now accepts a payment matched against an invoice only planned in the same run, even when workbook tabs are ordered unfavorably.
- BL-004 stabilization also removed async errors on the invoice/payment execution path in the reversible engine.

### 2026-04-11

- IMP-03 progressed with shared normalization for `Factures` / `Paiements`.
- Sheet order is no longer a behavior factor for management import.
- IMP-03 was extended to `Caisse` and `Banque`, with preview/import alignment on separate `Entrée` / `Sortie` and `Débit` / `Crédit` columns.
- Header detection is now accent-insensitive.
- IMP-03 was completed for `Contacts`, including a sheet without a `Prénom` column.
- IMP-04 started with a first safeguard: a file containing a recognized but invalid sheet is now refused before any partial import.
- IMP-05 started with a global rollback validated on late import error.
- IMP-04 progressed with row-level errors now explicit and blocking on normalized management sheets.
- IMP-04 / IMP-05 progressed with shared preview/import validation for unmatchable payments, including against invoices already present in the database.
- IMP-04 / IMP-05 progressed with explicit blocking of ambiguous payment matches by reference or contact.
- IMP-03 / IMP-04 progressed with shared normalization of accounting entries and explicit blocking of invalid journal rows.
- IMP-04 / IMP-08 progressed with an explicit distinction between imported, ignored, and blocked rows, plus detailed sheet warnings on backend and frontend sides.
- IMP-07 started with a minimal import log and a hash-based block on exact re-imports already imported successfully.
- IMP-06 started with an explicit block on accounting import when auto-generated management entries already exist in the database.
- IMP-07 progressed with traceability of created objects stored directly in the import-log summary.
- IMP-01 started with an explicit import contract documented in `doc/dev/import-excel-contract.md`.
- IMP-11 started with a first operational procedure documented in `doc/dev/import-excel-procedure.md`.
- IMP-10 progressed with a UI distinction between blocked preview and preview without importable new data.
- IMP-04 / IMP-11 progressed with explicit handling of real export patterns: ignored `Total` rows, ignored descriptive opening `Banque` rows, ignored initial-balance `Caisse` rows, and accepted signed `Caisse` amounts.
- IMP-04 / IMP-11 progressed with explicit ignoring of undated cash-deposit forecasts when they correspond to a future bank deposit.
- IMP-04 / IMP-11 progressed with explicit ignoring of zero debit/credit `Journal` rows.
- The local replay database was migrated to the current schema (`0011`) so DB-aware previews could use `import_logs`.
- The `tests/integration/test_import_api.py` suite is green with 35 tests.
- A new `backend/services/excel_import_policy.py` layer centralizes a first core of business rules and messages, covered by `tests/unit/test_excel_import_policy.py` (8 passing tests).
- `backend/services/excel_import_policy.py` now also centralizes stable `already exists` reasons, preview warnings for ignored/unrecognized sheets, and business deduplication for `Contacts` / `Factures`, covered by `tests/unit/test_excel_import_policy.py` (16 passing tests).
- `backend/services/excel_import_policy.py` now also centralizes stable row-validation messages and the minimal required-column contract, reused in `backend/services/excel_import_parsers.py` and validated by `tests/unit/test_excel_import_policy.py` + `tests/unit/test_excel_import_parsers.py` (22 passing tests).
- `backend/services/excel_import_policy.py` now also centralizes stable formatting of row diagnostics and missing columns, reused in `backend/services/excel_import.py` and `backend/services/excel_import_preview_helpers.py`, while `backend/services/excel_import_results.py` exposes a first stable `category` in structured details, validated by `tests/unit/test_excel_import_policy.py` + `tests/unit/test_excel_import_results.py` (23 passing tests) and an import integration subset (5 passing tests).
- `backend/services/excel_import_policy.py` now also categorizes recognized but incomplete sheets (`*-missing-columns`) and residual validation errors through a per-type `*-validation-error` fallback; this extension is validated by `tests/unit/test_excel_import_policy.py` + `tests/unit/test_excel_import_results.py` (25 passing tests) and an import integration subset (6 passing tests).
- `backend/services/excel_import_policy.py` now also encapsulates DB-aware preview detection of `Contacts` / `Factures` already present, reused by `backend/services/excel_import.py` and validated by `tests/unit/test_excel_import_policy.py` (23 passing tests) plus the `existing_contact or existing_invoice` integration subset (3 passing tests).
- `backend/services/excel_import_policy.py` now also encapsulates the shared decision derived from `PaymentMatchResolution`, with workbook-candidate tolerance in preview but a persistable target requirement in import; this extraction is validated by `tests/unit/test_excel_import_policy.py` (26 passing tests) and the payment integration subset (4 passing tests).
- `backend/services/excel_import_preview_helpers.py` now also encapsulates construction of ignored preview sheets and unrecognized structures, reused by `backend/services/excel_import.py` and validated by `tests/unit/test_excel_import_preview_helpers.py` (7 passing tests) plus the `auxiliary_sheets or recognized_sheet_is_invalid` integration subset (2 passing tests).
- `ImportResult` and `PreviewResult` containers now live in `backend/services/excel_import_results.py`, covered by `tests/unit/test_excel_import_results.py` (2 passing tests).
- Pure parsing helpers now live in `backend/services/excel_import_parsing.py`, and sheet recognition lives in `backend/services/excel_import_classification.py`, covered respectively by 8 and 6 passing unit tests.
- Sheet-structure helpers now live in `backend/services/excel_import_sheet_helpers.py`, covered by 6 passing unit tests.
- Preview/diagnostic helpers now live in `backend/services/excel_import_preview_helpers.py`, covered by 5 passing unit tests.
- Real previews of `Comptabilite 2024.xlsx` and `Comptabilite 2025.xlsx` are green.
- Real import of `Gestion 2024.xlsx` reintroduced historical invoices `2025-0131` and `2025-0134`, which removed ambiguities in `Gestion 2025.xlsx`.
- The real `Gestion 2024.xlsx -> Gestion 2025.xlsx` chain was executed successfully on the local database, and exact re-import of `Gestion 2025.xlsx` is correctly blocked again by hash.
- IMP-10 was closed on the frontend side: direct import without preview is no longer possible, confirmation is invalidated when the type changes, and warnings require explicit acknowledgement.
- A targeted Vue test now covers that lock (`3` passing tests).
- Next concrete objective: open a new effort if needed; the current IMP plan is now fully addressed.
