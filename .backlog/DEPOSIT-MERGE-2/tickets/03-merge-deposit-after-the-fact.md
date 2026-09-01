# BIZ-251 — Rattacher une ligne de relevé à un bordereau depuis l'interface

Status: ✅ done
Type: feature
Files: `backend/services/bank_service.py`, `backend/routers/bank_transactions.py`,
`backend/schemas/bank.py`, `backend/services/audit_service.py`,
`frontend/src/api/bank.ts`, `frontend/src/components/bank/BankMergeDepositDialog.vue`,
`frontend/src/views/BankView.vue`, `frontend/src/i18n/fr.ts`,
`tests/unit/test_bank_service.py`, `tests/integration/test_bank_api.py`,
`docs/user/manuel.md`, `CHANGELOG.md`

## What to build

- **Service** — `list_deposit_merge_candidates` renvoie les lignes provisoires
  (`manual`, non rapprochées, catégorie remise, même compte, **même montant**) qu'une
  ligne de relevé peut absorber, ordonnées par proximité de date ; refuse une ligne
  source qui n'est pas un relevé, déjà rapprochée, ou qui n'est pas une remise.
  `merge_deposit_transaction` applique la fusion sur la candidate désignée : la ligne du
  bordereau prend date, référence et source du relevé, la ligne importée est supprimée,
  les soldes sont recalculés.
- **API** — `GET /transactions/{id}/deposit-merge-candidates` et
  `POST /transactions/{id}/merge-deposit`, code d'erreur `BANK_DEPOSIT_MERGE_INVALID`,
  audit `bank.deposit.merge`.
- **Interface** — action de ligne « Rattacher à un bordereau enregistré » sur une ligne
  de relevé non rapprochée de catégorie remise, et dialogue de sélection.

## Acceptance criteria

- [x] Deux lignes pour un seul mouvement → après rattachement, une seule subsiste,
      portant le nom du bordereau, la date et la référence de la banque.
- [x] Une ligne d'un autre montant n'est pas proposée et son rattachement est refusé.
- [x] Une ligne manuelle, déjà rapprochée, ou qui n'est pas une remise, ne peut pas
      servir de source.
- [x] L'action n'apparaît que sur une ligne de relevé non rapprochée de type remise.

## Blocked by

None.
