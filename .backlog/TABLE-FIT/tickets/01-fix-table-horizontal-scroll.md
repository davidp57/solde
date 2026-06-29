# TEC-212 — Supprimer le scroll horizontal des tableaux sur grand écran

Status: ⬜ ready
Type: fix
Files: `frontend/src/views/BankView.vue`, `frontend/src/assets/main.css`, autres vues à `DataTable` (audit), `frontend/src/tests/`

## What to build

Faire en sorte que les tableaux se contraignent à la largeur disponible et ne provoquent
plus de scroll horizontal sur grand écran. La banque est l'écran de repro ; le fond est
transversal (pattern `DataTable` partagé).

1. **Diagnostiquer** la cause exacte du débordement sur `BankView` en conditions réelles
   (largeurs figées des colonnes + padding cellules PrimeVue + absence de responsive).
2. **Corriger BankView** : rendre la colonne « description » (et autres colonnes texte)
   **flexible** pour absorber l'espace ; ne conserver de largeur fixe que là où c'est
   justifié (montant, solde, source) ; contraindre la table à son conteneur.
3. **Centraliser** la règle dans le style partagé des tableaux (`.app-data-table` dans
   `main.css`) plutôt que de la dupliquer par écran, pour qu'elle profite aux autres vues.
4. **Auditer visuellement** les autres vues larges (au moins `AccountingJournalView`,
   `SupplierInvoicesView`, `ClientInvoicesView`) et corriger les cas résiduels.
5. **Préserver** un scroll horizontal uniquement sous la largeur seuil (mobile).

## Acceptance criteria

- [ ] `BankView` : aucun scroll horizontal sur grand écran ; toutes les colonnes (dont
      actions « Importer ») visibles.
- [ ] La règle est centralisée dans le style partagé, pas dupliquée écran par écran.
- [ ] `AccountingJournalView`, `SupplierInvoicesView`, `ClientInvoicesView` : pas de scroll
      horizontal sur grand écran après le fix.
- [ ] Le scroll réapparaît proprement sous la largeur seuil (mobile), sans perte de lisibilité.
- [ ] Aucune régression de mise en page sur les autres vues à tableau.

## Notes

Si l'audit transversal révèle des ajustements manuels lourds par écran, scinder en un
second ticket dédié (cf. PRD).

## Blocked by

None — can start immediately.
