# TEC-253 — Une remise fusionnée est rapprochée d'office

Status: ✅ done
Type: fix
Files: `backend/services/bank_service.py`, `tests/unit/test_bank_service.py`,
`tests/integration/test_bank_api.py`, `docs/user/manuel.md`, `CHANGELOG.md`

## What to build

`absorb_pending_deposit_transaction` et `merge_deposit_transaction` marquent la ligne
survivante `reconciled = True` et renseignent `reconciled_with` avec « Bordereau #N »,
déduit de la référence `DEP-ESP-N` / `DEP-CHQ-N` de la ligne provisoire (rien si la
référence est celle saisie par l'utilisateur).

## Acceptance criteria

- [x] Après fusion automatique comme manuelle, la ligne est rapprochée.
- [x] La colonne Réf. comptable affiche « Bordereau #N ».
- [x] Référence bancaire personnalisée → colonne vide, pas de valeur devinée.
- [x] Aucune écriture comptable supplémentaire n'est générée.

## Blocked by

None.
