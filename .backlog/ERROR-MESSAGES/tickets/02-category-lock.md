# BIZ-262 — Catégorie d'une opération rapprochée : verrou ciblé, cadenas, catégorie posée par le règlement

Status: ✅ done
Type: fix
Files: `backend/services/bank_service.py`, `backend/routers/bank_transactions.py`, `backend/schemas/bank.py`, `frontend/src/api/bank.ts`, `frontend/src/views/BankView.vue`, `docs/user/manuel.md`, `tests/integration/test_bank_api.py`

## Acceptance criteria

- [x] Rapprochement direct : la catégorie est refusée (`BANK_TRANSACTION_RECONCILED_LOCKED`) et `category_locked` vaut `true`.
- [x] Ligne portée par un règlement : la catégorie se modifie ; date, montant et compte restent refusés.
- [x] Créer ou rattacher un règlement client (fournisseur) passe la catégorie en `customer_payment` (`supplier_payment`).
- [x] Écran Banque : cadenas à la place du crayon, message adapté au rôle au clic, mis à jour sans rechargement après « Rapprocher ».
