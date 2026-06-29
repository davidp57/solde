# BIZ-221 — Exclure les irrécouvrables de « en retard » + bascule de segment

Status: ✅ done
Type: feat
Files: `frontend/src/composables/useInvoiceMetrics.ts`, `frontend/src/views/ClientInvoicesView.vue`, `frontend/src/i18n/fr.ts`, `frontend/src/tests/`

## What to build

Sortir les créances abandonnées de la vue « en retard » et permettre de les consulter.

1. **`isOverdueInvoice()` exclut `IRRECOVERABLE`** : une facture irrécouvrable, même échue
   avec un restant dû > 0, n'est plus « en retard ». Comme `isOverdueInvoice()` alimente
   aussi les métriques (« Restant en retard », « N en retard »), liste **et** chiffres sont
   alignés d'un coup.
2. **Bouton bascule dans le segment « en retard »** (pas de 6ᵉ segment), à deux états
   mutuellement exclusifs :
   - par défaut : factures **en retard** (donc hors irrécouvrables) ;
   - basculé : **toutes** les factures irrécouvrables (pas de filtre d'échéance), et rien
     d'autre.
   Réutiliser les clés i18n existantes `invoices.show_irrecoverable` / `hide_irrecoverable`
   si elles conviennent (sinon libellés « En retard » ⇄ « Irrécouvrables »).
3. **Pas de bouton « Relancer »** sur une facture irrécouvrable (dans la vue basculée, la
   relance n'a pas lieu d'être).

## Acceptance criteria

- [ ] `isOverdueInvoice()` renvoie `false` pour `IRRECOVERABLE` (échue, restant > 0 compris).
- [ ] Les métriques « Restant en retard » / « N en retard » excluent les irrécouvrables.
- [ ] Segment « en retard » par défaut : aucune irrécouvrable ; basculé : uniquement les
      irrécouvrables (toutes).
- [ ] Aucune action « Relancer » proposée sur une facture irrécouvrable.
- [ ] Strings via i18n. Tests Vitest (`isOverdueInvoice`, bascule, métriques).

## Blocked by

None — indépendant des autres tickets du lot (peut être réalisé isolément).
