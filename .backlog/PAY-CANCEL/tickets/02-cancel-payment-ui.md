# BIZ-224 — Bouton d'annulation de règlement dans l'écran Paiements

Status: ✅ done
Type: feature
Files: `frontend/src/views/PaymentsView.vue`, `frontend/src/api/payments.ts`,
`frontend/src/i18n/fr.ts`, `frontend/src/tests/views/PaymentsView.spec.ts`,
`docs/user/manuel.md`, `docs/user/changelog-user.md`, `CHANGELOG.md`

## What to build

Exposer l'annulation de règlement dans l'écran Paiements, visible pour les seuls
administrateurs.

- **API front** — `cancelPayment(id)` et `getPaymentCancelPreview(id)` dans
  `api/payments.ts`, avec le type `PaymentCancelPreview`.
- **Action de ligne** — ajouter une action « Annuler le règlement » (icône poubelle,
  `severity: 'danger'`) à côté de « Modifier », rendue **uniquement** si
  `authStore.isAdmin`. Les autres rôles ne la voient pas.
- **Boîte de confirmation** — à l'ouverture, appeler `cancel-preview` :
  - annulation possible et paiement libre → « Le règlement de 120,00 € du 12/06/2026 sera
    supprimé. Cette action est définitive. » ;
  - bordereau conservé → ajouter « Il sera retiré du bordereau de remise du 12/06/2026,
    dont le total passera de 340,00 € à 220,00 €. » ;
  - bordereau supprimé → ajouter « Ce règlement est le seul du bordereau du 12/06/2026 :
    le bordereau sera supprimé. » ;
  - annulation impossible → afficher le motif traduit et ne proposer que « Fermer ».
- **i18n** — toutes les chaînes dans `i18n/fr.ts` (y compris un libellé par code de
  refus : `PAYMENT_DEPOSITED`, `PAYMENT_SUPPLIER`, `PAYMENT_RECONCILED`,
  `FISCAL_YEAR_CLOSED`). Aucun texte en dur dans le composant.
- **Après succès** — toast de confirmation et rechargement de la liste.
- **Documentation** — section « Annuler un règlement saisi par erreur » dans le manuel
  utilisateur : qui peut le faire, jusqu'à quand, ce qui se passe pour le bordereau, et
  la marche à suivre pour ressaisir ensuite les règlements corrects.

## Acceptance criteria

- [ ] L'action n'apparaît pas pour un utilisateur secrétaire ou trésorier ; elle apparaît
      pour un admin.
- [ ] La confirmation affiche le bon texte dans les trois cas (paiement libre, bordereau
      conservé avec les deux totaux, bordereau supprimé).
- [ ] Un règlement inéligible affiche le motif en français et ne peut pas être annulé
      depuis la boîte de dialogue.
- [ ] Après annulation, la liste est rechargée et le règlement a disparu.
- [ ] Une erreur serveur affiche un toast d'erreur sans vider la liste.
- [ ] Aucune chaîne en dur : tout passe par `i18n/fr.ts`.

## Blocked by

BIZ-223 — a besoin de l'endpoint d'annulation et de `cancel-preview`.
