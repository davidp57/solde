# TEC-211 — Garde-fou : régénérer le PDF d'une facture si le fichier est manquant

Status: ✅ done
Type: feat
Files: `backend/services/pdf_service.py`, `backend/services/invoice.py`, `backend/routers/invoice.py`, `tests/unit/`, `tests/integration/`

## What to build

Aujourd'hui la régénération à la demande ne se déclenche que si `invoice.pdf_path`
est **vide**. Étendre la consultation/le téléchargement du PDF d'une facture pour
**régénérer le PDF dès que le fichier référencé est absent du disque**, indépendamment
de `pdf_path`. Le PDF régénéré est ré-écrit à son emplacement attendu et servi.

Périmètre : le flux `GET /{id}/file` (et tout point qui sert le PDF d'une facture).
Réutiliser le service de génération WeasyPrint existant (`pdf_service`, import à la
génération pour respecter le budget RAM).

## Acceptance criteria

- [ ] Quand le fichier pointé par `pdf_path` est absent, le PDF est régénéré puis servi.
- [ ] Le comportement existant (régénération si `pdf_path` vide) est préservé.
- [ ] Aucune régénération inutile quand le fichier est présent.
- [ ] Pas de régression sur les factures archivées (le PDF figé est servi s'il existe).

## Blocked by

None — can start immediately
