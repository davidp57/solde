# TEC-250 — Dater la ligne provisoire et la sortie de caisse sur le bordereau

Status: ✅ done
Type: fix
Files: `backend/services/bank_service.py`, `tests/unit/test_bank_service.py`,
`docs/user/manuel.md`, `CHANGELOG.md`

## What to build

Dans `confirm_deposit`, remplacer `deposit.confirmed_date` par `deposit.date` pour la
transaction bancaire (espèces et chèques) et pour le `CashEntry` de sortie. Documenter
le choix dans la docstring : `confirmed_date` reste la date de la confirmation, pas
celle du mouvement.

## Acceptance criteria

- [x] Un bordereau daté du 03/08 confirmé le 09/08 produit une ligne bancaire au 03/08.
- [x] La sortie de caisse d'une remise d'espèces porte la même date que la ligne bancaire.
- [x] `confirmed_date` continue d'enregistrer le jour de la confirmation.

## Blocked by

None.
