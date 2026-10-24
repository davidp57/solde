# BIZ-256 — Afficher le signal des étapes détectables

Status: ✅ done
Type: feature
Files: `backend/services/checklist_service.py`, `backend/routers/checklist.py`,
`frontend/src/components/checklist/`, `tests/unit/test_checklist_service.py`

## What to build

Pour la séance en cours, calculer et renvoyer un signal factuel par étape détectable :

| étape | signal renvoyé |
|---|---|
| Importer le relevé | date du dernier import et nombre d'opérations créées |
| Saisir les fiches de salaire | nombre de fiches pour le mois traité |
| Rapprocher les opérations | nombre d'opérations non rapprochées restantes |
| Comptage de caisse | date du dernier comptage |
| Préparer les bordereaux | montants en attente de remise (chèques, espèces) |
| Vérifier la sauvegarde | date et issue de la dernière sauvegarde |

Le signal est **affiché à côté de l'étape et ne coche rien** (décision 3). Il est
formulé comme un fait daté, pas comme un verdict : « relevé importé le 01/09,
12 opérations », jamais « fait ».

Aucun signal pour les étapes de jugement (l'application ne sait pas ce qui n'a pas été
saisi) ni pour les étapes externes.

## Acceptance criteria

- [x] Aucune étape n'est cochée automatiquement.
- [x] Chaque signal est daté et chiffré, jamais réduit à un booléen.
- [x] Une étape sans signal détectable n'affiche rien plutôt qu'un signal vide.
- [x] Le calcul des signaux ne ralentit pas l'ouverture de la fenêtre.

## Blocked by

BIZ-254, BIZ-255.
