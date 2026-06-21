<!-- markdownlint-disable MD033 -->
# Backlog — Solde ⚖️

Backlog produit pour Solde ⚖️ — gestion comptable associative.
Quand le travail démarre sur un sujet, créer une branche `feature/` depuis `develop`.
Quand un sujet est livré, mettre à jour `CHANGELOG.md` et passer le ticket en ✅ Fait ici.

> Lots terminés depuis plus de 3 jours → [backlog-archive.md](backlog-archive.md)

---

## Calibration estimations

Facteur de marge actuel : **1,00** (0%) — inchangé (voir note CR2).

| Lot | Estimé Copilot | Réel Copilot | Ratio | Estimé gestion | Réel gestion | Ajustement |
| --- | --- | --- | --- | --- | --- | --- |
| UI | ~65 min | ~30 min | **0,46** | 15 min | ? | ↓ facteur → 1,00 |
| CR2 | ~70 min | ~20 min | **0,29** | — | — | voir note |
| REV | ~190 min | ~70 min | **0,37** | 15 min | — | voir note REV |
| BK | ~280 min | ~2h04+ (6 tickets n/m) | **≤0,44** | 15 min | ~10 min | ratio partiel, 6 tickets non mesurés |

> Lot UI : estimations 2x trop élevées. Les tickets UI/bulk-replace et les vérifications de tickets "déjà fait" ont été surestimés.
> Lot CR2 : ratio 0,29 — très inférieur à 1,15. Cependant ces tickets étaient tous très petits (i18n, tests, nav, squelette) et le facteur 1,00 reflète déjà une marge nulle. Plutôt que d'abaisser le facteur en dessous de 1,00 (ce qui serait contre-productif), la leçon est : **pour les tickets de finition/tests simples, l'estimation de référence doit être 3–5 min, pas 10–20 min**. Facteur maintenu à 1,00 ; calibration des estimations unitaires à revoir pour ces catégories.
> Lot REV : ratio 0,37. Cause principale : 3 tickets sur 11 étaient en réalité déjà traités (TEC-161, TEC-163, TEC-166 = 80 min estimés → 7 min réels). Les tickets d'implémentation pure (TEC-160, TEC-162, TEC-167, TEC-169, TEC-172) ont un ratio ~0,55. **Leçon** : avant d'estimer un ticket de « review fix », vérifier si le problème existe réellement. Pour les tickets d'implémentation technique, appliquer un facteur **0,60** par rapport à l'estimation initiale naïve.

---

## Lots actifs

### Lot RF — Refonte UI/UX (tableau de bord · factures · admin · mode sombre) — cible v1.8

Source : `design_handoff_solde_refonte-v2/` (handoff Claude Design — remplace la v1, ajoute le volet **responsive**). Objectif : reprise de la **hiérarchie de l'information**, **mutualisation des composants dupliqués** et **adaptation mobile/tablette/desktop**, dans l'identité Solde (Manrope, emerald, surfaces slate). Hi-fi : reproduire la mise en page des maquettes, mais **mapper les couleurs sur les tokens du thème** (pas d'inline-styles).

Ordre de livraison conseillé par le designer : `InvoiceWorkspace` d'abord (supprime le plus de duplication), puis le mode sombre (store + tokens), puis tableau de bord et écrans admin, enfin le responsive transverse. Découpage en 4–5 PR (Factures / Mode sombre / Tableau de bord / Admin / Responsive).

| ID | Titre | Prio | Est. | Créé | Démarré | Terminé |
| --- | --- | --- | --- | --- | --- | --- |
| TEC-193 | Composant `InvoiceStatusBadge` mutualisé | P2 | ~15 min | 2026-06-18 | 2026-06-18 | 2026-06-18 |
| TEC-194 | Composant `InvoiceWorkspace` paramétré par type | P1 | ~70 min | 2026-06-18 | 2026-06-18 | 2026-06-18 |
| BIZ-206 | Migrer vues factures client/fournisseur → `InvoiceWorkspace` | P1 | ~45 min | 2026-06-18 | 2026-06-18 | 2026-06-18 |
| TEC-195 | Store Pinia `theme` + bascule clair/sombre topbar | P2 | ~25 min | 2026-06-18 | 2026-06-18 | 2026-06-18 |
| TEC-196 | Tokens de thème clair/sombre (preset Aura dark) + rayons sobres | P2 | ~45 min | 2026-06-18 | 2026-06-18 | 2026-06-18 |
| TEC-197 | Composant `AppWorklist` mutualisé (« À traiter » / anomalies) | P2 | ~20 min | 2026-06-18 | 2026-06-18 | 2026-06-18 |
| BIZ-207 | Refonte `DashboardView` — héro trésorerie, file à traiter, graphe unique | P1 | ~60 min | 2026-06-18 | 2026-06-18 | 2026-06-18 |
| TEC-198 | Enrichissement API dashboard (delta trésorerie, rapprochement, adhérents) | P3 | ~30 min | 2026-06-18 | | |
| BIZ-208 | Refonte `UsersView` — matrice de rôles vivante + filtres | P2 | ~40 min | 2026-06-18 | 2026-06-18 | 2026-06-18 |
| BIZ-209 | Refonte `SystemView` — bandeau d'état, anomalies, restauration isolée | P2 | ~50 min | 2026-06-18 | 2026-06-18 | 2026-06-18 |
| TEC-199 | Shell de navigation adaptatif (3 breakpoints) — sidebar / rail tablette / onglets + drawer | P2 | ~50 min | 2026-06-18 | 2026-06-21 | 2026-06-21 |
| TEC-200 | Responsive des écrans refondus — table→cartes, grilles KPI, FAB, cibles ≥44px | P2 | ~40 min | 2026-06-18 | | |
| TEC-201 | Généraliser les composants : `AppRowActions` + `AppFilterSegments` (extraits de `Invoice*`) | P2 | ~30 min | 2026-06-18 | 2026-06-20 | 2026-06-20 |
| BIZ-211 | Rollout actions de ligne + segments aux autres écrans (contacts, paiements, banque, caisse, salariés, employés, écritures) | P2 | ~90 min | 2026-06-18 | 2026-06-20 | 2026-06-20 |
| TEC-202 | Refonte Admin — `AppSettingRow` (motif ligne de réglage) | P2 | ~20 min | 2026-06-20 | 2026-06-20 | 2026-06-20 |
| BIZ-212 | Refonte Supervision — 2 onglets (État & surveillance / Sauvegardes & restauration) | P2 | ~30 min | 2026-06-20 | 2026-06-20 | 2026-06-20 |
| BIZ-213 | Refonte Paramètres — 4 onglets + lignes de réglage + barres d'enregistrement | P1 | ~80 min | 2026-06-20 | 2026-06-20 | 2026-06-20 |
| CHR-195 | Quality gate + CHANGELOG + docs + release v1.8 | P2 | ~30 min | 2026-06-18 | | |

> Total estimé : **~640 min Copilot + 15 min gestion** (facteur de marge 1,00). Dépendances : TEC-193 précède TEC-194 ; TEC-194 précède BIZ-206 ; TEC-196 s'appuie sur TEC-195 ; TEC-197 précède BIZ-207 et BIZ-209 ; BIZ-207 bénéficie de TEC-198 (sinon dégradation gracieuse) ; TEC-200 vient **après** les écrans refondus (TEC-194, BIZ-207/208/209) et s'appuie sur le pattern mobile existant (`AppMobileCardList` + `useBreakpoints`, lot MOB) ; **TEC-201 puis BIZ-211** (généralisation aux autres écrans) viennent **après** stabilisation des composants factures et peuvent être livrés post-v1.8. Le mode sombre étant piloté par tokens, les écrans livrés avant TEC-196 en héritent automatiquement.

---

### Hors lots

| ID | Titre | Prio | Est. | Créé | Démarré | Terminé |
| --- | --- | --- | --- | --- | --- | --- |
| BIZ-169 | Édition/suppression des opérations manuelles | P2 | ~25 min | 2026-05-04 | 2026-05-04 | |
| BIZ-210 | Factures client — réintroduire un rappel créances exercice/historique (post-RF) | P3 | ~20 min | 2026-06-18 | | |
| BIZ-202 | Ligne de remise (prix négatif) dans une facture client | P2 | ~20 min | 2026-05-30 | 2026-05-30 | 2026-05-30 |
| ~~BIZ-201~~ | ~~Backup auto — inclure les fichiers du répertoire data/pdfs~~ | ~~P1~~ | ~~20 min~~ | ~~2026-05-14~~ | ~~2026-05-15~~ | ~~2026-05-15~~ |

---

## Détails

### Lot RF — Refonte UI/UX

#### TEC-193 — Composant `InvoiceStatusBadge` mutualisé

`statusSeverity` est redéclaré à l'identique dans `ClientInvoicesView.vue` et `SupplierInvoicesView.vue`. Créer `frontend/src/components/invoices/InvoiceStatusBadge.vue` : props `status` (+ `type` si la sémantique diffère client/fournisseur), rendu **pastille + texte** (jamais la couleur seule), mappage statut → sévérité centralisé. Réutiliser les clés i18n `invoices.statuses.*` existantes. Tests Vitest : chaque statut rend le bon libellé + la bonne classe.

#### TEC-194 — Composant `InvoiceWorkspace` paramétré par type

Créer `frontend/src/components/invoices/InvoiceWorkspace.vue` piloté par props : `type: 'client' | 'supplier'`, `columns: ColumnDef[]` (Libellé côté client / Référence + pièce jointe côté fournisseur), `primaryAction(row)` contextuelle selon statut (Encaisser / Relancer / Voir / Modifier / Traiter), `overflowActions[]` dans un menu `⋯` PrimeVue (Historique, PDF, Envoyer, Dupliquer, **destructif isolé** = abandon de créance ; côté fournisseur : Téléverser / Aperçu fichier), `kpi` (entonnoir). Layout : en-tête, bascule de type (segmented `Clients (n)` / `Fournisseurs (n)`), **héro entonnoir** (panneau 2 colonnes : reste à encaisser/payer + barre empilée Encaissé/À venir/En retard avec légende chiffrée), **toolbar** (segments rapides `Toutes`/`En retard`/`Impayées`/`Brouillons`/`Payées` avec compteurs + recherche, filtres avancés PrimeVue repliables), **table** (`overflow-x:auto`, `min-width:880px`, montants `tabular-nums` alignés droite), **pied de tableau** (N factures + total de la sélection). Mutualiser **le dialog de paiement** (aujourd'hui copié à l'identique). Aucun inline-style : tokens + classes utilitaires. Ne pas casser le mode mobile (`AppMobileCardList`).

#### BIZ-206 — Migrer vues factures client/fournisseur → `InvoiceWorkspace`

Réécrire `ClientInvoicesView.vue` et `SupplierInvoicesView.vue` comme de fines enveloppes passant leurs props à `InvoiceWorkspace`. Supprimer la duplication : KPI, toolbar, `DataTable`, `statusSeverity`, dialog de paiement. Paramétrer le store invoice par `type` (liste, segment actif, terme de recherche, total de sélection dérivé de `totalAmount`). Vérifier les query params de navigation existants (`unpaid`, `status=overdue`, etc.) toujours honorés. Tests Vitest des deux vues + non-régression des parcours.

#### TEC-195 — Store Pinia `theme` + bascule clair/sombre topbar

Créer `frontend/src/stores/theme.ts` : `mode: 'light' | 'dark'`, action `toggle()`, persistance `localStorage` clé `solde-theme`, respect de `prefers-color-scheme` au premier chargement. Appliquer/retirer la classe de thème sur `<html>` (l'app utilise déjà `html.dark-mode`). Ajouter l'icône lune/soleil (`pi-moon`/`pi-sun`) dans la topbar de `layouts/AppLayout.vue`. Tests : toggle, persistance, init depuis la préférence système.

> **Déjà couvert** (2026-06-18) : le mode sombre existait déjà via le composable `composables/useDarkMode.ts` (persistance `solde-dark-mode`, classe `html.dark-mode`, anti-FOUC dans `index.html`) + bascule lune/soleil dans `AppLayout`. Fonctionnellement équivalent au store Pinia demandé — non réécrit. Seul reliquat optionnel : respect de `prefers-color-scheme` au premier chargement (non implémenté).

#### TEC-196 — Tokens de thème clair/sombre (preset Aura dark) + rayons sobres

Définir les variables CSS clair **et** sombre dans `assets/main.css` (+ config preset Aura) à partir de la table Design Tokens du handoff : surfaces, bordures, textes, primaire emerald (`#10b981` clair / `#34d399` sombre), sémantiques succès/attention/danger/info avec fonds. Réduire les rayons : panneaux `16px`, cartes internes `12px`, boutons/champs `8–10px`, pills `999px` (depuis `22px`). Ombres clair/sombre du handoff. S'assurer que terminal de logs et montants `tabular-nums` restent lisibles en sombre. Comme tout passe par tokens, les écrans refondus héritent du mode sombre automatiquement.

#### TEC-197 — Composant `AppWorklist` mutualisé (« À traiter » / anomalies)

Créer un composant de **file d'actions** réutilisé par le tableau de bord (« À traiter ») et l'écran Système (« Données à corriger »). Chaque ligne : icône colorée 40px, libellé + sous-texte, montant/valeur à droite coloré par sévérité, chevron ; ligne cliquable → navigue vers la liste filtrée correspondante ; survol = bordure colorée + légère ombre. Props : tableau d'items `{ icon, label, sublabel, value, severity, to }` + compteur d'en-tête. Pas de hover « translateY » (réservé aux éléments interactifs, jamais aux chiffres de référence).

#### BIZ-207 — Refonte `DashboardView` — héro trésorerie, file à traiter, graphe unique

Restructurer `DashboardView.vue` (colonne, gap 24px) : 1) **en-tête** eyebrow + titre « Vue d'ensemble » + **sous-titre** (« Exercice … · à jour au … ») + actions à droite (Exporter secondaire, Nouvelle facture primaire) ; 2) **héro Trésorerie nette** pleine largeur 2 colonnes : grand chiffre + pill delta + **sparkline** (depuis `getResourcesChartApi`) à gauche, détail Banque courant/épargne/Caisse à droite ; 3) grille 1.5fr/1fr : **`AppWorklist` « À traiter »** (impayés, en retard, chèques à déposer, à rapprocher) + **Actions rapides** ; 4) **4 chiffres de référence non cliquables** (Résultat exercice, Recettes/Dépenses du mois, Adhérents) — pas de hover ; 5) **un seul graphe** Produits & charges (barres groupées). Supprimer le `Select` d'exercice local du graphe (effet de bord sur le store global) — l'exercice vit uniquement dans le sélecteur topbar. Couleur + signe sémantiques (vert = bonne nouvelle, rouge = dû). Dégradation gracieuse des éléments dépendant de TEC-198 si l'API ne fournit pas encore la donnée.

> **BIZ-207 livré** (2026-06-18) avec dégradation gracieuse : le delta trésorerie et la sparkline sont dérivés côté front depuis `getResourcesChartApi` (net_resources). Les éléments **« opérations à rapprocher »** (file À traiter) et **« adhérents »** (chiffre de référence) sont **omis** faute de donnée API — ils restent à couvrir par TEC-198. Le 4ᵉ chiffre de référence affiche l'exercice en cours à la place des adhérents.

#### TEC-198 — Enrichissement API dashboard (delta trésorerie, rapprochement, adhérents)

Compléter `GET /api/dashboard/` (`backend/services/dashboard_service.py` + schéma) pour alimenter la refonte : delta trésorerie nette vs mois précédent (sinon calculable côté front depuis `getResourcesChartApi`), compteur d'opérations bancaires **à rapprocher** (ligne « À traiter »), et nombre d'**adhérents** (chiffre de référence). Conditionnel : ne créer que les champs réellement manquants après vérification du service existant ; sinon fermer en notant que la donnée est déjà dérivable côté front. Tests d'intégration sur les nouveaux champs.

#### BIZ-208 — Refonte `UsersView` — matrice de rôles vivante + filtres

Restructurer `UsersView.vue` : en-tête + bouton primaire « Nouvel utilisateur » → 3 KPI (Comptes / Actifs / Admins, dérivés) → **matrice de rôles** (4 cartes Lecture seule / Secrétaire / Trésorier / Admin avec **compteur d'utilisateurs** par rôle + description des permissions) → **table** avec filtres rapides par rôle (Tous, Admins, Trésoriers, Inactifs, compteurs dérivés), colonnes Utilisateur / E-mail / Rôle / Statut / Créé le / Actions. Badge **« vous »** sur la ligne courante ; action « réinitialiser mot de passe » désactivée sur sa propre ligne. Composant **badge de rôle** mutualisé (pastille + texte) : Lecture seule `#94a3b8`, Secrétaire `#60a5fa`, Trésorier `#22c55e`, Admin `#f59e0b` → via tokens. Statut Actif/Inactif. Tests Vitest.

#### BIZ-209 — Refonte `SystemView` — bandeau d'état, anomalies, restauration isolée

Restructurer `SystemView.vue` (colonne, gap 22px) : 1) **bandeau d'état** pleine largeur (pastille « Opérationnel » + Version / Taille BDD / Démarré le) ; 2) **file d'anomalies** via `AppWorklist` (« Données à corriger : chèques sans date de dépôt » + compteur — remplace le panneau « paiements incohérents » anonyme) ; 3) **Sauvegardes & restauration** : table des sauvegardes + libellé/Télécharger, **restauration marquée destructive** (icône rouge + mention « écrase la base ») avec **`ConfirmDialog` en 2 étapes** (saisie de `RESTAURER` pour activer le bouton) ; 4) **journaux applicatifs** : terminal mono (fond très sombre même en clair), filtres INFO/WARN/ERROR colorés, `overflow-x:auto` ; 5) **journal d'audit** (Horodatage / Acteur / Action / Cible). Tests Vitest sur la confirmation 2 étapes.

#### TEC-199 — Shell de navigation adaptatif (3 breakpoints)

Étendre `layouts/AppLayout.vue` à 3 breakpoints : **desktop ≥ 1200px** sidebar pleine 240px + contenu `max-width` ~1320px centré ; **tablette 768–1199px** rail d'icônes 72px (libellés au survol/tap) ; **mobile < 768px** barre d'onglets basse (4 items principaux) + **drawer** pour le reste (panneau gauche 300px + overlay `rgba(15,23,42,.45)`, fermable). Topbar condensée sur mobile (burger + logo + sélecteur d'exercice + avatar, recherche en icône). S'appuyer sur le `useBreakpoints` existant (lot MOB) en ajoutant le palier tablette s'il manque. Cibles tactiles ≥ 44px. Le mode sombre s'applique à l'identique (mêmes tokens). Tests Vitest des bascules de breakpoint.

#### TEC-200 — Responsive des écrans refondus

Décliner les écrans refondus (InvoiceWorkspace, Dashboard, Users, System) sur mobile/tablette : **table → cartes empilées** (1 facture = 1 carte : N° + contact, date + montant, badge statut, action primaire pleine largeur + `⋯`) en réutilisant/alignant `AppMobileCardList` existant sur le design des maquettes (ne pas dupliquer le markup ; envisager `responsiveLayout="stack"` PrimeVue là où pertinent) ; **grilles KPI** 1–2 col. mobile / 2 col. tablette / 3–4 col. desktop ; **héros** empilés pleine largeur sur petit écran ; **segments de filtre** en scroll horizontal (`overflow-x:auto`, chips `flex:none`) ; **action primaire en FAB** ancré au pouce sur mobile ; boutons-icônes de ligne (édition, ⋯, clé) regroupés en **feuille d'action mobile** (items pleine largeur) plutôt qu'en cibles serrées. Vérifier la cohérence avec l'existant mobile (lot MOB/BIZ-164). Tests Vitest ciblés sur la bascule cartes et la feuille d'action.

#### TEC-201 — Généraliser les composants : `AppRowActions` + `AppFilterSegments`

Promouvoir les briques nées sur les factures en composants génériques réutilisables app-wide, sans casser les vues factures :
- `InvoiceFilterSegments` → `AppFilterSegments` (déplacer en `components/ui/`, déjà 100 % générique ; déjà réutilisé tel quel dans `UsersView`). Mettre à jour les imports (factures + users).
- `InvoiceRowActions` → `AppRowActions` (déplacer en `components/ui/`, le type `InvoiceRowPrimaryAction` → `RowAction`). Pattern action principale + menu `⋯` (destructif isolé) indépendant du domaine.
- Optionnel : extraire le chrome de liste de `InvoiceWorkspace` en `AppListWorkspace` (header + toolbar + segments + panneau via slots), si le gain est net.
Conserver des ré-exports/alias depuis les emplacements `invoices/` pour limiter le diff, ou mettre à jour tous les imports. Tests unitaires conservés/déplacés.

#### BIZ-211 — Rollout actions de ligne + segments aux autres écrans

Appliquer les patterns mutualisés (TEC-201) aux écrans listes restants pour une cohérence app-wide : remplacer les rangées de boutons-icônes par `AppRowActions` (action principale contextuelle + menu `⋯`, destructif isolé) et ajouter des **segments rapides** (`AppFilterSegments`) là où c'est pertinent. Écrans visés : **Contacts**, **Paiements**, **Banque** (transactions + dépôts), **Caisse**, **Salariés**, **Employés**, et tables de **comptabilité** (journal, grand-livre…). Au cas par cas : définir l'action principale par statut/contexte propre à chaque écran ; conserver les filtres colonne en « avancé ». Ne pas transposer les composants spécifiques facture (entonnoir, dialog paiement, badge statut, bascule de type). Découpage possible en plusieurs PR par écran. Tests Vitest par vue migrée.

#### Refonte profonde Admin (handoff `design_handoff_solde_complet/`)

Source : handoff Claude Design `design_handoff_solde_complet/details/02-admin-parametres-supervision.md`. Garder **2 écrans séparés**, réorganisés en onglets internes (PrimeVue `Tabs`/`TabList`/`Tab` en sélecteur + contenu en `v-show`).

- **TEC-202** ✅ — `components/ui/AppSettingRow.vue` : motif ligne de réglage (libellé + description + warning + slot `#control`), responsive row→column. Fondation pour Paramètres.
- **BIZ-212** ✅ — `SystemView` réorganisé en 2 onglets : **État & surveillance** (bandeau + anomalies + logs + audit) / **Sauvegardes & restauration** (backup auto + liste + restauration). Aucun bloc déplacé : `v-show` par panneau (préserve l'état des logs chargés). Éléments déjà faits conservés (bandeau, anomalies, restauration RESTAURER).
- **BIZ-213** ✅ — `SettingsView` : passer de 5 panneaux empilés à **4 onglets** (Organisation · Comptabilité · Communication · Zone dangereuse), re-répartir les `Settings*Panel`, convertir les champs en `AppSettingRow`, ajouter une **barre d'enregistrement collante par onglet** (point ambre/✓ vert, Annuler/Enregistrer désactivés si pas de changement), aperçu live du n° de facture, avertissement sur les chiffres de séquence. Le gros morceau (refactor des 6 panneaux + logique de save par onglet).

#### CHR-195 — Quality gate + CHANGELOG + docs + release v1.8

Exécuter la quality gate complète (ruff check + format, mypy, pytest, eslint, vue-tsc, vitest) et corriger les résidus. Mettre à jour `CHANGELOG.md` (`[Non publié]`), `doc/user/changelog-user.md` (sections par rôle : nouveautés visuelles + mode sombre), `doc/dev/architecture.md` (système de thème / tokens), et les statuts du backlog. Documenter le mode sombre côté utilisateur. Bump version `MINOR` → v1.8 dans `pyproject.toml` et `frontend/package.json`.

### BIZ-195 — Statut ARCHIVED — modèle, transitions, service, router, migration

Ajouter `ARCHIVED = "archived"` à `InvoiceStatus` dans `backend/models/invoice.py`. Mettre à jour `_VALID_TRANSITIONS` dans `backend/services/invoice.py` : `PAID → {ARCHIVED}`, `ARCHIVED → {}` (terminal). Ajouter `archive_invoice(db, invoice)` dans le service : génère le PDF WeasyPrint si `pdf_path` est null, puis passe le statut à ARCHIVED. Dans `backend/routers/invoice.py` : relâcher la restriction "FOURNISSEUR uniquement" sur `GET /{id}/file` pour les CLIENT en statut ARCHIVED. Migration Alembic commentée (SQLite stocke les enums en texte, pas de contrainte CHECK à modifier). Tests unitaires des transitions valides/invalides pour ARCHIVED.

### BIZ-196 — Script import_word_invoices.py

Créer `scripts/import_word_invoices.py` (dry-run par défaut, `--commit` pour écrire en base). Args : `--source /chemin/vers/dossier`, `[--db data/solde.db]`, `[--commit]`, `[--verbose]`. Pour chaque `.docx` (pattern `facture YYYY-NNNN.docx`) : extraire le numéro depuis le nom de fichier, la date via `_DATE_RE` (réutilisé depuis `import_addresses_from_docx.py`), le nom client et l'adresse via les patterns de fuzzy-matching existants, les lignes de prestation depuis `doc.tables` (parcourir les tables Word pour identifier colonnes description/quantité/PU/total), le montant total (ligne « Total » du tableau ou somme des lignes). Résolution contact : recherche par nom, création `ContactType.CLIENT` si absent. Skip silencieux si une facture avec ce numéro existe déjà en base (log). Créer la facture : `type=CLIENT`, `status=ARCHIVED`, pas d'écriture comptable. Copier le `.docx` dans `data/uploads/invoices/{uuid}.docx`, stocker dans `invoice.file_path`. Rapport final : N créées, M skippées (doublon), P erreurs. Tests unitaires des fonctions de parsing (dates, noms, tables Word).

### BIZ-197 — Endpoint POST /invoices/bulk-archive + schémas + tests intégration

Ajouter dans `backend/schemas/invoice.py` : `BulkArchiveRequest` (body `invoice_ids: list[int]`) et `BulkArchiveResult` (response `{"archived": int, "skipped": int, "errors": list[str]}`). Ajouter `POST /invoices/bulk-archive` dans `backend/routers/invoice.py` : rôle TRESORIER ou ADMIN requis ; pour chaque ID, vérifier que la facture existe et est PAID (sinon skip avec raison dans errors) ; appeler `archive_invoice()` du service pour chaque facture valide ; retourner `BulkArchiveResult`. Tests intégration dans `tests/integration/test_invoices_api.py` : factures PAID → archivées, factures non-PAID → skippées, accès refusé sans rôle suffisant.

### BIZ-190 — Frontend — types + i18n + badge + boutons UI factures archivées

Ajouter `'archived'` à `InvoiceStatus` dans `frontend/src/api/invoices.ts`. Ajouter clé i18n `invoices.statuses.archived: 'Archivée'` dans `fr.ts` et `'Archived'` dans `en.ts`. Ajouter une couleur/sévérité grise pour le badge statut ARCHIVED dans le composant de badge. Dans `ClientInvoicesView.vue` : pour les factures ARCHIVED, n'afficher que — bouton "Consulter" (vue détail read-only), bouton "PDF" si `pdf_path` non null (affiche le fichier figé, ne génère pas à la volée), bouton "Document" si `file_path` non null (télécharge le `.docx`). Masquer pour ARCHIVED : boutons éditer, payer, envoyer email, dupliquer, passer irrécupérable, restaurer. Ajouter `'archived'` aux options de filtre statut (colonne et dropdown global).

### BIZ-191 — Frontend — action bulk archive

Dans `ClientInvoicesView.vue` : ajouter un bouton "Archiver les factures filtrées" dans la barre d'outils, visible uniquement si au moins une facture PAID est présente dans `displayedInvoices`. Confirmation via `useConfirm()` + `<ConfirmDialog />` : "Archiver X facture(s) payée(s) ? Cette action est irréversible." Appel `POST /invoices/bulk-archive` avec les IDs des factures PAID de `displayedInvoices`. Toast résultat : "N factures archivées" + avertissement si M skippées. Rafraîchir la liste après archivage. Clés i18n : `invoices.bulk_archive_confirm`, `invoices.bulk_archive_result`, `invoices.bulk_archive_btn`.

### TEC-192 — Composable useTableExport (SheetJS) + tests Vitest

Installer `xlsx` (SheetJS) : `npm install xlsx` dans `frontend/`. Créer `frontend/src/composables/useTableExport.ts` exposant `exportToExcel(rows: object[], columns: {field: string, header: string}[], filename: string)` : construire un tableau de données en appliquant les colonnes sur les rows, créer un `WorkSheet` via `XLSX.utils.aoa_to_sheet`, créer un `WorkBook`, télécharger le fichier `.xlsx` via `XLSX.writeFile`. Ajouter clé i18n `common.export_excel: 'Exporter Excel'` dans `fr.ts` et `en.ts`. Tests Vitest dans `frontend/src/tests/` : colonnes correctement mappées, fichier bien déclenché (mock XLSX.writeFile), comportement avec rows vides.

### BIZ-193 — Bouton export Excel sur toutes les vues DataTable

Ajouter `@value-change` sur chaque `DataTable` qui ne tracke pas encore ses lignes affichées (pour exposer les données filtrées courantes). Ajouter un bouton "Exporter Excel" (utilisant `useTableExport`) dans chaque vue avec DataTable : `ClientInvoicesView`, `SupplierInvoicesView`, `BankView` (transactions + dépôts), `CashView` (entrées + comptages de caisse), `ContactsView`, `EmployeesView`, `FiscalYearView`, `AccountingAccountsView`, `AccountingRulesView`, `AccountingJournalView`, `AccountingLedgerView`, `AccountingBalanceView`, `AccountingBilanView`, `AccountingResultatView`. Le bouton exporte uniquement les lignes visibles (après filtrage). Nom du fichier : `{entité}-{date}.xlsx`.

### CHR-194 — Quality gate complet + CHANGELOG + docs + bump version

Exécuter la quality gate complète (ruff check + format, mypy, pytest, eslint, vue-tsc, vitest) et corriger tout problème résiduel. Mettre à jour `CHANGELOG.md` (section `[Non publié]`), `doc/user/changelog-user.md` (sections Secrétaire/Trésorier/Administrateur), et `doc/backlog.md` (statuts tickets). Incrémenter la version patch dans `pyproject.toml` et `frontend/package.json`.
### BIZ-169 — Édition/suppression des opérations manuelles

Permettre de modifier ou supprimer les opérations bancaires créées manuellement depuis BankView (opérations sans import source).

### BIZ-202 — Ligne de remise (prix négatif) dans une facture client

**Problème :** il est impossible de saisir un prix négatif sur une ligne de facture client (ex. : remise, trop-perçu à déduire). Le composant d'édition transforme tout prix négatif en `0` dès la saisie, et le total ne reflète pas la ligne.

**Cause :** dans `frontend/src/components/ClientInvoiceForm.vue`, la fonction `normalizeDecimalInput` applique `Math.max(0, parsed)` indifféremment aux champs `quantity` et `unit_price`, ce qui écrase toute valeur négative par zéro.

**Correctif frontend :**
- Dans `normalizeDecimalInput`, ne clamper à `≥ 0` que pour `quantity` ; laisser `unit_price` accepter les négatifs.
- Conserver la garde `hasNegativeTotal` (le total de la facture ne peut pas être négatif) et améliorer le message d'erreur associé pour indiquer que c'est la ligne de remise qui rend le total négatif.

**Backend :** aucun changement — `unit_price` n'a pas de contrainte non-négative dans `InvoiceLineBase`, et `validate_client_total` rejette déjà les totaux négatifs.

**Tests :** ajouter un test Vitest vérifiant que `normalizeDecimalInput` accepte bien un prix négatif et que `computedTotal` / `hasNegativeTotal` se comportent correctement.


### BIZ-210 — Factures client : réintroduire un rappel créances exercice/historique (post-RF)

Le Lot RF (BIZ-206) a remplacé les 6 KPI factures client par l'`InvoiceFunnelHero`, qui agrège le **jeu de factures affiché** (reste à encaisser, encaissé, à venir, en retard). Ce faisant, la distinction **créances de l'exercice** vs **créances totales + report historique** (anciennement issue de `useInvoiceMetrics.receivableMetrics`) n'est plus exposée — information utile au trésorier. À rediscuter en review de la PR Factures. Si retenu : réafficher un rappel discret (ex. sous l'entonnoir ou en sous-texte) du report historique des créances ouvertes hors exercice courant, sans réintroduire la grille de 6 KPI. `receivableMetrics` reste disponible dans le composable.

### BIZ-201 — Backup auto — inclure les fichiers du répertoire data/pdfs

Corriger le processus de sauvegarde automatique pour inclure systématiquement les fichiers présents dans `data/pdfs` (factures et documents PDF générés/stockés). Vérifier le comportement pour les différents types de destination (local, SMB, OneDrive) et pour les deux modes d'envoi (snapshot seul vs dossier complet), puis ajouter des tests de non-régression backend sur la présence de `data/pdfs` dans l'artefact de sauvegarde.

---

## Lots terminés récents (≤ 3 jours)

| Lot | Nom | Version | Tickets | Terminé | Est. Copilot | Réel Copilot |
| --- | --- | --- | --- | --- | --- | --- |
| UX2 | Corrections UX contacts & factures | v1.7.3 | BIZ-203, BIZ-204, BIZ-205 | 2026-05-14 | ~110 min | — |
| FW | Import Word + Archivage + Export Excel | v1.7.2 | BIZ-190→197, TEC-192, CHR-194 | 2026-05-12 | ~395 min | ~2h50 |
| BK | Backup automatique | v1.7 | BIZ-173→184, BIZ-187, BIZ-188, BIZ-189 | 2026-05-11 | ~4h40 | ~2h+ (partiel) |
| TEC-185/BIZ-186 | Fix Chrome PDF + filigrane Payé | v1.6.3 | TEC-185, BIZ-186 | 2026-05-10 | ~40 min | — |
| REV2 | Refactoring technique différé | v1.6.2 | TEC-170, TEC-171, TEC-173 | 2026-05-07 | ~55 min | — |
| REV | Revue de code technique | v1.6.1 | TEC-160–165, 167–169, 172 (+ TEC-161, 163, 166 déjà faits) | 2026-05-06 | ~190 min | ~70 min |
| BIZ-172 | Paiements chèques incohérents | v1.6 | BIZ-172 | 2026-05-05 | ~45 min | — |
| BIZ-171 | Améliorations factures mobile | v1.6 | BIZ-171 | 2026-05-05 | ~35 min | — |
| BIZ-170 | Gestion bordereaux en attente | v1.6 | BIZ-170 | 2026-05-05 | ~60 min | ~45 min |
| BIZ-034 | Support multi-compte banque + bugfixes comptables | v1.5 | BIZ-034, fix virement, fix journal filtré, fix fiscal_year_id manuel | 2026-05-04 | — | — |
| CR2 | Correctifs & finitions post-MOB | v1.5 | TEC-157, TEC-158, TEC-159, BIZ-165, BIZ-166, BIZ-167, BIZ-168, CHR-078 | 2026-05-04 | ~95 min | ~30 min |
| Wizard | Wizard factures & Contacts | v1.2 | BIZ-144, BIZ-145, BIZ-147, BIZ-151 | 2026-05-02 | — | — |
| CR | Correctifs revue de code | v1.3.1 | TEC-133, TEC-134, TEC-135, TEC-136, TEC-137, TEC-138, TEC-139, TEC-140, TEC-141, TEC-155 | 2026-05-02 | — | — |
| DOC | Documentation utilisateur | v1.5 | BIZ-161, BIZ-162, BIZ-163 | 2026-05-03 | ~115 min | ~45 min |
| UI | Améliorations UI & saisie | v1.4 | BIZ-149, BIZ-150, BIZ-157, BIZ-158 | 2026-05-03 | ~65 min | ~30 min |
| MOB | Mode téléphone | v1.5 | BIZ-164 | 2026-05-03 | ~90 min | — |

<details>
<summary>Lot BK — Backup automatique (2026-05-11)</summary>

| Ticket | Titre | Est. | Réel |
| --- | --- | --- | --- |
| BIZ-173 | Migration Alembic + modèle BackupDestination | ~15 min | ~7 min |
| BIZ-174 | Schemas Pydantic backup | ~10 min | ~5 min |
| BIZ-175 | Service rclone (backup_destination_service) | ~25 min | ~9 min |
| BIZ-176 | Dockerfile — installation rclone | ~5 min | ~3 min |
| BIZ-177 | Scheduler APScheduler + lifespan main.py | ~30 min | ~14 min |
| BIZ-178 | Service restore (test-restore + restore distante) | ~15 min | ~9 min |
| BIZ-179 | Router backup.py (12 endpoints) | ~35 min | ~19 min |
| BIZ-180 | Frontend api/backup.ts | ~10 min | ~7 min |
| BIZ-181 | Frontend SettingsBackupPanel.vue | ~45 min | ~16 min |
| BIZ-182 | Frontend SettingsView + i18n fr/en | ~15 min | n/m |
| BIZ-183 | Tests unitaires backend | ~15 min | n/m |
| BIZ-184 | Tests intégration API backup | ~20 min | n/m |
| BIZ-187 | Type planification quotidien (HH:MM) + option snapshot-only | ~35 min | n/m |
| BIZ-188 | Option inclure tous les backups précédents | *(inclus BIZ-187)* | n/m |
| BIZ-189 | Fix : spinner visible si backup auto déclenché page ouverte | ~15 min | n/m |
| PR review (Copilot) | Corrections commentaires revue | — | ~35 min |
| **Total** | | **~4h40** | **~2h04 mesurés** (6 tickets n/m) |

</details>

<details>
<summary>Lot REV — Revue de code technique (2026-05-06)</summary>

| Ticket | Titre | Est. | Réel | Note |
| --- | --- | --- | --- | --- |
| TEC-160 | Fix race condition entry_number | ~15 min | ~10 min | Migration + unique index + retry |
| TEC-161 | Masquer clés API/SMTP | ~15 min | ~2 min | Déjà traité (schema excluait déjà les champs) |
| TEC-162 | Frontend .catch vides | ~30 min | ~8 min | 11 occurrences → console.error |
| TEC-163 | Optimiser fonds mensuels | ~20 min | ~2 min | Déjà efficace (2 queries, pas N) |
| TEC-164 | Rendre next_entry_number public | ~5 min | ~2 min | Fusionné avec TEC-160 |
| TEC-165 | max_length mot de passe | ~5 min | ~2 min | +2 lignes |
| TEC-166 | Tests accounting_engine | ~45 min | ~3 min | Tests déjà existants (8 classes) |
| TEC-167 | Allocation batch numéros | ~15 min | ~8 min | next_entry_numbers + refacto apply |
| TEC-168 | Cache Jinja2 Environment | ~5 min | ~2 min | @lru_cache |
| TEC-169 | max_length schemas bank | ~20 min | ~8 min | Field(max_length=…) |
| TEC-172 | CSRF X-Requested-With | ~15 min | ~8 min | Header check + frontend + tests |
| — | Quality gate + fixes | — | ~15 min | ruff, mypy, pytest, eslint, vue-tsc, vitest |
| **Total** | | **~190 min** | **~70 min** | Ratio 0,37 |

</details>

| Ticket | Titre | Est. | Réel |
| --- | --- | --- | --- |
| TEC-157 | i18n AppMobileCardList + CashView | ~10 min | ~3 min |
| TEC-158 | Tests intégration suggest_cheque_number (5 tests) | ~20 min | ~5 min |
| TEC-159 | Tests cheque_number_template settings API (4 tests) | ~15 min | ~4 min |
| BIZ-165 | Navigation prev/next preview factures client | ~10 min | ~5 min |
| CHR-078 | Squelette i18n anglais (en.ts) | ~15 min | ~3 min |
| CR-077 | Corrections revue Copilot PR #77 (8 threads) | ~25 min | ~20 min |
| **Total** | | **~95 min** | **~36 min** |

### Détail

- **TEC-157** : `AppMobileCardList.vue` — prop `emptyMessage` default migré vers `t('common.empty')` + import `useI18n`. `CashView.vue` — `'Écart :'` remplacé par `t('cash.count_diff')`. Clé `common.empty: 'Aucune donnée.'` ajoutée dans `fr.ts`.
- **TEC-158** : 5 tests dans `test_payments_api.py` : statut 200, string non vide, pas de date → aujourd'hui, incrément après un chèque existant, 401 sans auth, 403 readonly.
- **TEC-159** : 4 tests dans `test_settings_api.py` (dans `TestUpdateSettings`) : valeur par défaut `{date}.{seq}`, update valide, 422 sans `{seq}`, 422 avec placeholder inconnu.
- **BIZ-165** : `ClientInvoicesView.vue` — `historyIndex` ref, `openHistory` indexe dans `displayedInvoices`, barre nav ◀ N/total ▶ dans le dialog, `goToPrevHistory` / `goToNextHistory`, styles `.preview-nav-bar`.
- **CHR-078** : `frontend/src/i18n/en.ts` créé — sections `app`, `auth`, `common` traduits en anglais. Enregistré dans `index.ts` (messages: `{ fr, en }`).
- **CR-077** : Corrections des 8 threads de revue Copilot sur PR #77 — CSS dupliqué supprimé (`SupplierInvoicesView`), fuite Blob URL corrigée (`ClientInvoicesView`), bouton créance douteuse restreint à `type === 'client'` (`ContactHistoryContent`), commentaire `en.ts` corrigé, tests `suggest_cheque_number` renforcés (format exact + date today), 4 tests Vitest nav prev/next ajoutés (client + fournisseur). Version 1.4.7 → 1.4.8.

</details>

<details>
<summary>Lot MOB — Mode téléphone (2026-05-03)</summary>

| Ticket | Titre | Est. | Réel | Écart |
| --- | --- | --- | --- | --- |
| BIZ-164 (mobile) | Vues cartes + composant + breakpoint | ~50 min | — | — |
| BIZ-164 (depot) | Tuile dépôt espèces redesignée | ~15 min | — | — |
| BIZ-164 (stat) | Stat cards 2 colonnes mobile | ~5 min | — | — |
| BIZ-164 (cheque) | Suggestion auto n° chèque | ~20 min | — | — |
| **Total** | | **~90 min** | **—** | **—** |

### BIZ-164 — Mode téléphone & UX mobile
Migration Alembic `0049` : `cheque_number_template` dans `app_settings`. Endpoint `GET /api/payments/suggest_cheque_number`. Service `suggest_cheque_number` dans `settings.py`. Auto-suggestion dans `ClientInvoicesView`, `SupplierInvoicesView`, `QuickPaymentWizard`. Champ configurable dans `SettingsAssociationPanel`. Vues cartes mobile sur **toutes les listes** via `AppMobileCardList` (générique `T`) + `useBreakpoints` : Factures client/fournisseur (historiques), Contacts, Banque (transactions + dépôts), Règlements, Caisse, Salaires (3 tables), Employés, Comptabilité (Comptes, Balance, Bilan, Résultat, Règles, Journal, Grand-livre), Exercices, Utilisateurs. Dialogs full-width mobile. Stat grid 2 colonnes mobile.

</details>

<details>
<summary>Lot UI — Améliorations UI & saisie (2026-05-03)</summary>

| Ticket | Titre | Est. | Réel | Écart |
| --- | --- | --- | --- | --- |
| BIZ-158 | Limite API 1000 items + warning | ~30 min | ~18 min | −12 min |
| BIZ-149 | Auto-capitalisation intitulés facture | ~15 min | ~2 min | −13 min |
| BIZ-150 | Accepter la virgule comme séparateur décimal | ~10 min | ~7 min | −3 min |
| BIZ-157 | Pagination 50 items par défaut | ~10 min | ~3 min | −7 min |
| **Total** | | **~65 min** | **~30 min** | **−35 min** |

### BIZ-158 — Limite API 1000 items + warning si atteinte
`default=1000, le=1000` sur 6 routeurs (`invoice.py`, `payment.py`, `contact.py`, `bank.py` transactions + dépôts, `salary.py`). Bandeau `Message` PrimeVue severity `warn` dans chaque vue liste quand le résultat atteint 1 000 items. 4 tests mis à jour (renommage + assertions). Correction d'un bug de docstring introduit en cours de session.

### BIZ-149 — Auto-capitalisation des intitulés facture
Déjà implémenté (`@blur="capitalizeFirstLetter(line)"` dans `ClientInvoiceForm.vue`) — vérification rapide, ticket fermé.

### BIZ-150 — Accepter la virgule comme séparateur décimal
Champs `quantity` et `unit_price` dans `ClientInvoiceForm.vue` : `type="text" inputmode="decimal"` + fonction `normalizeDecimalInput()` (remplace `,` par `.` à la saisie, met à jour le modèle via `parseFloat`).

### BIZ-157 — Pagination 50 items par défaut
`:rows="50"` dans tous les composants Vue (anciennement 20). Remplacement global dans `frontend/src/`.

</details>

<details>
<summary>Lot CR — Correctifs revue de code (2026-05-02)</summary>

### TEC-133 — Access token en mémoire uniquement (XSS)
Token stocké dans un `ref` Pinia non persisté ; rechargement via `POST /api/auth/refresh` (cookie HttpOnly) ; `initFromStorage()` supprimé.

### TEC-134 — Atomicité audit log
`record_audit()` appelé avant `await db.commit()` dans `update_user`.

### TEC-135 — Race condition numérotation factures
Retry loop sur `IntegrityError` (3 tentatives) dans `invoice_service._next_number()`.

### TEC-136 — Chemins relatifs en base
`Invoice.file_path` / `Invoice.pdf_path` stockés en relatif ; résolution absolue uniquement à la lecture via `resolve_file_path()`.

### TEC-137 — Décodage JWT unique
Payload JWT mis en cache dans `request.state.jwt_payload` par le middleware ; `get_current_user` le réutilise.

### TEC-138 — Rate limiter : mémoire bornée
Purge des clés expirées toutes les 100 tentatives dans `rate_limiter.py`.

### TEC-139 — Tokens OpenAI en streaming
`stream_options={"include_usage": True}` + extraction de `chunk.usage` sur le dernier événement SSE.

### TEC-140 — Pagination audit log
`GET /api/settings/audit-logs` : `skip`, `limit`, `action`, `actor_id`, `from_date`, `to_date` ; vue Paramètres mise à jour.

### TEC-141 — Constante `USER_ROLES`
`frontend/src/constants/roles.ts` : source unique pour les chaînes de rôles.

### TEC-155 — Suppression `# type: ignore`
13 suppressions dans `backend/routers/invoice.py` éliminées ; annotations corrigées.

</details>

Tickets fermés hors lots récents : **BIZ-127**, **BIZ-128**, **BIZ-129**, **BIZ-130**, **BIZ-131**, **BIZ-132**, **TEC-156**, **BIZ-198**, **BIZ-199**, **BIZ-200**.

> Lots et tickets plus anciens → [backlog-archive.md](backlog-archive.md)

<details>
<summary>TEC-156 — Fix token auth chat (2026-05-03)</summary>

### TEC-156 — Fix token auth chat (localStorage → Pinia)

`streamChat` dans `api/chat.ts` lisait `localStorage.getItem('access_token')` — toujours `null` car le token est stocké uniquement en mémoire Pinia (mitigation XSS). Chaque `POST /api/chat` retournait 401. Corrigé en lisant `useAuthStore().accessToken`. Découvert lors du test du Lot DOC (2026-05-03).

</details>

<details>
<summary>BIZ-127 — Dialogue confirmation avant envoi e-mail facture (2026-05-02)</summary>

### BIZ-127 — Dialogue de confirmation avant envoi e-mail facture

- **Terminé** : 2026-05-02
- **Livré** : dialog de confirmation avec destinataire (lecture seule), sujet et corps éditables + aperçu PDF ; endpoint `GET /api/invoices/{id}/email-preview` ; `POST /api/invoices/{id}/send-email` accepte payload `{subject, body}` édité par l'utilisateur ; helpers `compose_subject()`/`compose_body()` extraits, `send_invoice_email` accepte `override_subject`/`override_body` ; audit log inclut le sujet ; 8 nouveaux tests unitaires.

</details>

<details>
<summary>BIZ-128 — Modèles d'e-mail configurables (2026-05-02)</summary>

### BIZ-128 — Modèles d'e-mail configurables dans les paramètres

- **Terminé** : 2026-05-02
- **Livré** : colonnes `email_subject_template` et `email_body_template` sur `app_settings` (migration 0037) ; section dédiée dans les paramètres SMTP ; variables `{invoice_number}`, `{description}`, `{association_name}`, `{invoice_ref}` ; `_SafeFormatMap` pour variables inconnues ; 7 nouveaux tests unitaires.

</details>

<details>
<summary>BIZ-130 — Confirmation de dépôt bancaire + métriques espèces/chèques (2026-05-02)</summary>

### BIZ-130 — Confirmation de dépôt bancaire + métriques espèces/chèques

- **Terminé** : 2026-05-02
- **Livré** :
  - Migration Alembic 0038 — colonnes `confirmed` (Boolean, default false) et `confirmed_date` (Date nullable) sur la table `deposits`
  - `bank_service.confirm_deposit()` — marque un dépôt comme confirmé (date = aujourd'hui) ; `list_deposits` accepte filtre `confirmed`
  - Endpoint `POST /api/bank/deposits/{id}/confirm` (write access) + audit log `bank.deposit.confirm`
  - Vue Banque : panneau « Dépôts en attente de confirmation » (visible si ≥ 1 dépôt non confirmé) — résumé nb chèques / nb encaissements + montant + bouton confirmer ; colonne « Statut » dans le tableau des dépôts avec filtre
  - Vue Paiements : deux métriques séparées « Chèques à remettre » et « Espèces à déposer » remplacent le compteur unique « Non remis »
  - 4 nouveaux tests d'intégration (`test_confirm_deposit`, déjà confirmé → 422, non trouvé → 404, filtre confirmed)

</details>

---

## Légende

| Préfixe | Signification |
| --- | --- |
| BIZ-NNN | Fonctionnalité métier — valeur utilisateur directe |
| TEC-NNN | Technique — qualité, refactoring, tests, sécurité technique |
| CHR-NNN | Maintenance — outillage, documentation, CI, DevOps |

| Priorité | Signification |
| --- | --- |
| P1 | Important — fort impact métier, risque ou besoin opérationnel |
| P2 | Utile — amélioration à programmer |
| P3 | Confort, finition ou dette technique optionnelle |

| Statut | Signification |
| --- | --- |
| Bac d'entrée | Besoin capturé, pas encore arbitré |
| ⬜ Prêt | Besoin clarifié, prêt à être pris |
| 🔄 En cours | Implémentation en cours sur une branche active |
| ✅ Fait | Sujet livré — détail dans `CHANGELOG.md` |
