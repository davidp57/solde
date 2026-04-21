# BL-008 — Local Excel/Solde Convergence Check

## Objective

Replay the BL-008 convergence previews on local historical workbooks without persisting anything, so that three questions can be answered quickly:

- what is still missing in Solde;
- what exists in excess in Solde;
- whether the file is still importable or already blocked again by idempotence.

## Validation command

From the repository root, with the virtual environment activated:

```bash
python scripts/run_excel_convergence_preview.py
```

To keep the JSON report:

```bash
python scripts/run_excel_convergence_preview.py --output data/logs/bl-008-convergence-preview.json
```

## Script behavior

- uses the database pointed to by application configuration; locally here that is usually `data/solde.db`;
- prioritizes configured `test_import_*_path` values when present;
- otherwise automatically detects the four historical workbooks under `data/`;
- runs the existing `Gestion` and `Comptabilite` previews without importing;
- returns JSON with global counters, domain-level counters, and a few warning/error samples.

## Local findings on 2026-04-18

Command executed against the current local database `data/solde.db`.

| File | Mode | Importable | Quick reading |
| --- | --- | --- | --- |
| `data/Gestion 2024.xlsx` | `gestion-excel-to-solde` | No | Blocked by an already imported hash; `already_in_solde=329`, `missing_in_solde=579`, `extra_in_solde=0`. |
| `data/Gestion 2025.xlsx` | `gestion-excel-to-solde` | Yes | Significant delta still present; `missing_in_solde=602`, `extra_in_solde=492`. |
| `data/Comptabilité 2024.xlsx` | `global-convergence` | No | Blocked by an already imported hash; `already_in_solde=1385`, `missing_in_solde=0`, `extra_in_solde=1384`. |
| `data/Comptabilité 2025.xlsx` | `global-convergence` | Yes | Readable delta without writing; `missing_in_solde=930`, `extra_in_solde=879`. |

## Minimum interpretation

- The local check confirms that the BL-008 preview now reports both directions of the delta on real files: what is missing in Solde and what exists there in excess.
- Files that were already imported remain naturally blocked by hash-based idempotence, but the comparison report is still usable to inspect the current state.
- The 2025 files remain previewable and already provide a first quantified diagnostic before any import or deeper business analysis.
