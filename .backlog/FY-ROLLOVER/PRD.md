# Lot FY-ROLLOVER — Bascule d'exercice utilisable depuis l'interface

Status: ✅ done
Branch: feature/fiscal-year-rollover → PR → develop

## Problem Statement

Première bascule d'exercice réelle (2025-2026 → 2026-2027, exercices du 1er août au
31 juillet) : le moteur est complet côté serveur, mais **l'interface n'expose pas l'étape
qui reporte les soldes**.

- `POST /{id}/open-next` crée l'exercice suivant **et** génère les reports à nouveau pour
  tous les comptes de bilan — **aucun écran ne l'appelle**.
- `GET /{id}/pre-close-checks` signale balance déséquilibrée et écritures sans exercice —
  **aucun écran ne l'appelle** non plus.
- Les fonctions front existaient pourtant déjà (`openNextFiscalYearApi`,
  `getFiscalYearPreCloseChecksApi` dans `api/accounting.ts`) : du code mort, jamais câblé.
- Des clés i18n (`open_next`, `open_next_ok`, `pre_close_checks`, `pre_close_ok`)
  attendaient aussi leur écran.

Conséquence : l'utilisateur clôture, puis clique **Nouvel exercice** — le seul bouton
disponible — et obtient un exercice **sans aucun report à nouveau**. Banque, caisse,
créances et dettes repartent à zéro. Erreur silencieuse et pénible à rattraper.

Deuxième trou constaté sur le même cas : rien n'empêche de créer deux exercices qui se
**chevauchent**, ce qui rendrait `find_fiscal_year_for_date` ambigu — une écriture
tomberait dans l'un ou l'autre selon l'ordre de tri.

## Solution

- **A (BIZ-226)** — L'écran Exercices expose la bascule complète : les vérifications avant
  clôture s'affichent dans la fenêtre de clôture, et une action **« Ouvrir le prochain
  exercice »** apparaît sur un exercice clôturé sans successeur, avec nom et dates
  pré-remplis dans la continuité.
- **B (TEC-217)** — `create_fiscal_year` et `open_new_fiscal_year` refusent une période
  qui chevauche un exercice existant (`422 FISCAL_YEAR_OVERLAP`).
- **C** — Le manuel utilisateur documente la procédure de fin d'exercice, l'ordre à
  respecter, et le piège du bouton « Nouvel exercice ».

## User Stories

1. En tant que trésorier, je veux voir ce qui cloche **avant** de clôturer, parce que la
   clôture est irréversible.
2. En tant que trésorier, je veux ouvrir l'exercice suivant en reprenant les soldes, sans
   savoir qu'il existe deux façons de créer un exercice.
3. En tant que trésorier, je veux être empêché de créer deux exercices qui se chevauchent.

## Implementation Decisions

- **Bouton conditionnel** : « Ouvrir le prochain exercice » n'apparaît que si l'exercice
  est `closed` **et** qu'aucun exercice ne commence après sa date de fin. Évite les
  doublons sans avoir à interroger le serveur.
- **Dates pré-remplies** : début = lendemain de la fin de l'exercice clôturé, fin = douze
  mois moins un jour. Nom dérivé (`2026-2027`, ou l'année seule si l'exercice ne traverse
  pas le Nouvel An). Tout reste éditable.
- **Formatage des dates en composantes locales**, pas via `toISOString()` : à l'est de
  Greenwich, le passage en UTC décalait la frontière d'exercice d'un jour (bug attrapé par
  le test avant livraison).
- **Fenêtre de clôture dédiée** plutôt que le `ConfirmDialog` générique : il fallait
  afficher une liste d'avertissements, ce qu'un message d'une ligne ne permet pas. La
  clôture administrative garde le `ConfirmDialog` existant.
- **Avertissements non bloquants** : les pré-contrôles informent, ils n'interdisent pas la
  clôture — c'est le trésorier qui juge.

## Testing Decisions

- Avertissements de pré-clôture affichés ; cas « aucun problème détecté » ; clôture
  déclenchée à la confirmation.
- Action de bascule absente sur un exercice ouvert, présente sur un exercice clôturé sans
  successeur, absente dès qu'un exercice postérieur existe.
- Pré-remplissage sur un exercice août→juillet : `2026-08-01 → 2027-07-31`, nom
  `2026-2027` (ce test a détecté le décalage UTC).
- Backend : chevauchement refusé, période commençant le lendemain acceptée.

## Out of Scope

- Rattacher rétroactivement à un exercice les écritures créées sans exercice — le
  contournement est d'annuler puis ressaisir le règlement (lot PAY-CANCEL).
- Réouverture d'un exercice clôturé.
- Assistant multi-étapes de fin d'exercice (checklist guidée).
