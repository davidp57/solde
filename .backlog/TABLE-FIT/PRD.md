# Lot TABLE-FIT — Supprimer le scroll horizontal des tableaux sur grand écran

Status: ⬜ ready
Branch: fix/table-horizontal-scroll → PR → develop

## Problem Statement

L'écran Banque (`BankView.vue`) provoque un **scroll horizontal** gênant, y compris sur
grand écran où la place ne manque pas (la colonne d'actions « Importer » est tronquée à
droite). La cause n'est pas propre à la banque : ~18 vues partagent le même pattern
`DataTable` PrimeVue avec des **largeurs de colonnes figées** (`width` / `min-width`) et
**aucun mode responsive**, si bien que la table impose un plancher de largeur qui pousse
le conteneur au lieu de s'y contraindre. Écrans manifestement à risque : `BankView`,
`AccountingJournalView` (`wide`), `SupplierInvoicesView` (actions `13rem` + `12rem`).

## Solution

Corriger le **fond, de façon transversale** : faire en sorte qu'un tableau se contraigne
à la largeur disponible et ne déclenche un scroll horizontal qu'en **dernier recours**
(petits écrans / mobile), pas sur grand écran. Concrètement (à confirmer au diagnostic) :

- assouplir les largeurs figées — la colonne « description » devient **flexible**
  (absorbe l'espace), les largeurs fixes ne restent que là où c'est justifié (montant,
  solde, source) ;
- centraliser la règle dans le style partagé (`.app-data-table`) plutôt que la dupliquer
  par écran, pour qu'elle bénéficie à toutes les vues à tableau ;
- conserver un scroll **uniquement** sous une largeur seuil (mobile), pas sur desktop.

## User Stories

1. En tant qu'utilisateur sur grand écran, je veux voir l'intégralité d'un tableau (Banque
   et autres) sans scroll horizontal, puisque la place est largement suffisante.

## Implementation Decisions

- **Diagnostic d'abord sur `BankView`** (écran de repro), puis dériver une règle générique.
- **Fix centralisé** dans le style partagé des tableaux quand c'est possible, afin qu'il
  s'applique aux autres vues sans réécriture écran par écran.
- **Scroll toléré uniquement sur petit écran / mobile** (cohérent avec les lots MOB/RF).
- **Si le balayage transversal s'avère lourd** (ajustements manuels spécifiques à certains
  écrans), scinder en cours de route en un second ticket dédié à l'audit par écran.

## Testing Decisions

- Vérification **visuelle** sur grand écran : `BankView`, `AccountingJournalView`,
  `SupplierInvoicesView`, `ClientInvoicesView` — pas de scroll horizontal.
- Vérification que le scroll réapparaît correctement sous la largeur seuil (mobile), sans
  casser la lisibilité.
- Pas de régression de mise en page sur les autres vues à tableau.

## Out of Scope

- Refonte fonctionnelle des tableaux (colonnes, tri, pagination) — uniquement la largeur /
  le débordement horizontal.
- Refonte du layout mobile au-delà du comportement de scroll des tableaux.

## Further Notes

Issu d'une session `/grill-with-docs` (2026-06-29). Diagnostic : largeurs de colonnes
figées (~1232px de plancher sur BankView) + absence de responsive PrimeVue ; la cause
exacte du débordement sur grand écran reste à confirmer en conditions réelles à
l'implémentation.
