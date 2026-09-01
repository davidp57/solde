# TEC-254 — Le compteur d'opérations à rapprocher ne mesurait pas le bon ensemble

Status: ✅ done
Type: fix
Files: `backend/services/checklist_service.py`,
`frontend/src/components/checklist/ChecklistPanel.vue`, `frontend/src/i18n/fr.ts`,
`tests/unit/test_checklist_service.py`, `docs/user/manuel.md`, `CHANGELOG.md`

## What to build

Le signal `unreconciled` comptait toute ligne `reconciled = False` du journal. En
production cela donnait **212** alors que trois restaient réellement à traiter :

| source | nombre | nature |
|---|---|---|
| `import` | 209 | reprise de l'historique à la mise en service (2024-2025) |
| `system_opening` | 1 | solde d'ouverture |
| `import_ofx` | 4 | le vrai reste, dont une ligne postérieure au mois traité |

Le compteur ne retient plus que les sources de **relevé** (`import_ofx`, `import_csv`,
`import_qif`), datées **au plus tard à la fin du mois traité** — un export « toutes les
opérations disponibles » ramène aussi le mois suivant. Les lignes `manual` — une remise
confirmée avant l'arrivée de son relevé, que seul un import futur peut solder — sont
comptées dans un champ `awaiting` distinct, mentionné dans le libellé seulement s'il est
non nul.

## Acceptance criteria

- [x] La reprise historique et le solde d'ouverture ne sont jamais comptés.
- [x] Une ligne de relevé postérieure au mois traité n'est pas comptée.
- [x] Les remises en attente de relevé sont comptées à part, pas avec le reste.
- [x] Le libellé ne mentionne les remises en attente que s'il y en a.

## Blocked by

BIZ-256.
