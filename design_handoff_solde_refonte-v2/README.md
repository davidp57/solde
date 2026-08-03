# Handoff — Refonte UI/UX Solde (tableau de bord, factures, admin + mode sombre)

## Overview
Ce paquet décrit une refonte de l'interface de **Solde** (gestion comptable d'association, Vue 3 + PrimeVue / thème Aura). Il couvre quatre écrans retravaillés et l'introduction d'un **mode sombre** cohérent à l'échelle de l'app :

1. **Tableau de bord** — hiérarchisé par action requise plutôt qu'une grille de 9 KPI égaux.
2. **Factures** (clients **et** fournisseurs) — fusionnés en un seul patron paramétré.
3. **Administration › Utilisateurs** — matrice de rôles vivante + filtres.
4. **Administration › Système** — état en tête, zone destructive isolée, anomalies en tâches.

L'objectif n'est pas un thème cosmétique : c'est une reprise de la **hiérarchie de l'information** et de la **mutualisation des composants dupliqués**.

## About the Design Files
Les fichiers de `references/` sont des **maquettes de référence en HTML** (`*.dc.html`) — des prototypes montrant l'intention visuelle et comportementale, **pas du code à copier tel quel**. Ouvre-les dans un navigateur pour voir le rendu (ils chargent Manrope + PrimeIcons par CDN ; `support.js` est le runtime du prototype, sans intérêt pour l'implémentation).

La tâche est de **recréer ces intentions dans le codebase existant** : Vue 3 `<script setup>` + PrimeVue (thème Aura) + Pinia, en réutilisant les composants maison (`AppPanel`, `AppPageHeader`, `AppStatCard`, `AppDataTable`…) et les tokens du thème. Ne pas introduire d'inline-styles façon prototype : tout passe par les tokens PrimeVue et les classes utilitaires déjà en place.

## Fidelity
**Hi-fi.** Couleurs, typographie, espacements et états sont définitifs et alignés sur le langage Solde (Manrope, emerald `#10b981`, surfaces slate). Reproduire fidèlement la mise en page et la hiérarchie ; mais **mapper les couleurs sur les tokens du thème** (voir Design Tokens) plutôt que de coller les hex en dur.

---

## Fichiers du codebase concernés
Chemins relatifs à `frontend/src/` du repo `davidp57/solde` :

| Écran / sujet | Fichier(s) à modifier ou créer |
|---|---|
| Tableau de bord | `views/DashboardView.vue` |
| Factures clients | `views/ClientInvoicesView.vue` |
| Factures fournisseurs | `views/SupplierInvoicesView.vue` |
| **Nouveau** patron mutualisé | `components/invoices/InvoiceWorkspace.vue` *(à créer)* |
| **Nouveau** badge statut | `components/invoices/InvoiceStatusBadge.vue` *(à créer)* |
| Utilisateurs | `views/UsersView.vue` |
| Système | `views/SystemView.vue` |
| Thème / tokens | `assets/main.css` (variables CSS) + config preset Aura |
| Bascule de thème | `layouts/AppLayout.vue` (topbar) + store Pinia `theme` *(à créer)* |

---

## Screens / Views

### 1. Tableau de bord (`DashboardView.vue`)
**Purpose** : donner au trésorier, en un coup d'œil, la trésorerie réelle et ce qui demande une action.

**Constat actuel** : 9 `AppStatCard` de poids égal dans une grille `auto-fit minmax(180px, 1fr)`, toutes cliquables (`--link` + translateY au survol) ; l'exercice apparaît à la fois en carte KPI et via un `Select` dans le graphe qui mute le store global ; deux graphiques redondants (courbe ressources + barres produits/charges).

**Layout cible** (de haut en bas, `flex-direction:column; gap:24px`) :
1. **En-tête de page** — eyebrow « Tableau de bord », titre « Vue d'ensemble », **sous-titre** « Exercice 2024 · à jour au … » + actions à droite (`Exporter` secondaire, `Nouvelle facture` primaire).
2. **Héro Trésorerie nette** — panneau pleine largeur en 2 colonnes : à gauche le grand chiffre (`48 920,40 €`) + delta `+3,2 %` (pill verte) + sparkline ; à droite le détail Banque courant / épargne / Caisse.
3. **Grille 1.5fr / 1fr** : à gauche file **« À traiter »** (impayés, en retard, chèques à déposer, opérations à rapprocher — chaque ligne : icône colorée 40px, libellé + sous-texte, montant à droite coloré par sévérité, chevron) ; à droite **Actions rapides** (3 boutons icône + libellé).
4. **4 chiffres de référence** (`repeat(4,1fr)`) — Résultat exercice, Recettes/Dépenses du mois, Adhérents — **non cliquables**, fond calme (vert pâle pour le résultat positif).
5. **Un seul graphe** Produits & charges — barres groupées sur 12 mois + légende.

**Composants & valeurs** :
- Panneaux : `border-radius: 16px`, bordure `#e2e8f0` (= `--surface-border`), ombre `0 18px 40px rgba(15,23,42,.06)`, fond `#fff`.
- Pill delta positif : fond `#f0fdf4`, texte `#16a34a`. Montant dû : `#dc2626`. En attente : `#b45309`.
- Tous les montants : `font-variant-numeric: tabular-nums`.
- Sparkline : ligne `#10b981` 2.5px + aire dégradée vers transparent.

### 2. Factures — patron mutualisé (`InvoiceWorkspace.vue`)
**Purpose** : suivre encaissements (clients) et règlements (fournisseurs) dans un espace unique.

**Constat actuel** : `ClientInvoicesView.vue` et `SupplierInvoicesView.vue` **dupliquent** KPI + toolbar + `DataTable` + le helper `statusSeverity` (redéclaré à l'identique) **et le dialog de paiement (copié mot pour mot)**. Côté client : 6 KPI qui se recouvrent et jusqu'à **9 boutons-icônes par ligne**. Côté fournisseur : 3 KPI seulement, 5 actions forcées en `nowrap` sur 13rem. Aucun total visible côté client ; côté fournisseur `totalAmount` est calculé mais enfoui dans une carte.

**Cible** : un composant `InvoiceWorkspace` piloté par props.

```
InvoiceWorkspace
  props:
    type: 'client' | 'supplier'
    columns: ColumnDef[]        // diffère : Libellé (client) vs Référence + pièce jointe (supplier)
    primaryAction: (row) => Action   // contextuelle selon statut (voir plus bas)
    overflowActions: Action[]        // le reste, dans un menu ⋯
    kpi: { funnelLabels, segments }  // « reste à encaisser » vs « à payer »
```

**Layout** (`column; gap:24px`) :
1. En-tête de page (eyebrow « Gestion », titre, sous-titre).
2. **Bascule de type** — segmented control `Clients (47)` / `Fournisseurs (23)` (signale l'espace partagé).
3. **Héro entonnoir** — panneau 2 colonnes : à gauche « Reste à encaisser » (`24 830,00 €`, couleur `#b45309`) + « sur X facturés · N factures » ; à droite **barre empilée** (Encaissé vert `#16a34a` / À venir jaune `#fcd34d` / En retard rouge `#ef4444`) + légende chiffrée. Côté fournisseur : « Reste à payer ».
4. **Panneau tableau** :
   - **Toolbar** : segments rapides (`Toutes`, `En retard`, `Impayées`, `Brouillons`, `Payées` — chacun avec compteur) + champ recherche. Remplace les **deux** systèmes de filtre actuels (Select serveur + filtres colonne PrimeVue).
   - **Table** : N°, Date, Contact, Libellé/Référence, Total (aligné droite, `nowrap`, tabular-nums), Statut (badge), Actions. Conteneur `overflow-x:auto`, table `min-width: 880px`.
   - **Action principale contextuelle** : `Encaisser` (envoyée/partiel) · `Relancer` (en retard, style rouge) · `Voir` (payée) · `Modifier` (brouillon) · `Traiter` (litige) — suivie d'un bouton `⋯` (menu de débordement : Historique, PDF, Envoyer, Dupliquer, et **destructif isolé** = Abandon de créance). Côté fournisseur le menu ajoute Téléverser / Aperçu du fichier.
   - **Pied de tableau** (`tfoot`) : « N factures affichées » + **Total de la sélection** (aligné sous la colonne Total).

### 3. Administration › Utilisateurs (`UsersView.vue`)
**Purpose** : gérer comptes et rôles.

**Layout** : en-tête + bouton primaire « Nouvel utilisateur » → 3 KPI (Comptes / Actifs / Admins) → **Matrice de rôles** (4 cartes : Lecture seule, Secrétaire, Trésorier, Admin — chacune avec **compteur d'utilisateurs** dans ce rôle + description des permissions) → **table** avec filtres rapides par rôle (Tous, Admins, Trésoriers, Inactifs), colonnes Utilisateur / E-mail / Rôle / Statut / Créé le / Actions. Badge **« vous »** sur la ligne de l'utilisateur courant ; action « réinitialiser mot de passe » désactivée sur sa propre ligne.

**Badges de rôle** (réutiliser un seul composant, pastille + texte) : Lecture seule `#94a3b8` · Secrétaire `#60a5fa` · Trésorier `#22c55e` · Admin `#f59e0b`. Statut : Actif vert / Inactif gris.

### 4. Administration › Système (`SystemView.vue`)
**Purpose** : santé de l'instance, sauvegardes, journaux.

**Constat actuel** : 6 `AppPanel` de même poids (état, sauvegardes, restauration, logs, paiements incohérents, audit). Le bouton **Restaurer** (qui écrase la base) est noyé dans un tableau au même niveau visuel que tout le reste.

**Layout cible** (`column; gap:22px`) :
1. **Bandeau d'état** — pleine largeur, en tête : pastille « Opérationnel » verte + Version / Taille BDD / Démarré le.
2. **File d'anomalies** — « Données à corriger : chèques sans date de dépôt » avec compteur (même motif que le « À traiter » du dashboard). Remplace le panneau « paiements incohérents » anonyme.
3. **Sauvegardes & restauration** — table des sauvegardes (Fichier mono, Libellé, Taille, Date) + champ libellé/`Télécharger`. **La restauration est marquée comme destructive** : icône rouge + mention explicite « écrase la base — confirmation en 2 étapes (saisie de “RESTAURER”) ».
4. **Journaux applicatifs** — terminal mono (fond très sombre même en clair), filtres INFO/WARN/ERROR colorés, `overflow-x:auto`.
5. **Journal d'audit** — table Horodatage / Acteur / Action / Cible.

---

## Interactions & Behavior
- **Lignes « À traiter » / anomalies** : cliquables → naviguent vers la liste filtrée correspondante. Survol : bordure colorée par sévérité + légère ombre.
- **Cartes de référence / KPI** : **non interactives** (pas de hover translateY). Seuls tâches, actions et lignes de table réagissent.
- **Segments de filtre** : un seul actif (fond foncé `#0f172a` / `#e2e8f0`), met à jour la requête liste. Les anciens filtres de colonne PrimeVue passent dans un panneau « filtres avancés » repliable.
- **Action principale de ligne** : déterminée par le statut (table de correspondance ci-dessus). Le `⋯` ouvre un `Menu` PrimeVue ; l'item destructif est séparé visuellement et déclenche une confirmation.
- **Restauration** : `ConfirmDialog` en deux étapes — l'utilisateur doit taper `RESTAURER` pour activer le bouton.
- **Bascule de thème** : icône lune/soleil dans la topbar → bascule la classe de thème sur `<html>` et persiste dans `localStorage` (`solde-theme`). Respecter `prefers-color-scheme` au premier chargement.

## State Management
- `themeStore` (Pinia) : `mode: 'light' | 'dark'`, action `toggle()`, persistance `localStorage`.
- `invoiceStore` paramétré par `type` : liste, segment actif, terme de recherche, total de sélection (déjà calculable depuis `totalAmount`).
- L'**exercice fiscal** doit vivre à **un seul endroit** (store global, exposé par le sélecteur de la topbar) — supprimer le `Select` local du graphe qui mutait le store en effet de bord.
- Compteurs par rôle / par segment : dérivés (computed) de la liste, pas des champs séparés.

## Responsive (mobile / tablette)
Les écrans desktop ci-dessus s'adaptent selon 3 breakpoints. Maquette de référence : `references/Solde - Responsive.dc.html` (+ captures `09`–`12`).

**Breakpoints & comportements**

| | Mobile `< 768px` | Tablette `768–1199px` | Desktop `≥ 1200px` |
|---|---|---|---|
| Navigation | Barre d'onglets basse (4 items) + drawer pour le reste | Rail d'icônes 72px (libellés au tap/survol) | Sidebar pleine 240px |
| Tables | **Cartes empilées** (1 ligne = 1 carte) | Conservées, `overflow-x:auto` | Complètes |
| Grilles KPI | 1–2 colonnes | 2 colonnes | 3–4 colonnes |
| Héros | Pleine largeur, empilés | Pleine largeur | Multi-colonnes |
| Topbar | Burger + logo + exercice + avatar ; recherche en icône | Condensée | Complète |
| Action primaire | **FAB** ancré au pouce | Bouton en-tête | Bouton en-tête |

**Règles clés à implémenter**
- **Table → cartes** : sur mobile, chaque facture devient une carte (N° + contact, date + montant, badge statut, action primaire pleine largeur + `⋯`). PrimeVue `DataTable` expose `responsiveLayout="stack"` / `breakpoint` pour cette bascule — l'exploiter plutôt que de dupliquer le markup.
- **Segments de filtre** : passent en scroll horizontal (`overflow-x:auto`, chips `flex:none`).
- **Cibles tactiles** ≥ **44px**. Les boutons-icônes serrés (édition, ⋯, clé) deviennent des **items de menu pleine largeur** dans une feuille d'action mobile, pas des cibles 30px côte à côte.
- **Drawer** : nav complète en panneau gauche 300px + overlay sombre `rgba(15,23,42,.45)`, fermable.
- Le mode sombre s'applique à l'identique sur tous les formats (mêmes tokens).

## Design Tokens

**Mode clair**
| Rôle | Hex |
|---|---|
| Fond app | `#f8fafc` |
| Surface / carte | `#ffffff` |
| Bordure surface | `#e2e8f0` |
| Texte principal | `#0f172a` |
| Texte secondaire | `#64748b` |
| Texte tertiaire | `#94a3b8` |
| Primaire (emerald) | `#10b981` (hover `#059669`) |
| Succès | `#16a34a` / fond `#f0fdf4` |
| Attention | `#b45309` / fond `#fffbeb` |
| Danger | `#dc2626` / fond `#fef2f2` |
| Info | `#2563eb` / fond `#eff6ff` |

**Mode sombre** (preset Aura dark)
| Rôle | Hex |
|---|---|
| Fond app | `#020617` |
| Surface basse / panneau | `#0e1a30` → dégradé `#13203a` |
| Surface carte interne | `#0c1730` |
| Bordure surface | `#2a3a55` (subtile `#1f2c44`) |
| Texte principal | `#f1f5f9` |
| Texte secondaire | `#94a3b8` |
| Primaire (emerald clair) | `#34d399` (texte sur primaire : `#04231a`) |
| Succès / Attention / Danger / Info | `#4ade80` / `#fcd34d` / `#f87171` / `#60a5fa` (fonds en `rgba(...,.12–.16)`) |

**Échelles**
- Rayons : panneaux `16px`, cartes internes `12px`, boutons/champs `8–10px`, pills `999px`. *(Réduit depuis les `22px` actuels, jugés trop « grand public » pour un registre comptable.)*
- Espacement : grille à `gap` 16/24px ; padding panneau `18–24px`.
- Ombres : clair `0 18px 40px rgba(15,23,42,.06)` ; sombre `0 20px 44px rgba(2,6,23,.45)`.
- Typo : **Manrope** 400/600/700/800. Titres `letter-spacing:-.03em à -.04em`. Eyebrows : `.72–.76rem`, 800, `letter-spacing:.12em`, uppercase. Montants : `tabular-nums`.

## Assets
- **Police** : Manrope (Google Fonts) — déjà ou à ajouter au codebase.
- **Icônes** : PrimeIcons (déjà présent via PrimeVue). Classes utilisées : `pi-home, pi-file, pi-file-import, pi-building-columns, pi-wallet, pi-money-bill, pi-chart-bar, pi-chart-pie, pi-users, pi-cog, pi-server, pi-comment, pi-exclamation-circle, pi-clock, pi-inbox, pi-credit-card, pi-wallet, pi-shield, pi-history, pi-exclamation-triangle, pi-check-circle, pi-sun, pi-moon, pi-ellipsis-h, pi-send, pi-eye, pi-pencil, pi-key, pi-sparkles`.
- Aucune image bitmap. Les graphes utilisent PrimeVue `Chart` (Chart.js) déjà en place — ne pas reproduire les barres en HTML du prototype.

## Screenshots (`screenshots/`)
Captures de référence des écrans (mode clair + sombre). **Note** : les petites icônes carrées (« tofu ») dans les captures sont un artefact d'export (police PrimeIcons cross-origin non embarquée) — dans l'app réelle ce sont les icônes PrimeIcons listées plus haut. La typo, les couleurs et la mise en page sont fidèles.

| Fichier | Écran |
|---|---|
| `01-dashboard.png` | Tableau de bord — en-tête + héro trésorerie |
| `02-dashboard-worklist.png` | Tableau de bord — file « À traiter » + actions rapides |
| `03-factures-top.png` | Factures — bascule type + héro entonnoir |
| `04-factures-table.png` | Factures — toolbar segments + table + total |
| `05-dark-users-top.png` | Utilisateurs (sombre) — KPI + matrice de rôles |
| `06-dark-users-table.png` | Utilisateurs (sombre) — table + filtres rôle |
| `07-dark-system-top.png` | Système (sombre) — bandeau d'état + file d'anomalies |
| `08-dark-system-backups.png` | Système (sombre) — sauvegardes/restauration + logs |
| `09-mobile-dashboard.png` | Mobile — tableau de bord + factures en cartes |
| `10-mobile-drawer.png` | Mobile — menu drawer complet |
| `11-tablet-dashboard.png` | Tablette — rail d'icônes + grille 2 colonnes |

## Files (références dans ce paquet)
- `references/Solde - Refonte tableau de bord.dc.html` — écrans **Tableau de bord** + **Factures** (mode clair), suivis de leurs cartes de recommandations.
- `references/Solde - Mode sombre.dc.html` — écrans **Utilisateurs** + **Système** en pleine fidélité sombre, galerie du reste de l'app, recommandations admin.
- `references/support.js` — runtime du prototype (à ignorer pour l'implémentation).

> Pour ouvrir les références : ouvre les `.dc.html` dans un navigateur. Connexion internet requise (Manrope + PrimeIcons par CDN).
