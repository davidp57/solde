# BIZ-210 — Rappel discret des créances hors exercice courant

Status: 🚫 wontfix
Type: feat
Files: `frontend/src/components/invoices/` (zone `InvoiceFunnelHero`), `frontend/src/composables/useInvoiceMetrics.ts`, `frontend/src/i18n/fr.ts`, `tests/`

## What to build

Réafficher un rappel discret du report historique des créances ouvertes **hors exercice
courant**, dérivé de `useInvoiceMetrics.receivableMetrics`, sous l'entonnoir
(`InvoiceFunnelHero`) ou en sous-texte. Ne pas réintroduire la grille de 6 KPI.

## Acceptance criteria

- [ ] Décision d'arbitrage prise (opportunité + emplacement) avant implémentation.
- [ ] Le rappel affiche le report de créances ouvertes hors exercice courant.
- [ ] La grille de 6 KPI n'est pas réintroduite.
- [ ] Chaînes via i18n (`fr.ts`).

## Blocked by

None — mais **en attente d'arbitrage humain** (à rediscuter en revue de la PR Factures).
