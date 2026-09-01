# BIZ-261 — Action « Défaire le rapprochement » dans l'écran Banque

Status: ✅ done
Type: feature
Files: `frontend/src/api/bank.ts`, `frontend/src/views/BankView.vue`,
`frontend/src/i18n/fr.ts`, `frontend/src/tests/`, `CHANGELOG.md`,
`docs/user/manuel.md`, `docs/user/changelog-user.md`

## What to build

- **API** — `unreconcileTransaction(id)` dans `api/bank.ts`.
- **Menu de ligne** — une entrée « Défaire le rapprochement » dans `txMenuItems`, visible
  sur une opération **rapprochée**, avec confirmation. Le prédicat reste optimiste côté
  interface : c'est le serveur qui arbitre les cas règlement / bordereau / exercice clos,
  et son message explique par où passer — reproduire cette logique dans le frontend la
  ferait diverger.
- **Retour d'erreur** — les codes `RECONCILED_VIA_PAYMENT`, `RECONCILED_VIA_DEPOSIT`,
  `FISCAL_YEAR_CLOSED` et `NOT_RECONCILED` reçoivent leur message dans `fr.ts` (section
  des codes d'erreur) et `en.ts`, comme les codes existants.
- **Rafraîchissement** — s'appuyer sur la réponse du serveur plutôt que recharger la
  liste, conformément à TEC-248/TEC-246. La ligne repasse « à rapprocher » et ses actions
  contextuelles (Modifier, Supprimer) réapparaissent immédiatement.
- **Documentation** — une sous-section dans le manuel, à la suite de *Supprimer une
  opération* : ce que défait le geste, ce qu'il refuse et pourquoi.

## Acceptance criteria

- [x] L'entrée n'apparaît que sur une opération rapprochée, et demande confirmation.
- [x] Après succès, la ligne redevient « à rapprocher » sans rechargement de page, et
      propose de nouveau Modifier / Supprimer.
- [x] Un refus affiche le message du code renvoyé, qui nomme le chemin à emprunter.
- [x] Toutes les chaînes passent par i18n.

## Blocked by

BIZ-260 — l'endpoint.
