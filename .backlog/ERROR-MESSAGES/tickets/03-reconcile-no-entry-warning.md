# BIZ-263 — Avertir avant un rapprochement direct qui ne génère aucune écriture

Status: ✅ done
Type: fix
Files: `frontend/src/views/BankView.vue`, `frontend/src/i18n/fr.ts`, `docs/user/manuel.md`

## Contexte

Tranché par David le 04/10/2026 (option a) : « Créer un règlement client » reste proposé sur « Autre crédit », catégorie par défaut d'un crédit non reconnu. Le piège est le bouton « Rapprocher », qui sur ces catégories ne passe aucune écriture.

## Acceptance criteria

- [x] « Rapprocher » sur une ligne `other_credit`, `other_debit`, `customer_payment` ou `supplier_payment` demande confirmation, en nommant la catégorie.
- [x] « Tout rapprocher » et « Rapprocher avant… » demandent confirmation quand la sélection contient de telles lignes, avec leur nombre.
- [x] Aucune confirmation pour les autres catégories.
- [x] Manuel corrigé : « Rapprocher » ne choisit pas de paiement.
