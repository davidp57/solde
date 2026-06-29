# BIZ-218 — Historique des relances : colonne `reminder_dates` + append à l'envoi

Status: ⬜ ready
Type: feat
Files: `backend/models/invoice.py`, `backend/alembic/versions/`, `backend/schemas/invoice.py`, `backend/services/invoice.py`, `backend/routers/invoice.py`, `tests/unit/`, `tests/integration/`

## What to build

Socle backend de l'historique des relances, sur la facture **client**.

1. Ajouter une colonne `reminder_dates` à `Invoice` : liste de dates ISO, type JSON,
   défaut `[]` (jamais `NULL`). Migration Alembic (`NNNN_short_description.py`, séquence
   zéro-paddée).
2. Exposer `reminder_dates` dans le schéma de lecture de la facture (et donc dans l'API
   de liste/détail) pour que le front lise la dernière date sans appel dédié.
3. Append de la date du jour (`date.today()`) à `reminder_dates` **uniquement** à l'envoi
   d'un email de **relance** réussi (type `reminder` — cf. BIZ-220 pour la distinction de
   type côté flux). Aucun append pour l'envoi `initial`, ni si l'envoi SMTP échoue.

Pas de tri/filtre SQL sur `reminder_dates` (volume faible). Pas de saisie manuelle.

## Acceptance criteria

- [ ] `Invoice.reminder_dates` existe, type JSON, défaut `[]`, migration Alembic appliquée.
- [ ] Les factures existantes obtiennent `[]` (pas de `NULL`).
- [ ] `reminder_dates` est renvoyé par l'API (liste + détail facture).
- [ ] Un envoi `reminder` réussi append la date du jour ; un échec SMTP n'append rien.
- [ ] Un envoi `initial` (DRAFT→SENT) n'append jamais de date.
- [ ] Tests unitaires (service) + intégration (API) couvrant append / non-append.

## Blocked by

None — can start immediately (socle du lot).
