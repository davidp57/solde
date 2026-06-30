# BIZ-222 — Net à payer auto-rempli et validé dans le formulaire salaire

Status: ✅ done
Type: fix
Files: `frontend/src/views/SalaryView.vue`, `frontend/src/i18n/fr.ts`, `frontend/src/tests/views/SalaryView.spec.ts`, `CHANGELOG.md`, `docs/user/changelog-user.md`

## What to build

Le champ « Net à payer » (`form.net_pay`) est manuel, par défaut `0`, et découplé du
« Net calculé » affiché. On peut donc enregistrer une paie au net nul sans s'en rendre
compte (cause directe du trou WOLFF mai). On le rend auto-rempli, éditable, et validé.

- `watch` sur (`gross`, `employee_charges`, `tax`) → `form.net_pay = round2(gross −
  employee_charges − tax)`. Le champ reste **éditable** (une saisie manuelle tient
  jusqu'au prochain changement d'un composant).
- À l'ouverture en **mode édition**, charger la valeur stockée sans la faire écraser par
  le watch au montage (garde déjà présente : ne synchroniser que sur changement réel).
- `save()` : refuser (toast d'avertissement) si `net_pay <= 0`, avec une clé i18n
  dédiée. Ne pas envoyer le payload tant que le net est nul.

## Acceptance criteria

- [ ] Modifier brut/charges/impôt met à jour automatiquement le « Net à payer ».
- [ ] Le « Net à payer » reste modifiable à la main.
- [ ] L'enregistrement est bloqué avec un message clair si net ≤ 0.
- [ ] En édition, le net stocké s'affiche correctement (pas écrasé à l'ouverture).
- [ ] Toutes les chaînes passent par i18n (`fr.ts`).

## Blocked by

None — frontend indépendant.
