# Lot CREANCES-RAPPEL — Rappel créances exercice/historique sur les factures client (post-RF)

Status: 🧑 waiting-human
Branch: feat/receivables-reminder → PR → develop

## Problem Statement

Le lot RF (BIZ-206) a remplacé les 6 KPI des factures client par l'`InvoiceFunnelHero`,
qui agrège le **jeu de factures affiché** (reste à encaisser, encaissé, à venir, en
retard). Ce faisant, la distinction **créances de l'exercice** vs **créances totales +
report historique** (anciennement issue de `useInvoiceMetrics.receivableMetrics`) n'est
plus exposée — information utile au trésorier.

## Solution

Réafficher un **rappel discret** du report historique des créances ouvertes **hors
exercice courant** (ex. sous l'entonnoir ou en sous-texte), **sans** réintroduire la
grille de 6 KPI. `receivableMetrics` reste disponible dans le composable.

## User Stories

1. En tant que trésorier, je veux voir d'un coup d'œil le report de créances ouvertes
   hors exercice courant, sans revenir à l'ancienne grille de KPI.

## Implementation Decisions

- **À arbitrer en revue** : opportunité et emplacement exact du rappel. Ne pas
  réintroduire la grille de 6 KPI.

## Testing Decisions

- À définir une fois la décision prise (probable test Vitest sur l'affichage conditionnel
  du rappel à partir de `receivableMetrics`).

## Out of Scope

- Retour à la grille de 6 KPI factures.

## Further Notes

Ancien ticket hors-lot BIZ-210 (P3, créé 2026-06-18). **En attente d'arbitrage humain**
(`🧑 waiting-human`) : à rediscuter en revue de la PR Factures avant implémentation.
