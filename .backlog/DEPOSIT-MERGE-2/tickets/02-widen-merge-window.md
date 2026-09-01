# TEC-251 — Élargir la fenêtre de fusion à ± 10 jours

Status: ✅ done
Type: fix
Files: `backend/services/bank_service.py`, `tests/unit/test_bank_service.py`,
`.backlog/DEPOSIT-MERGE/PRD.md`, `CHANGELOG.md`

## What to build

`_DEPOSIT_MERGE_WINDOW_DAYS` passe de 3 à 10, avec le commentaire disant pourquoi la
date du bordereau reste déclarative. La garde « exactement une candidate » est
inchangée.

## Acceptance criteria

- [x] Une ligne provisoire au 09/08 et un crédit au 04/08 fusionnent (échouait avec 3).
- [x] Au-delà de 10 jours, toujours aucune fusion.
- [x] Deux candidates dans la fenêtre → toujours aucune fusion.

## Blocked by

TEC-250 (même fichier).
