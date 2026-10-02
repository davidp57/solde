# TEC-259 — L'import d'écritures Excel numérote à partir du plus grand numéro numérique

Status: ⬜ ready
Type: fix · P1
Files: `backend/services/excel_import/_import_entries.py`,
`tests/unit/` ou `tests/integration/test_import_api.py`

## What to build

Remplacer le `select(func.max(AccountingEntry.entry_number))` brut et son
`except ValueError: next_entry_num = 1` par l'allocateur commun (`next_entry_numbers`, qui
filtre `GLOB '[0-9]{6}'`), en allouant le lot d'écritures de l'import d'un coup.

## Acceptance criteria

- [ ] Test rouge avant correctif : base avec `SAL-2026-03-pay-08` et `002423` → l'import
      échoue (`UNIQUE constraint failed`) ou numérote à `000001`.
- [ ] Après correctif, les écritures importées sont numérotées à partir de `002424`.
- [ ] Plus aucun repli silencieux à `1` sur un `max()` non numérique.
