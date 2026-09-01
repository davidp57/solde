# BIZ-255 — L'écran de checklist

Status: ⬜ ready
Type: feature
Files: `frontend/src/views/`, `frontend/src/i18n/fr.ts`, `frontend/src/router/`

## What to build

La liste ordonnée en six sections, cases à cocher, progression visible (n/20). Les étapes
externes (⇢) sont visuellement distinctes : elles ne se font pas dans l'application et
personne ne peut les détecter à la place de l'utilisateur.

Chaque étape mène à l'écran concerné, dans l'esprit de la liste de travail déjà présente
sur l'accueil (`AppWorklist`).

## Acceptance criteria

- [ ] Les six sections et leur ordre correspondent au PRD.
- [ ] Une étape externe est reconnaissable au premier coup d'œil.
- [ ] Chaque étape interne ouvre l'écran où elle se fait.
- [ ] La progression du mois en cours est lisible sans dérouler la liste.

## Blocked by

BIZ-254.
