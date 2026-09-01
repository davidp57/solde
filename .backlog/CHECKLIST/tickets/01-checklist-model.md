# BIZ-254 — Modèle de checklist mensuelle et son état

Status: ⬜ ready
Type: feature
Files: à définir après le gril — dépend de la question ouverte n° 2 (base ou navigateur)

## What to build

Le support de l'état : pour un mois donné, quelles étapes sont cochées, par qui et quand.

Deux options exclusives, à trancher :
- **En base** : table `monthly_checklists` (mois, étape, coché, auteur, horodatage) +
  migration Alembic + API. Partagé entre postes et utilisateurs, historisable.
- **Dans le navigateur** : `localStorage`. Aucun changement de schéma, mais l'état est
  propre au poste et invisible pour un second utilisateur.

## Acceptance criteria

- [ ] L'état survit à un rechargement et à une session interrompue.
- [ ] Un nouveau mois démarre avec une liste vierge.
- [ ] Les mois passés restent consultables.

## Blocked by

Questions ouvertes 1, 2, 6 du PRD.
