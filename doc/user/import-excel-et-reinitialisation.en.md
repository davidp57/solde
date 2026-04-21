# User Guide - Excel Import and Reset

## Purpose

This guide explains how to use the following features in Solde:

- the `Gestion` Excel import;
- the `Comptabilite` Excel import;
- the reversible import history;
- the selective reset used during import recovery;
- the full database reset.

It is written from a business-usage and manual-testing perspective.

## The two import types

### `Gestion` import

The `Gestion` import is used to replay day-to-day business data from a historical workbook.

It can create or feed:

- contacts;
- invoices;
- payments;
- cash movements;
- bank transactions;
- accounting entries generated from the rules configured in Solde.

On the historical files currently used in the project, it can also reconstruct supplier invoices and their settlements when references such as `FF-...` are detected in `Banque` or `Caisse`.

### `Comptabilite` import

The `Comptabilite` import is used to replay accounting entries from the Excel `Journal` workbook.

It does not create contacts, invoices, or payments. It only adds accounting entries.

If entries already exist in Solde:

- exact duplicates are ignored;
- genuinely new rows can still be imported;
- some similarities with manual entries may only appear as warnings.

## Before you start

Before any replay or manual retest, check the following:

1. Work on a database that is backed up or easy to restore.
2. Use an unchanged Excel source file between comparable runs.
3. Create the fiscal years that actually cover the dates present in the files.
4. Prepare the chart of accounts if you want to review imported accounting entries.
5. Prepare the accounting rules if you want `Gestion` to generate accounting entries automatically.

Important: the Excel import does not create fiscal years, the chart of accounts, or accounting rules automatically.

## Recommended workflow

When the import has been prepared by Solde through the reversible workflow, the recommended order is:

1. Preview.
2. Execute the import if the diagnostics are acceptable.
3. Verify the business result.
4. Use import history to `undo` or `redo` as long as the reversible journal is still applicable.

When the reversible workflow is not enough, or for older historical imports that were not covered by it, use the selective reset described below.

## Preview

Preview is the mandatory step before an import.

It shows:

- whether the file is importable in the current database state;
- how many objects or entries are likely to be created;
- which sheets are recognized;
- which rows will be ignored;
- which rows block the import.

Recommended procedure:

1. Choose the right file type: `Gestion` or `Comptabilite`.
2. Select the Excel file.
3. Run the preview.
4. Check that the overall status allows the import.
5. Review warnings sheet by sheet.
6. Review ignored and blocking row counters.

If the preview is blocked, do not launch the import.

## How to read diagnostics

### Warnings

A warning means that a row or a sheet was ignored, or that an automatic adaptation was applied without blocking the import.

### Blocking rows

A blocking row prevents the full file from being imported.

### Exact re-import

If the same file has already been imported successfully, Solde refuses to import the exact same file again.

This protects historical replay against unintentional duplicates.

## Reversible import history

The reversible import history is the first tool to use when you want to replay a recent import prepared by Solde.

Depending on the case, it allows you to:

- review prepared operations;
- execute a prepared import;
- undo an import or a single operation;
- redo an undone operation.

This mechanism is strict: if the current state no longer matches the expected one, Solde blocks `undo` or `redo` to prevent an inconsistent rollback.

## Selective reset for import recovery

The selective reset is available in the danger zone of the settings page.

It is used to remove a targeted import perimeter without wiping the whole database.

### When to use it

Use this reset when:

- the original import was not covered by the reversible journal;
- strict `undo` is no longer applicable;
- you need to replay a historical `Gestion` or `Comptabilite` import for a specific fiscal year.

### How it is targeted

The selective reset requires two choices:

- the import stream: `Gestion` or `Comptabilite`;
- the fiscal year to clean.

Solde then builds a deletion plan from import traces and displays a preview before confirmation.

### What the selective reset removes

For `Gestion`, Solde removes:

- imported objects found in the traces;
- derived objects later created in Solde from those imported objects when they belong to the known business dependencies;
- import traces associated with the deleted perimeter.

For `Comptabilite`, Solde removes:

- imported accounting entries for the targeted fiscal year;
- import traces associated with that perimeter.

The preview lists separately:

- imported objects found in the traces;
- derived objects identified;
- the final deletion plan.

### Known limits

The selective reset is not a generic universal cleanup engine.

It applies the business rules currently known for historical import recovery. Always read the preview carefully before confirming.

### Important precaution

This action is irreversible.

Before using it, verify that you selected the intended fiscal year and the correct import stream.

## Full database reset

The full reset removes all application data.

It notably deletes:

- contacts;
- invoices;
- payments;
- accounting entries;
- bank and cash data;
- import traces.

After a full reset, you must reconfigure the environment before replaying a recovery, especially:

- fiscal years;
- chart of accounts;
- accounting rules needed for generated entries;
- any treasury opening settings.

This action should remain limited to demos, isolated tests, and full historical replays on disposable or restorable databases.

## Manual checks after import or reset

After every import, `undo`, selective reset, or full reset, verify at least:

1. the global summary of the operation;
2. the expected created or deleted objects;
3. the impacted fiscal years;
4. bank, cash, and accounting journals when the perimeter touches them;
5. the absence of unexpected side effects on the data that should remain.

## If you are unsure

If a result looks inconsistent:

1. do not replay immediately without understanding what happened;
2. re-read the preview or import history;
3. verify the fiscal year and import type;
4. restart from a restored database if you need a clean full replay.