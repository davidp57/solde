# BIZ-256 — Détection automatique des étapes déjà faites

Status: ⬜ ready
Type: feature
Files: `backend/services/dashboard_service.py` (ou service dédié), `backend/routers/`

## What to build

Étapes détectables sans ambiguïté sur le mois courant :

| étape | signal |
|---|---|
| Relevé importé | une transaction `import_*` créée ce mois-ci |
| Fiches de salaire saisies | au moins une fiche pour le mois |
| Bordereaux confirmés | aucun bordereau non confirmé |
| Opérations rapprochées | aucune opération non rapprochée sur la période |
| Comptage de caisse | un comptage enregistré ce mois-ci |
| Sauvegarde | dernière sauvegarde réussie datée de ce mois |

Non détectables : tout ce qui relève du jugement (« toutes les factures du mois sont
saisies » — l'application ne sait pas ce qui n'a pas été saisi) et toutes les étapes
externes.

À trancher (question ouverte n° 3) : cocher d'office, ou afficher le signal à côté de la
case en laissant l'utilisateur décider.

## Acceptance criteria

- [ ] Aucune étape non détectable n'est cochée automatiquement.
- [ ] Le signal détecté est expliqué à l'utilisateur, pas seulement appliqué.

## Blocked by

BIZ-254, BIZ-255.
