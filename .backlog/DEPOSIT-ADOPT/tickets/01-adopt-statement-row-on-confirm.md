# BIZ-253 — Adopter la ligne du relevé à la confirmation du bordereau

Status: ✅ done
Type: feature
Files: `backend/services/bank_service.py`, `tests/unit/test_bank_service.py`,
`docs/user/manuel.md`, `CHANGELOG.md`

## What to build

`_adopt_statement_row_for_deposit(db, *, deposit, category, description, reference)` :
cherche une transaction non rapprochée de source relevé, sur le compte courant, du même
montant et de la **même** catégorie que le bordereau, dans ± `_DEPOSIT_MERGE_WINDOW_DAYS`
autour de `deposit.date`. Exactement une candidate → reprendre le libellé de Solde, la
marquer rapprochée, renvoyer la ligne. Sinon `None` (et journaliser l'ambiguïté), le
crédit provisoire étant alors créé comme avant.

Appelée par `confirm_deposit` pour les deux types de bordereau.

## Acceptance criteria

- [x] Relevé importé puis bordereau confirmé → une seule opération, celle du relevé,
      portant le nom du bordereau et rapprochée.
- [x] Pas de ligne au relevé → crédit provisoire créé comme avant, non rapproché.
- [x] Un dépôt d'espèces du même montant n'est pas adopté par un bordereau de chèques.
- [x] Deux lignes candidates → aucune adoption.
- [x] Ligne déjà rapprochée → aucune adoption.

## Blocked by

None.
