# TEC-213 — Régénérer les écritures comptables à l'édition d'un salaire

Status: ✅ done
Type: fix
Files: `backend/services/salary_service.py`, `backend/services/accounting_engine.py`, `backend/routers/salary.py`, `tests/unit/test_salary_service.py`, `tests/integration/test_salary_api.py`, `CHANGELOG.md`

## What to build

`update_salary` ne régénère pas les écritures comptables : corriger un montant après
coup laisse le journal incohérent (cas WOLFF mai : paiement jamais créé). On régénère
les écritures du salaire quand un montant comptable change.

- Ajouter un helper de suppression dans `accounting_engine.py` :
  `delete_entries_for_source(db, source_type, source_id)` (supprime les
  `AccountingEntry` correspondants ; pas de FK cascade, suppression explicite).
- Dans `update_salary` : détecter si l'un de `gross`, `employee_charges`,
  `employer_charges`, `tax`, `net_pay` change réellement (comparer avant/après). Si oui :
  supprimer les écritures `source_type=salary, source_id=<id>` puis rappeler
  `generate_entries_for_salary`. Sinon (ex. notes seules), ne rien régénérer.
- **Garde-fou clôture** : refuser la régénération si l'exercice de la date d'écriture
  existante **ou** de la nouvelle date est `FiscalYearStatus.CLOSED` → exception typée
  mappée en `409` par le routeur. Aucune écriture modifiée en cas de refus.

## Acceptance criteria

- [ ] Éditer un montant régénère les écritures : le paiement (421000/512100) apparaît
      quand `net_pay > 0`, même s'il manquait avant.
- [ ] Éditer uniquement les notes ne touche aucune écriture.
- [ ] Régénération refusée (409) si l'exercice concerné est clôturé ; écritures intactes.
- [ ] Les écritures régénérées partagent le `group_key` `salary:<id>` et `source_id`.
- [ ] `delete_entries_for_source` est couvert par un test unitaire.

## Blocked by

None — fix de fond, à faire en premier.
