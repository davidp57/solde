# Lot SCHEMA-DRIFT — Aligner les modèles ORM sur les migrations, et le vérifier en CI

Status: ⬜ ready
Branch: fix/schema-drift → PR → develop

## Problem Statement

Les modèles SQLAlchemy (`backend/models/`) et le schéma produit par les migrations
(`alembic upgrade head`) ne décrivent plus la même base. Rien ne le signale : la CI ne
compare jamais les deux, et les tests créent leur schéma par `Base.metadata.create_all`,
donc **à partir des modèles** — ils ne voient pas ce que la prod a réellement.

Constat du 2026-10-02 (après PR #168, qui rendait déjà visibles à Alembic les tables
`import_runs`, `import_operations`, `import_effects`) : sur une base vierge montée à
`head`, `alembic check` relève encore **17 écarts**. Une prochaine
`alembic revision --autogenerate` les embarquerait tous, dans une migration sans rapport,
et certains sont dangereux :

| Table | Écart détecté (autogénération proposerait…) | Risque |
|---|---|---|
| `accounting_entries` | **supprimer** l'index unique `ix_accounting_entries_entry_number_unique` (créé par 0052, absent du modèle) | **perte du garde-fou anti-doublon** de numéros d'écriture (correctif de course de 0052) |
| `accounting_entries` | ajouter `ix_accounting_entries_id` | bruit (index sur la clé primaire) |
| `accounting_rule_entries` | ajouter `ix_accounting_rule_entries_id` | bruit |
| `accounting_rules` | remplacer `ix_accounting_rules_trigger_type` non unique par un **unique** ; ajouter `ix_accounting_rules_id` | échec de migration en prod si deux règles partagent un `trigger_type` |
| `app_comments` | ajouter `ix_app_comments_id` | bruit |
| `app_settings` | `email_body_template` TEXT → VARCHAR(4000) ; `reminder_first_subject_template` et `reminder_next_subject_template` VARCHAR(4000) → VARCHAR(500) | réduction de longueur (non appliquée par SQLite, mais le modèle et la base divergent sur la limite réelle) |
| `bank_transaction_payments` | supprimer `ix_bank_transaction_payments_payment_id` | perte d'index utile aux jointures |
| `bank_transactions` | supprimer `ix_bank_transactions_reconciled` | perte d'index utile aux filtres « à rapprocher » |
| `chat_log` | supprimer `ix_chat_log_asked_at`, `ix_chat_log_user_id` | perte d'index |
| `fiscal_years` | remplacer `ix_fiscal_years_name` non unique par un **unique** ; ajouter `ix_fiscal_years_id` | échec de migration en prod si deux exercices portent le même nom |

## Solution

Faire converger modèles et migrations, **dans le bon sens pour chaque écart** — ni « le
modèle a toujours raison », ni « la base a toujours raison » :

- un index présent en base et utile (anti-doublon, jointure, filtre) → **le déclarer dans
  le modèle** ;
- un index déclaré par le modèle mais redondant (index sur une clé primaire, `index=True`
  sur `id`) → **le retirer du modèle** plutôt que de le créer ;
- une contrainte d'unicité voulue par le modèle mais absente en base → **migration** qui
  la crée, précédée d'un contrôle des doublons existants (la migration doit échouer avec
  un message clair, ou la décision documentée, plutôt que planter sur une erreur SQLite
  brute) ;
- une longueur de colonne divergente → aligner le modèle sur ce que l'écran et l'usage
  réel exigent (vérifier les longueurs effectivement stockées en prod avant de réduire).

Puis empêcher la dérive de revenir : un **test** qui monte une base à `head` et exige
`compare_metadata` vide, lancé par `pytest` donc par la CI existante.

## User Stories

1. En tant que développeur, je veux qu'`alembic revision --autogenerate` ne produise que
   le changement que je viens de faire, pour ne pas embarquer à mon insu la suppression
   d'un garde-fou.
2. En tant que trésorier, je veux que l'unicité des numéros d'écriture reste garantie par
   la base, pour qu'une double soumission ne crée jamais deux écritures de même numéro.
3. En tant que mainteneur, je veux que la CI échoue dès qu'un modèle et les migrations
   divergent, pour que l'écart soit corrigé dans la PR qui l'introduit.

## Implementation Decisions

- **Un seul ticket de convergence (TEC-256) et un ticket de garde (TEC-257), une PR.**
- Le test de garde vit côté backend (`tests/unit/test_schema_drift.py` ou équivalent),
  monte une base SQLite temporaire par `alembic upgrade head`, appelle
  `alembic.autogenerate.compare_metadata` avec **tous** les modules de `backend/models/`
  importés (même découverte `pkgutil` que `backend/alembic/env.py` et `tests/conftest.py`),
  et affiche les écarts lisiblement en cas d'échec.
- Écrire le test **d'abord** : il doit être rouge sur les 17 écarts ci-dessus, puis vert.
- Les migrations existantes ne sont **jamais réécrites** ; la convergence passe par une
  nouvelle migration `NNNN_…` quand la base doit changer.

## Testing Decisions

- Le test de garde est la mesure de succès : `compare_metadata` vide.
- Pour chaque contrainte d'unicité ajoutée : un test de migration sur une base contenant un
  doublon, qui vérifie le comportement choisi (refus explicite ou dédoublonnage documenté).
- Suite complète verte, et chaque fichier de test passant isolément.

## Out of Scope

- Le `SAWarning` « SQL-parsed foreign key constraint … could not be located in PRAGMA
  foreign_keys for table payments » émis pendant la comparaison : à noter dans la PR si sa
  cause est trouvée en passant, pas à traiter ici.

## Further Notes

- **Piège de mesure** : le paquet `backend` est installé en mode editable depuis le
  checkout principal `D:\dev\_misc\solde`. Un script Python lancé hors de la racine du
  worktree importe ce checkout-là (souvent en retard), pas le code de la branche. Lancer
  depuis la racine du worktree ou avec `PYTHONPATH=.`. Le 2026-10-02, une mesure faite sans
  cette précaution a rapporté deux faux écarts sur `smtp_use_tls` / `smtp_security`.
- `DEBUG=true` est nécessaire pour instancier la config hors tests (sinon
  `jwt_secret_key must be configured`), et `DATABASE_URL` pointe la base temporaire.
