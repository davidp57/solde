# BIZ-249 — Saisie explicite du montant pour un règlement en espèces

Status: ⬜ ready
Type: feature
Files: `frontend/src/components/invoices/InvoicePaymentDialog.vue`,
`frontend/src/components/QuickPaymentWizard.vue`,
`frontend/src/composables/useCashPaymentGuard.ts` (nouveau),
`frontend/src/i18n/fr.ts`,
`frontend/src/tests/components/InvoicePaymentDialog.spec.ts`,
`frontend/src/tests/components/QuickPaymentWizard.spec.ts`,
`docs/user/manuel.md`, `docs/user/changelog-user.md`, `CHANGELOG.md`

## What to build

Retirer le pré-remplissage automatique du montant **quand le mode est « espèces »**, dans
les deux points de saisie d'un règlement client.

- **Composable** — `useCashPaymentGuard(method, remaining, cashBalance)` dans
  `frontend/src/composables/`, exposant :
  - `shouldClearAmount` — vrai quand `method === 'especes'` ;
  - `projectedCashBalance` — `cashBalance + montant saisi`, ou `null` hors espèces ;
  - le libellé du bouton de report, montant formaté inclus.
- **Dialogue fiche facture** (`InvoicePaymentDialog.vue`) :
  - à l'ouverture, `form.amount` vaut `remainingForInvoice(invoice)` **sauf** si le mode
    initial est « espèces » — dans ce cas, champ vide (remplace la ligne 153) ;
  - un `watch` sur `form.method` vide le montant au passage en espèces et le repropose au
    retour vers un autre mode (étendre le `watch` existant, ligne 164) ;
  - sous le champ, un bouton secondaire **« Solde dû (X,XX €) »** qui remplit le champ ;
  - en mode espèces, une ligne d'information : solde de caisse actuel → solde après ce
    règlement, rafraîchie à chaque frappe. Le solde vient de `getCashBalance()`
    (`api/cash.ts:85`), chargé à l'ouverture du dialogue ; si l'appel échoue, la ligne est
    simplement masquée (aucun blocage de la saisie).
- **Wizard rapide** (`QuickPaymentWizard.vue`) : même comportement, en remplaçant le
  pré-remplissage de la ligne 304 et en réutilisant le composable.
- **i18n** — nouvelles clés sous `payments.*` (libellé du bouton de report, ligne d'effet
  caisse). Aucune chaîne en dur.
- **Non touché** : les validations existantes (montant > 0, montant ≤ solde dû), le mode
  chèque et son numéro obligatoire, et `BankClientPaymentDialog` — le montant y vient du
  relevé bancaire, qui fait foi.

## Acceptance criteria

- [ ] Dialogue ouvert avec « espèces » sélectionné : le champ montant est **vide**.
- [ ] Passer de « chèque » à « espèces » vide le montant ; revenir à « chèque » le
      repropose au solde dû.
- [ ] Le bouton « Solde dû » remplit le champ avec le solde dû exact, au centime.
- [ ] Enregistrer avec un montant vide ou nul reste refusé, avec le message existant.
- [ ] Un montant **inférieur** au solde dû est toujours accepté ; un montant
      **supérieur** est toujours refusé (non-régression).
- [ ] En mode espèces, le solde de caisse projeté s'affiche et suit la saisie ; il vaut
      `solde courant + montant saisi`.
- [ ] Si `getCashBalance()` échoue, la ligne d'effet caisse disparaît et la saisie reste
      possible.
- [ ] Le comportement des deux points de saisie est identique.
- [ ] `docs/user/manuel.md` (section *Enregistrer un règlement*) décrit la saisie
      explicite pour les espèces ; `docs/user/changelog-user.md` mentionne le changement.

## Blocked by

None — ticket unique du lot.
