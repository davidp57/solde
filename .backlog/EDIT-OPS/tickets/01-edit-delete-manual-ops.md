# BIZ-169 — Édition/suppression des opérations bancaires manuelles

Status: ⬜ ready
Type: feat
Files: `backend/routers/bank.py`, `backend/services/bank_service.py`, `frontend/src/views/BankView.vue`, `frontend/src/i18n/fr.ts`, `tests/`

## What to build

Permettre de modifier ou supprimer les opérations bancaires créées manuellement depuis
`BankView` (opérations sans source d'import).

- Backend : endpoints d'édition et de suppression restreints aux opérations manuelles
  (écriture : Trésorier+) ; garde-fous sur opération rapprochée / ayant généré une
  écriture comptable.
- Frontend : actions « Modifier » / « Supprimer » sur les lignes manuelles uniquement,
  via le pattern d'actions de ligne mutualisé (`AppRowActions`), confirmation pour la
  suppression. Toutes les chaînes via i18n (`fr.ts`).

## Acceptance criteria

- [ ] Une opération manuelle peut être éditée (montant, date, libellé, catégorie).
- [ ] Une opération manuelle peut être supprimée (avec confirmation).
- [ ] Les opérations issues d'un import ne sont ni éditables ni supprimables.
- [ ] Garde-fous sur opération rapprochée / avec écriture liée respectés.

## Blocked by

None — can start immediately
