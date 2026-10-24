# BIZ-257 — Panneau latéral et réorganisation après premiers retours

Status: ✅ done
Type: fix
Files: `backend/services/checklist_steps.py`,
`frontend/src/components/checklist/ChecklistPanel.vue`,
`frontend/src/stores/checklist.ts`, `frontend/src/layouts/AppLayout.vue`,
`frontend/src/i18n/fr.ts`, `tests/unit/test_checklist_service.py`,
`docs/user/manuel.md`, `CHANGELOG.md`

## What to build

Quatre corrections issues du premier usage réel :

- **Panneau latéral** — la fenêtre modale imposait de la fermer pour agir et de la
  rouvrir pour cocher, dix-sept fois dans la séance. Un `Drawer` à droite, **non
  modal**, reste ouvert pendant qu'on travaille (masque transparent, `pointer-events:
  none`). Le composant est renommé `ChecklistPanel`, et `dialogVisible` devient
  `panelVisible`.
- **`salary_summary` retirée** — le récapitulatif mensuel fait doublon avec la
  vérification du net à la saisie de chaque fiche.
- **`supplier_cash_payments` ajoutée** — l'encodage des règlements de factures
  fournisseurs payés en espèces manquait, alors qu'il déplace la caisse.
- **Bloc `cash_and_deposits` scindé** en `cash` (règlements en espèces, mouvements
  divers, **puis** comptage) et `deposits` (bordereaux). Le comptage passe en dernier
  du bloc caisse : compter avant d'avoir tout saisi compare le tiroir à un total
  périmé. Le titre du bloc `deposits` nomme l'écran Banque, où les bordereaux se
  préparent réellement — le titre précédent laissait croire à l'écran Caisse.

## Acceptance criteria

- [x] Le panneau s'ouvre à droite et laisse l'application utilisable derrière lui.
- [x] Le comptage de caisse suit tous les mouvements du tiroir (test).
- [x] Les deux étapes de bordereau sont dans le bloc `deposits` et pointent vers
      l'écran Banque (test).
- [x] Dix-sept étapes, sept blocs.

## Blocked by

BIZ-254/255/256.
