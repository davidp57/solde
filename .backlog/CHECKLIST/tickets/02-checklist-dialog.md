# BIZ-255 — La fenêtre de checklist et son bouton d'en-tête

Status: ✅ done
Type: feature
Files: `frontend/src/components/checklist/`, `frontend/src/api/checklist.ts`,
`frontend/src/components/layout/` (en-tête), `frontend/src/i18n/fr.ts`,
`frontend/src/tests/components/`

## What to build

- **Bouton permanent dans l'en-tête** portant la progression (« 12/16 »), visible à
  partir du rôle trésorier. Sans séance ouverte, il propose de démarrer celle du mois
  proposé.
- **Fenêtre** listant les sept blocs et leurs étapes, cases à cocher, progression par
  bloc. Le bloc de reprise n'apparaît que s'il contient quelque chose.
- Les étapes ⇢ **externes** sont visuellement distinctes : rien dans l'application ne
  peut les constater.
- Chaque étape interne ouvre l'écran où elle se fait, sans fermer la séance en cours.
- **Clôture** : récapitulatif de ce qui n'a pas été coché, confirmation, report annoncé.
- Utilisable sur téléphone comme le reste de l'application.

La liste des étapes vit dans le code (décision 2), avec sa clé stable, son bloc, son
libellé i18n et sa cible de navigation.

## Acceptance criteria

- [x] Les sept blocs et leur ordre correspondent au PRD.
- [x] Une étape externe est reconnaissable au premier coup d'œil.
- [x] Cocher depuis n'importe quel écran, sans revenir à l'accueil.
- [x] La clôture affiche ce qui reste non coché avant de demander confirmation.
- [x] Lisible et utilisable sur mobile.

## Blocked by

BIZ-254.
