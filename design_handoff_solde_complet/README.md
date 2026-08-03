# Handoff complet — Refonte UI/UX Solde

Paquet consolidé pour implémentation avec **Claude Code**. Couvre l'ensemble du lot de refonte de **Solde** (Vue 3 `<script setup>` + PrimeVue thème Aura + Pinia) : tableau de bord, factures, écrans admin, **mode sombre** et **responsive**.

## Comment utiliser ce paquet
1. Dézippe le dossier à la racine de ton repo Solde (à côté de `frontend/`).
2. Dans Claude Code, attaque **un écran à la fois**. Suggestion d'ordre :
   1. **Tokens + mode sombre** (store de thème Pinia + tokens Aura clair/sombre) — socle de tout le reste.
   2. **`InvoiceWorkspace`** (composant factures mutualisé) — supprime le plus de duplication.
   3. **Tableau de bord**.
   4. **Utilisateurs**, puis **Système**.
   5. **Paramètres** (onglets + `AppSettingRow`) et **Supervision** (2 onglets).
   6. **Responsive** en dernière passe (breakpoints, table→cartes, drawer/tab-bar).
3. Prompt type : *« Lis `details/01-...md` et implémente la refonte du tableau de bord en suivant les composants Vue/PrimeVue et tokens existants. Ne touche pas aux écrans non concernés. »*

## Contenu
```
references/    4 maquettes .dc.html (prototypes à ouvrir au navigateur) + support.js (runtime, à ignorer)
screenshots/   captures de référence (refonte/ et admin/)
details/       les 2 specs détaillées (mapping écran → fichiers/composants/tokens)
README.md      ce fichier
```

### Maquettes (`references/`)
| Fichier | Écrans |
|---|---|
| `Solde - Refonte tableau de bord.dc.html` | Tableau de bord + Factures (clair) + recommandations |
| `Solde - Mode sombre.dc.html` | Utilisateurs + Système (sombre, pleine fidélité) + galerie du reste de l'app |
| `Solde - Responsive.dc.html` | Téléphone (dashboard, factures en cartes, drawer) + tablette + règles de breakpoints |
| `Solde - Admin (Parametres + Supervision).dc.html` | Paramètres (4 onglets) + Supervision (2 onglets) + mobile (accordéon) |

> Ce sont des **prototypes HTML**, pas du code à copier : ils montrent l'intention visuelle/comportementale. Reproduire dans le codebase via composants maison + tokens (jamais d'inline-styles). CDN Manrope + PrimeIcons requis pour l'aperçu.

### Specs détaillées (`details/`)
- **`01-dashboard-factures-darkmode-responsive.md`** — tableau de bord, factures (patron `InvoiceWorkspace` mutualisé clients/fournisseurs), tokens clair+sombre, responsive.
- **`02-admin-parametres-supervision.md`** — Paramètres en 4 onglets + motif `AppSettingRow` + barres d'enregistrement, Supervision en 2 onglets.

## Principes transverses (valables partout)
- **Réutiliser** les composants maison (`AppPage`, `AppPageHeader`, `AppPanel`, `AppWorklist`, `AppStatCard`, `AppDataTable`, `AppMobileCardList`, `AppDatePicker`, `AppFilterSegments`) et PrimeVue ; **aucun inline-style**.
- **Tokens du thème** clair/sombre — **parité sombre requise** sur tous les écrans. Manrope, primaire emerald, rayons **16/12 px**.
- **UI strings FR via i18n** (`i18n/fr.ts`).
- **Hiérarchiser par action** : héros + files de tâches (`AppWorklist`) plutôt que grilles de KPI égaux ; chiffres de référence non cliquables.
- **Couleur sémantique disciplinée** + signe + `tabular-nums` sur les montants ; icône **et** couleur (jamais la couleur seule).
- **Destructif isolé** (zone dangereuse, restauration « RESTAURER » en 2 étapes).
- **Exercice fiscal** géré à **un seul endroit** (store global + sélecteur topbar).
- **Responsive** : sidebar → tab-bar/drawer (mobile) ou rail d'icônes (tablette) ; tables → cartes ; cibles **≥ 44px**.
- **Conserver ce qui marche** : sur Supervision, bandeau d'état + file d'anomalies + restauration sécurisée sont déjà bons — ne pas redéfaire.

## Écrans NON couverts (mêmes patrons applicables)
Banque/rapprochement, Caisse, Salaires, Contacts, Comptabilité (Balance/Journal/Résultat), Imports — déclinables depuis les patrons ci-dessus (liste+table+filtres, formulaires, dashboard). Demander une déclinaison dédiée si besoin.
