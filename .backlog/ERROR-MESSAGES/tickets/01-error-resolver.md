# TEC-260 — Résolveur central des messages d'erreur

Status: ✅ done
Type: fix
Files: `frontend/src/utils/errorUtils.ts`, `frontend/src/i18n/fr.ts`, `frontend/src/i18n/en.ts`, vues et composants à `catch` générique, `frontend/src/tests/utils/errorUtils.spec.ts`

## Acceptance criteria

- [x] Un code présent dans `api_errors` affiche son message français.
- [x] Un 403 affiche « Votre rôle ne permet pas cette action. ».
- [x] Une requête sans réponse affiche « Impossible de contacter le serveur… ».
- [x] Un code sans traduction affiche le texte du serveur, jamais « Une erreur est survenue » quand le serveur a donné une raison.
- [x] Plus aucun `catch` n'affiche le message générique sans passer par le résolveur.
