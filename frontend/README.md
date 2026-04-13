# Frontend Solde

Frontend Vue 3 de Solde, construit avec Vite, Pinia, Vue Router, PrimeVue et `vue-i18n`.

## Rôle du frontend

- consommer l'API FastAPI exposée sous `/api`
- afficher les workflows métier de l'association en français
- centraliser l'état applicatif côté client avec Pinia
- fournir une interface cohérente pour la comptabilité, la trésorerie et l'import Excel

## Stack

- Vue 3 + TypeScript
- Vite
- Pinia
- Vue Router
- PrimeVue + PrimeIcons
- `vue-i18n`
- Axios
- Vitest + Vue Test Utils

## Installation

```sh
npm install
```

## Développement local

```sh
npm run dev
```

Le serveur Vite tourne par défaut sur `http://localhost:5173`.

## Scripts disponibles

```sh
npm run dev
npm run build
npm run preview
npm run type-check
npm run test:unit
npm run lint
npm run format
```

## Conventions du projet

- les libellés visibles par l'utilisateur passent par les clés i18n
- les vues vivent dans `src/views/`
- les appels HTTP sont centralisés dans `src/api/`
- l'état global vit dans `src/stores/`
- les composants d'interface réutilisables vivent dans `src/components/`

## Variables d'environnement de développement

Certaines variables Vite sont utilisées pour accélérer les tests locaux.

- `VITE_DEV_AUTO_LOGIN`
- `VITE_DEV_AUTO_LOGIN_USERNAME`
- `VITE_DEV_AUTO_LOGIN_PASSWORD`

## Validation recommandée

```sh
npx vue-tsc --noEmit -p tsconfig.app.json
npx vue-tsc --noEmit
npx eslint src/
npx vitest run
```
