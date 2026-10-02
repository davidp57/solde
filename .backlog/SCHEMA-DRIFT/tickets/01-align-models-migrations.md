# TEC-256 / TEC-257 — Converger modèles et migrations, et garder la convergence en CI

Status: ✅ done
Type: chore
Files: `backend/models/accounting_entry.py`, `backend/models/accounting_rule.py`,
`backend/models/app_comment.py`, `backend/models/app_settings.py`,
`backend/models/bank.py`, `backend/models/chat_log.py`, `backend/models/fiscal_year.py`,
`backend/alembic/versions/NNNN_…py` (si la base doit changer),
`tests/unit/test_schema_drift.py` (nouveau), `CHANGELOG.md`

## What to build

1. **TEC-257 d'abord (test rouge)** — un test qui monte une base SQLite temporaire à
   `head`, compare avec `compare_metadata` (tous les modèles importés par découverte
   `pkgutil`) et échoue en listant les écarts. Il doit relever les 17 écarts du PRD.
2. **TEC-256** — traiter chaque écart du tableau du PRD dans le sens justifié :
   - `ix_accounting_entries_entry_number_unique` : déclarer l'unicité dans le modèle
     (ne surtout pas la perdre) ;
   - index sur `id` (`accounting_entries`, `accounting_rule_entries`, `accounting_rules`,
     `app_comments`, `fiscal_years`) : retirer `index=True` des clés primaires ;
   - index présents en base sur `bank_transaction_payments.payment_id`,
     `bank_transactions.reconciled`, `chat_log.asked_at`, `chat_log.user_id` : les déclarer
     dans les modèles ;
   - unicité de `fiscal_years.name` et `accounting_rules.trigger_type` : décider (et écrire
     pourquoi) entre migration créant la contrainte — avec contrôle préalable des doublons —
     ou retrait de `unique=True` du modèle si l'unicité est déjà garantie ailleurs ;
   - longueurs des trois colonnes de `app_settings` : aligner, après vérification de la
     longueur maximale réellement stockée.
3. Le test passe au vert ; suite complète verte ; chaque fichier de test isolé vert.

## Acceptance criteria

- [x] `tests/unit/test_schema_drift.py` échoue sur `develop` avant correctif (constaté et
      noté dans la PR).
- [x] Après correctif, `compare_metadata` est vide et `alembic check` répond
      « No new upgrade operations detected ».
- [x] L'index unique sur `accounting_entries.entry_number` existe toujours en base après
      `upgrade head`.
- [x] Toute nouvelle contrainte d'unicité a un test de migration avec doublon préexistant.
      *Sans objet : aucune contrainte n'est nouvelle (voir Résultat).*
- [x] Aucune migration existante modifiée.
- [x] Porte de qualité verte, CHANGELOG `[Non publié]`, version patch montée
      (`pyproject.toml` + `frontend/package.json`).

## Résultat (2026-10-02)

- Test de garde rouge sur `develop` : **17 écarts**, ceux du PRD. Vert après correctif ;
  `alembic check` : « No new upgrade operations detected ». **Aucune migration ajoutée.**
- **Unicité de `fiscal_years.name` / `accounting_rules.trigger_type` : déjà en base.**
  0007 et 0009 déclarent `unique=True` sur la colonne (contrainte `UNIQUE` de table, vue
  dans `sqlite_master` de la base locale) en plus d'un index simple. Le modèle disait
  « index unique », la base « contrainte unique + index simple » : même garantie, forme
  différente. Le modèle déclare désormais la forme réelle (`UniqueConstraint`), et un test
  vérifie qu'un doublon est refusé à `head`. Le risque « échec de migration en prod » du
  PRD n'existait donc pas.
- Longueurs `app_settings` : modèle aligné sur la base (`TEXT`, `VARCHAR(4000)`), ce qui
  élargit la limite déclarée sans rien réduire ; SQLite ne l'applique pas et ni le schéma
  Pydantic ni l'écran ne bornent ces champs. Valeurs stockées en base locale : toutes nulles.
- **Bug révélé par le garde-fou** : déclarer l'index unique de 0052 dans le modèle a fait
  échouer 8 tests d'import de salaires — tous les numéros d'écriture d'un import étaient
  identiques (session sans autoflush). Corrigé dans `_import_payments_salaries.py`.
