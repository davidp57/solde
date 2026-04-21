# Operational Procedure — Historical Excel Import

## Objective

Run a historical `Gestion` or `Comptabilite` import with a safety level that matches the safeguards currently implemented in the application.

This procedure serves both as an operational checklist and as the baseline for future replays on real files.

## Prerequisites

- Work on a database that is backed up or easy to restore.
- Make sure the local database is on the current schema before any real replay (`alembic upgrade head` if needed).
- Confirm that the source file really matches the expected year and perimeter.
- Use an Excel source export that has not been manually edited between attempts so that the hash safeguard remains meaningful.
- Create in advance all fiscal years covering the imported periods if you want accounting entries to attach automatically to the correct year. For the historical exports currently replayed, this spans dates from `2022` to `2026`.
- Prepare the chart of accounts separately and, for day-to-day management, the accounting rules as well; Excel import never creates them.

## Recommended order

1. Import `Gestion` files first, in chronological order, when that stream is the main business source.
2. Import `Comptabilite` after `Gestion` if the journal is supposed to complement already generated entries; exact duplicates are then ignored and only genuinely new entries are added.
3. Never import the same file twice without first understanding why the initial import is not usable.
4. If payments from a current year point to invoices from the previous year, load the earlier `Gestion` file first so that matching candidates become unique again.

## Pre-import checklist

1. Open the preview for the target file.
2. Confirm that the prepared run can execute (`can_execute = true`).
3. Re-read the prepared operation details, especially blocked or ignored rows.
4. Review warnings sheet by sheet.
5. Check the `ignored_rows` and `blocked_rows` counters.
6. Confirm that ignored rows match expected cases such as in-file duplicates, data already present in the database, or auxiliary sheets.
7. If the preview is blocked, do not force the import: fix the data or the import strategy first.

## Expected blocking cases

- Missing required columns on a recognized sheet.
- Invalid rows in `Contacts`, `Factures`, `Paiements`, `Caisse`, `Banque`, or `Journal`.
- Payments without any matchable invoice.
- Payments ambiguous by reference or by contact.
- Exact re-import of a file already imported successfully.

## Expected ignored rows

- Auxiliary sheets, TODO sheets, reporting sheets, `Journal (saisie)`.
- In-file duplicates in `Contacts` and `Factures`.
- `Contacts` already present in the database.
- `Factures` already present in the database.
- `Total` or summary rows without usable business data in `Factures`.
- Opening-description rows without usable movement in `Banque`.
- Initial-balance rows without usable movement in `Caisse`.
- Cash-deposit forecast rows without a date in `Caisse` when they explicitly represent a future bank deposit.
- `Journal` rows where both debit and credit are zero.
- Exact `Journal` duplicates already present in the database during a complementary `Comptabilite` import.

## Real-world status observed on 2026-04-12

- `Gestion 2024.xlsx`: real import succeeded on an isolated preloaded database (chart of accounts, rules, and fiscal years `2022` to `2026`) with `64` contacts, `303` invoices, `308` payments, `1222` entries, `102` cash movements, and `210` bank transactions created; `2` ignored rows, `0` blocked rows.
- `Gestion 2024.xlsx`: those counters now include reconstructed historical supplier invoices and settlements from `FF-...` references detected in `Banque` and `Caisse`.
- `Gestion 2025.xlsx`: `Caisse` preview row `23` (`Remise espèces`, amount `-710`, missing date) is correctly ignored; `Paiements` ambiguities on rows `2` and `3` disappear after importing `Gestion 2024.xlsx` first, then the real import succeeds with `18` contacts, `211` invoices, `211` payments, `844` entries, `75` cash movements, and `145` bank transactions created; `12` ignored rows, `0` blocked rows.
- Exact re-import of `Gestion 2025.xlsx` is then correctly rejected by the hash safeguard.
- `Comptabilite 2024.xlsx`: DB-aware preview is green with `1385` estimated entries, then the complementary real import succeeds with `1367` created entries, `23` ignored rows, and `0` blocked rows.
- `Comptabilite 2025.xlsx`: DB-aware preview is green with `930` estimated entries, then the complementary real import succeeds with `928` created entries, `12` ignored rows, and `0` blocked rows.
- With fiscal years `2022` to `2026` preloaded, the full replay leaves no imported or generated entry unattached to a fiscal year.
- Former real false positives have been eliminated: `Total` rows in `Factures`, opening-description rows in `Banque`, initial-balance or signed-amount rows in `Caisse`, undated cash-deposit forecasts, and zero-amount `Journal` rows.

## Post-import checks

1. Review the global summary: created objects, ignored rows, blocked rows, warnings.
2. Re-read the sheet-by-sheet detail in the UI and, if needed, the list of executed operations in import history.
3. Verify that the expected created objects are visible in the application.
4. Verify that imported or generated entries are attached to the correct fiscal year when that year already exists.
5. For a `Gestion` import, verify that no accounting-entry error was only surfaced as a warning.
6. If an unexpected behavior appears but the import is technically coherent, use `undo` on the full run or the relevant operation before considering a full database restore.
7. If an unexpected behavior appears, inspect import history or the `import_runs` / `import_operations` / `import_effects` tables to recover the hash, status, and recorded effects; older `import_logs` remain useful for legacy imports.

## Closing imported historical fiscal years

After a full historical replay, the operational rule is the following:

1. Do not close historical fiscal years while imports are still in progress.
2. Import the full historical file set first and verify counters, reconciliations, and fiscal-year attachment.
3. Once the replay is validated, close the older fiscal years through an administrative close, meaning without generating new closing entries or carry-forward entries.
4. Reserve Solde's standard accounting close for fiscal years that are truly managed inside Solde and for which the application must generate the result entry and carry-forward itself.

This distinction avoids duplicating closing entries in Solde when those entries already exist in the imported Excel journals.

## Fallback strategy

1. If preview is blocked: import nothing and correct the source or the strategy.
2. If import fails mid-run: consider the run unusable; execution must stop on the failing operation and leave a diagnosable state.
3. If import succeeded but the business result is wrong and the current state has not diverged: use `undo` on the full run or the targeted operation.
4. If strict `undo` refuses to run because objects were modified afterwards: restore the database backup before retrying with a corrected source.
5. If there is still doubt about management/accounting coexistence: restart from a restored database, replay `Gestion`, then import `Comptabilite` to measure precisely new lines and ignored exact duplicates.

## Known limitations

- Legacy imports that predate BL-004 remain visible through `import_logs`, but they are not reversible with the same level of detail as newer runs.
- Coexistence currently relies on exact accounting-line deduplication only; it does not yet cover near business-level duplicates that are not identical.
- The historical exports currently used for replay cover a broader date perimeter than what their file name alone suggests, so all genuinely covered fiscal years must be prepared before judging accounting attachment quality.
