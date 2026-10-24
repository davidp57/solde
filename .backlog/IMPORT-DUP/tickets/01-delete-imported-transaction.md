# BIZ-258 — Supprimer une opération bancaire importée non rapprochée

Status: ✅ done
Type: feature
Files: `backend/services/bank_service.py`, `backend/routers/bank_transactions.py`,
`frontend/src/api/bank.ts`, `frontend/src/views/BankView.vue`,
`tests/integration/test_bank_api.py`, `CHANGELOG.md`

## What to build

Élargir la suppression d'une opération bancaire aux lignes issues d'un import **direct**
(OFX / CSV / QIF), tant qu'elles ne sont pas rapprochées. Sans cela, un doublon
d'import est incorrigible depuis l'interface.

- **Service** — `delete_manual_transaction` devient `delete_transaction` et s'appuie sur
  une constante `DELETABLE_SOURCES` (`manual`, `system_opening`, `import_csv`,
  `import_ofx`, `import_qif`). `import_excel` et le legacy `import` lèvent toujours une
  `ValueError` : l'import réversible tient le registre des lignes qu'il a créées, et en
  supprimer une dans son dos casserait l'annulation du run. Le refus sur opération
  rapprochée est inchangé.
- **Frontend** — un helper `canDeleteTransaction(tx)` exporté depuis `api/bank.ts`
  (miroir de `DELETABLE_SOURCES`, réutilisé par le dialogue d'import de BIZ-259). Dans
  `BankView`, l'action « Supprimer » suit ce prédicat ; « Modifier » reste sur
  `canEditOrDelete`, inchangé.

## Acceptance criteria

- [x] Une opération OFX non rapprochée peut être supprimée (204) et disparaît du relevé.
- [x] Une opération OFX rapprochée est refusée (422).
- [x] Une opération issue d'un import Excel est refusée (422), rapprochée ou non.
- [x] Une opération manuelle non rapprochée reste supprimable (comportement inchangé).
- [x] Les opérations importées ne sont toujours pas **éditables**.
- [x] La suppression est tracée dans `audit_logs` (inchangé, déjà en place).

## Blocked by

None — socle du lot.
