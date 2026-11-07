# BIZ-266 — Bouton « Nouveau paiement » dans la vue Paiements

Status: ✅ done
Type: feature
Files: `frontend/src/views/PaymentsView.vue`,
`frontend/src/components/QuickPaymentWizard.vue`,
`frontend/src/tests/views/PaymentsView.spec.ts`,
`frontend/src/tests/components/QuickPaymentWizard.spec.ts`,
`docs/user/manuel.md`, `docs/user/changelog-user.md`, `CHANGELOG.md`

## What to build

- Bouton principal « Nouveau paiement » (`payments.new`, `pi pi-plus`) dans l'en-tête de `PaymentsView`, slot `actions` d'`AppPageHeader`, affiché sur ordinateur et sur téléphone.
- Il ouvre `QuickPaymentWizard`.
- `QuickPaymentWizard` émet `saved` après un `createPayment` réussi ; `PaymentsView` y répond par `loadPayments()`.
- `?create=1` sur la route `payments` ouvre l'assistant au montage, puis `router.replace` retire le paramètre.

## Acceptance criteria

- [x] Le bouton est présent et ouvre l'assistant.
- [x] `?create=1` ouvre l'assistant et retire le paramètre de l'URL.
- [x] Un paiement enregistré dans l'assistant recharge la liste.
- [x] L'assistant n'émet pas `saved` quand l'enregistrement échoue.
- [x] Le tableau de bord continue d'ouvrir l'assistant comme avant.
