# BIZ-227 — Absorber la ligne de relevé dans la remise déjà enregistrée

Status: ✅ done
Type: feature
Files: `backend/services/bank_service.py`, `backend/routers/bank_import.py`,
`backend/schemas/bank.py`, `frontend/src/api/bank.ts`,
`frontend/src/components/bank/BankImportStatementDialog.vue`, `frontend/src/i18n/fr.ts`,
`tests/unit/test_bank_service.py`, `tests/integration/test_bank_ofx_qif_api.py`,
`docs/user/manuel.md`, `CHANGELOG.md`

## What to build

- **Service** — `absorb_pending_deposit_transaction(db, payload)` dans `bank_service` :
  ne fait rien si la source du payload est `manual`/`system_opening`, ou si la catégorie
  détectée sur la ligne du relevé n'est pas une remise. Sinon, cherche les transactions
  `manual`, **non rapprochées**, de même compte et même montant, de catégorie remise,
  dans une fenêtre de ± 3 jours. Fusionne **uniquement** s'il y a exactement une
  candidate : la ligne prend la date, la référence et la source du relevé, garde sa
  description, puis les soldes sont recalculés. Plusieurs candidates → journaliser et
  renvoyer `None`.
- **Import** — dans `_import_rows`, tenter l'absorption avant `add_transaction` ; compter
  les fusions séparément des créations.
- **Schéma** — `BankImportResult.merged: int = 0` (défaut pour ne pas casser les appelants).
- **Interface** — le message de fin d'import ajoute une phrase quand des remises ont été
  rapprochées, sinon le total d'opérations importées paraît incohérent avec le fichier.

## Acceptance criteria

- [ ] Une remise confirmée dans Solde puis présente au relevé ne laisse **qu'une seule**
      opération, portant la référence bancaire et la source du relevé.
- [ ] La description de Solde (nom du bordereau) est conservée.
- [ ] Aucune fusion si le montant diffère, si la date sort de la fenêtre, si la ligne est
      déjà rapprochée, ou si la ligne du relevé n'est pas une remise.
- [ ] Deux candidates de même montant → aucune fusion, import normal, trace dans les logs.
- [ ] `merged` est renvoyé par l'API et affiché à l'utilisateur en fin d'import.
- [ ] Les trois formats (CSV, OFX, QIF) en bénéficient.

## Blocked by

None.
