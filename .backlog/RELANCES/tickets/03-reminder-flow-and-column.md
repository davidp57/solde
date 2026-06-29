# BIZ-220 — Flux d'envoi de relance (« Relancer ») + colonne « dernière relance »

Status: ⬜ ready
Type: feat
Files: `backend/routers/invoice.py`, `backend/services/invoice.py`, `frontend/src/views/ClientInvoicesView.vue` (+ `InvoiceWorkspace.vue`), `frontend/src/api/`, `frontend/src/i18n/fr.ts`, `tests/integration/`, `frontend/src/tests/`

## What to build

Brancher la relance sur le **flux aperçu/envoi existant** et afficher la dernière relance.

1. **Type d'envoi explicite** : les endpoints d'aperçu (`/email-preview`) et d'envoi
   (`/send-email`) acceptent un type (`initial` | `reminder`). « Envoyer » sur un brouillon
   ⇒ `initial` ; « Relancer » sur une facture en retard ⇒ `reminder`. Le backend choisit le
   template via `email_service` (BIZ-219) et n'append une date (BIZ-218) que pour `reminder`.
2. **Bouton « Relancer »** : réutilise le même composant d'aperçu éditable que l'envoi
   initial — sujet + corps préremplis avec le bon template de relance et les variables
   résolues, le trésorier peut ajuster avant envoi.
3. **Colonne « dernière relance »** dans la liste : visible **uniquement** dans le segment
   « en retard ». Affiche la dernière date `reminder_dates` au format `JJ/MM/AAAA`, ou `—`
   si jamais relancée. Nombre de relances en **tooltip** uniquement (`{count} relance(s)`).

## Acceptance criteria

- [ ] `/email-preview` et `/send-email` portent le type d'envoi ; `reminder` ⇒ template de
      relance + append date, `initial` ⇒ comportement inchangé.
- [ ] « Relancer » ouvre l'aperçu éditable prérempli avec le bon template (1ère / suivante).
- [ ] La colonne « dernière relance » n'apparaît que dans le segment « en retard ».
- [ ] Date FR affichée si relancée, `—` sinon ; compteur en tooltip seulement.
- [ ] Strings via i18n. Tests intégration (API type d'envoi) + Vitest (colonne conditionnelle).

## Blocked by

BIZ-218, BIZ-219.
