# BIZ-226 — Exposer la bascule d'exercice dans l'écran Exercices

Status: ✅ done
Type: feature
Files: `frontend/src/views/FiscalYearView.vue`, `frontend/src/i18n/fr.ts`,
`frontend/src/tests/views/FiscalYearView.spec.ts`, `docs/user/manuel.md`,
`docs/user/changelog-user.md`, `CHANGELOG.md`

## What to build

Câbler les deux endpoints déjà disponibles mais appelés par aucun écran.

- **Fenêtre de clôture** — remplacer le `confirm.require` de `confirmClose` par un `Dialog`
  dédié qui appelle d'abord `getFiscalYearPreCloseChecksApi(fy.id)` :
  - avertissements listés sous un `Message severity="warn"` avec une phrase d'introduction ;
  - `Message severity="success"` + `pre_close_ok` quand la liste est vide ;
  - rappel que la reprise des soldes se fait ensuite via « Ouvrir le prochain exercice » ;
  - la clôture reste possible malgré les avertissements (ils informent, ils ne bloquent pas).
  La clôture administrative garde le `ConfirmDialog` existant.
- **Action « Ouvrir le prochain exercice »** — visible si `status === 'closed'` **et**
  qu'aucun exercice ne commence après `end_date`. Ouvre un dialogue avec nom et dates
  pré-remplis : début = `end_date + 1 jour`, fin = `début + 1 an − 1 jour`, nom
  `AAAA-AAAA` (ou l'année seule si l'exercice ne traverse pas le Nouvel An). Valide via
  `openNextFiscalYearApi`, qui génère les reports à nouveau.
- **Dates formatées depuis les composantes locales** (`getFullYear`/`getMonth`/`getDate`),
  **pas** `toISOString()` — sinon la frontière d'exercice recule d'un jour à l'est de
  Greenwich.
- **i18n** — réutiliser les clés déjà présentes (`open_next`, `open_next_ok`,
  `pre_close_checks`, `pre_close_ok`), ajouter celles qui manquent. Aucun texte en dur.
- Action disponible en mobile comme en desktop.

## Acceptance criteria

- [ ] La fenêtre de clôture affiche les avertissements renvoyés par les pré-contrôles.
- [ ] Sans avertissement, elle affiche « Aucun problème détecté » et la clôture reste
      possible.
- [ ] « Ouvrir le prochain exercice » est absent sur un exercice ouvert, présent sur un
      exercice clôturé sans successeur, absent dès qu'un exercice postérieur existe.
- [ ] Sur un exercice août→juillet, le dialogue propose `2026-08-01 → 2027-07-31` nommé
      `2026-2027`, et l'appel part avec ce payload.
- [ ] Le manuel décrit la procédure de fin d'exercice et met en garde contre « Nouvel
      exercice », qui ne reporte aucun solde.

## Blocked by

None.
