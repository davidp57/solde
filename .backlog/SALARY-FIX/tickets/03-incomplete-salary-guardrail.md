# TEC-214 — Garde-fou : détecter et signaler un salaire incomplet

Status: ✅ done
Type: fix
Files: `backend/services/accounting_engine.py`, `backend/services/salary_service.py`, `tests/unit/test_accounting_engine.py`, `tests/unit/test_salary_service.py`, `CHANGELOG.md`

## What to build

L'étape 5 de `generate_entries_for_salary` saute en silence quand `net_pay <= 0`, tout
en générant la constatation : on obtient un salaire structurellement incomplet
(constaté mais non payé) sans aucun signal. Ajouter un garde-fou défensif.

- Dans `generate_entries_for_salary` : `log.warning(...)` lorsque `gross > 0` et
  `net_pay <= 0` (constatation générée sans paiement), avec l'`id`/le mois du salaire.
- Helper `find_incomplete_salaries(db)` dans `salary_service.py` : liste les salaires
  ayant des écritures `source_type=salary` **sans** ligne sur le compte de banque
  (`512100`) alors que `net_pay > 0`. Réutilisable pour un futur écran/contrôle.

## Acceptance criteria

- [ ] Un warning est journalisé quand un salaire au net ≤ 0 génère sa constatation.
- [ ] `find_incomplete_salaries` détecte un salaire constaté sans écriture de paiement.
- [ ] `find_incomplete_salaries` ignore les salaires complets (paiement présent).
- [ ] N'altère pas le comportement de génération existant (étapes 1-5 inchangées).

## Blocked by

None — défensif ; peut suivre TEC-213.
