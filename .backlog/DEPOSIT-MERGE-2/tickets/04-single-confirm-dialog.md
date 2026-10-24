# TEC-252 — Une seule boîte de confirmation par vue

Status: ✅ done
Type: fix
Files: `frontend/src/components/bank/BankDepositActionsDialog.vue`,
`frontend/src/views/DashboardView.vue`,
`frontend/src/tests/components/BankDepositActionsDialog.spec.ts`, `CHANGELOG.md`

## What to build

`BankDepositActionsDialog` montait son propre `<ConfirmDialog />` alors que `BankView`
en monte déjà un. Le service de confirmation de PrimeVue diffuse `require` à **toutes**
les instances : les deux s'ouvrent, et `accept()` ne remet `visible = false` que sur la
sienne (`primevue/confirmdialog`) — l'autre reste affichée, bouton actif, prête à
rejouer l'action (« Cannot update a confirmed deposit »).

Retirer l'instance locale ; ajouter `<ConfirmDialog />` à `DashboardView`, seule autre
vue hôte de `BankPendingDepositsPanel` et qui n'en montait pas.

## Acceptance criteria

- [x] Le composant ne monte plus de `ConfirmDialog` (test de non-régression).
- [x] La confirmation reste disponible depuis l'écran d'accueil.

## Blocked by

None.
