# TEC-217 — Refuser deux exercices qui se chevauchent

Status: ✅ done
Type: fix
Files: `backend/services/fiscal_year_service.py`, `backend/routers/fiscal_year.py`,
`tests/unit/test_fiscal_year_service.py`, `CHANGELOG.md`

## What to build

`create_fiscal_year` accepte aujourd'hui n'importe quelle période, y compris une période
recouvrant un exercice existant. `find_fiscal_year_for_date` prend alors le premier
résultat trié : l'exercice d'une écriture devient dépendant de l'ordre de tri.

- Helper `_assert_no_overlap(db, start_date, end_date)` : lève `FiscalYearError` si un
  exercice satisfait `start_date <= end && end_date >= start`, en nommant l'exercice en
  conflit et ses dates.
- Appelé par `create_fiscal_year` **et** `open_new_fiscal_year`.
- Routeur : `POST /accounting/fiscal-years/` mappe `FiscalYearError` en
  `422 FISCAL_YEAR_OVERLAP` (l'endpoint ne rattrapait aucune exception typée).

## Acceptance criteria

- [ ] Créer un exercice recouvrant une période existante est refusé, exercice en conflit
      nommé dans le message.
- [ ] Un exercice démarrant le lendemain de la fin d'un autre est accepté (pas de jour
      commun).
- [ ] Le refus remonte en `422` avec le code `FISCAL_YEAR_OVERLAP`.
- [ ] `open-next` applique le même contrôle.

## Blocked by

None.
