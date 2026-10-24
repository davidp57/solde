# BIZ-242 — Écran Documents

Status: ✅ done
Type: feature
Files: `frontend/src/api/document.ts`, `frontend/src/views/DocumentsView.vue`,
`frontend/src/router/index.ts`, `frontend/src/i18n/fr.ts`,
`frontend/src/components/AppSidebar.vue`, `frontend/src/tests/views/DocumentsView.spec.ts`

## What to build

- **Client API** `document.ts` : types et appels correspondant au ticket 02.
- **Vue `DocumentsView.vue`**, sur `/documents`, entrée de menu dans la section
  **Gestion** :
  - tableau : titre, exercice, étiquettes, date de dépôt, taille, actions ;
  - barre de filtres : recherche, sélecteur d'exercice (dont « Sans exercice »),
    sélecteur d'étiquette alimenté par `/documents/tags` ;
  - bouton **Déposer un document** ouvrant une boîte de dialogue : choix du fichier,
    titre, exercice facultatif, étiquettes (saisie libre avec suggestion de l'existant),
    notes ;
  - action **Télécharger** sur chaque ligne ;
  - actions **Modifier** et **Supprimer** (avec confirmation) réservées à
    `secretaire+`, masquées pour `readonly` ;
  - rechargement de la liste après chaque dépôt, modification ou suppression ;
  - message d'attente pendant le dépôt, message d'erreur explicite en cas de refus
    (taille, type), repris du code renvoyé par le serveur.
- **Libellés** dans `fr.ts` sous la clé `documents.*` — aucun texte en dur.
- **Affichage de la taille** en Ko/Mo, et de la date de dépôt au format français.

## Acceptance criteria

- [ ] L'entrée « Documents » figure dans la section Gestion et mène à `/documents`.
- [ ] Le dépôt d'un fichier ajoute une ligne sans rechargement de page.
- [ ] Les filtres exercice, étiquette et recherche se combinent.
- [ ] « Sans exercice » ne montre que les documents non rattachés.
- [ ] La suppression demande confirmation puis retire la ligne.
- [ ] Un compte `readonly` ne voit ni le bouton de dépôt ni les actions de
      modification/suppression, mais peut télécharger.
- [ ] Un refus du serveur (taille, type) affiche un message explicite en français.
- [ ] Tests de la vue : rendu de la liste, application des filtres, masquage des actions
      pour `readonly`.

## Blocked by

02-documents-api
