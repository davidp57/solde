# BIZ-254 — Modèle de séance mensuelle et son API

Status: ✅ done
Type: feature
Files: `backend/models/checklist.py`, `backend/services/checklist_service.py`,
`backend/routers/checklist.py`, `backend/schemas/checklist.py`,
`alembic/versions/NNNN_monthly_checklist.py`, `tests/unit/test_checklist_service.py`,
`tests/integration/test_checklist_api.py`

## What to build

- **Modèle** — `checklist_sessions` (période : type `monthly` + mois traité, statut
  ouvert/clôturé, date de clôture) et `checklist_steps_state` (session, clé d'étape,
  coché, auteur, horodatage). Le type de période existe dès maintenant pour accueillir
  une checklist annuelle sans migration (décision 4).
- **Service** — ouvrir une séance (refuser si une autre est ouverte), cocher/décocher une
  étape, clôturer une séance en reportant les étapes non cochées vers la suivante,
  consulter une séance passée en lecture seule.
- **API** — séance courante, ouverture, bascule d'une étape, clôture, historique.
  Accès `tresorier` et plus.

Le mois proposé à l'ouverture suit la date : mois précédent avant le 15, mois courant
ensuite ; l'appelant peut imposer un autre mois.

## Acceptance criteria

- [x] L'état survit à un rechargement et à une session interrompue.
- [x] Une seule séance ouverte à la fois ; ouvrir la suivante exige de clôturer.
- [x] Clôturer une séance incomplète est possible et reporte les étapes non cochées.
- [x] Une séance clôturée est en lecture seule.
- [x] Les mois passés restent consultables.

## Blocked by

None.
