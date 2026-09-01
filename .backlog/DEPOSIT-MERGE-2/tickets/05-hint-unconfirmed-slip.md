# BIZ-252 — Nommer le bordereau non confirmé au lieu d'une impasse

Status: ✅ done
Type: feature
Files: `frontend/src/components/bank/BankMergeDepositDialog.vue`,
`frontend/src/i18n/fr.ts`,
`frontend/src/tests/components/BankMergeDepositDialog.spec.ts`,
`docs/user/manuel.md`, `CHANGELOG.md`

## What to build

Quand `list_deposit_merge_candidates` ne renvoie rien, chercher parmi les bordereaux
**non confirmés** (`listDeposits({confirmed: false})`) celui du même type (chèques /
espèces, déduit de la catégorie de la ligne) et du même montant, et l'annoncer avec sa
date et la marche à suivre. Un échec de cette recherche complémentaire ne doit pas
masquer le dialogue : repli silencieux sur le message générique.

## Acceptance criteria

- [x] Bordereau du bon montant en attente → message le nommant, avec sa date.
- [x] Bordereau d'un autre type ou d'un autre montant → message générique.
- [x] Candidats présents → les bordereaux en attente ne sont pas interrogés.
- [x] Erreur réseau sur cette recherche → message générique, pas d'erreur affichée.

## Blocked by

TEC-250/251 + BIZ-251 (le dialogue lui-même).
