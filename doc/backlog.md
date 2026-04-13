# Backlog — changements et améliorations

## But

Ce document est la source de vérité des changements à discuter puis à planifier hors roadmap initiale :

- corrections suite aux tests ;
- améliorations UX ;
- évolutions fonctionnelles ;
- dette technique ciblée.
- points remontés au fil des échanges avec l'utilisateur.

Il est volontairement simple, versionné dans Git, et relu en même temps que le code.

Tout point concret signalé par l'utilisateur et nécessitant un suivi doit être noté ici avec un statut explicite, puis mis à jour au fur et à mesure de son avancement.

## Règles de fonctionnement

1. Ajouter chaque nouveau sujet dans **Bac d'entrée** avec une description courte et concrète.
2. Proposer une **priorité** (`P1`, `P2`, `P3`) avant arbitrage.
3. Passer un sujet en **Prêt** une fois le besoin clarifié.
4. Déplacer en **En cours** quand on décide de le traiter.
5. Déplacer en **Fait** uniquement après livraison.
6. Ne pas laisser de sujet actionnable uniquement dans la conversation si son suivi doit continuer au-delà de l'échange en cours.

### Signification des priorités

- `P1` — important à discuter rapidement ; impact produit ou risque métier élevé.
- `P2` — utile mais pas bloquant ; amélioration à programmer.
- `P3` — confort, dette technique ou sujet optionnel.

### Signification des statuts

- `Bac d'entrée` — idée ou besoin capturé, pas encore arbitré.
- `Prêt` — sujet clarifié, prêt à être pris.
- `En cours` — traité dans une branche active.
- `Fait` — livré.

## Priorités proposées pour la prochaine discussion

1. **BL-008** — import Excel comme validation itérative de convergence avec la comptabilité réelle
2. **BL-004** — historique d'import visible dans l'interface
3. **BL-006** — traiter les warnings de dépréciation FastAPI dans la suite de tests

## Bac d'entrée

| ID | Type | Zone | Priorité proposée | Sujet |
|---|---|---|---|---|
| BL-001 | Process | Produit | P1 | Stabiliser la méthode de triage du backlog et la revue des priorités en début de séance |
| BL-004 | Amélioration | Import Excel | P2 | Afficher un historique d'import exploitable dans l'UI avec type, date, compteurs, lignes ignorées et erreurs |
| BL-005 | Amélioration | Comptabilité / Import | P2 | Étendre la déduplication comptable au-delà des doublons exacts pour couvrir les doublons métier proches |
| BL-006 | Technique | API / Framework | P3 | Traiter les warnings de dépréciation `HTTP_422_UNPROCESSABLE_ENTITY` remontés par la suite de tests |
| BL-007 | Process | Outillage | P3 | Définir si ce backlog doit rester la source de vérité unique ou être synchronisé plus tard avec des issues GitHub |
| BL-008 | Amélioration | Import Excel / Qualité | P1 | Faire évoluer l'import Excel pour qu'il serve d'abord à l'initialisation depuis les fichiers 2024/2025, puis à une validation itérative régulière entre Excel et Solde sans manque ni divergence |
| BL-010 | Décision | Exercices comptables / Import | P1 | Définir comment clôturer les exercices historiques importés sans dupliquer des écritures de clôture ou de report à nouveau déjà présentes dans Excel |
| BL-009 | Amélioration | Comptabilité / Paramétrage | P1 | Étendre le plan comptable par défaut pour couvrir les comptes réellement présents dans les imports historiques et fiabiliser les états comptables associés |

## Détail des sujets

### BL-001 — Stabiliser la méthode de triage du backlog

- **Pourquoi** : éviter que les retours de tests, idées d'amélioration et changements de cap restent dans les conversations seulement.
- **Résultat attendu** : un rituel simple de revue/priorisation et une règle claire sur ce qui entre dans le backlog.
- **Décision à prendre** : fréquence de revue, niveau de détail attendu, et règle de passage `Bac d'entrée` -> `Prêt`.

### BL-002 — Documentation utilisateur import/reset

- **Pourquoi** : l'écran d'import a été clarifié, mais il manque encore une documentation utilisateur durable et centralisée.
- **Résultat attendu** : une doc en français expliquant :
  - différence entre import `Gestion` et `Comptabilité` ;
  - lien avec les exercices comptables ;
  - rôle du plan comptable et des règles ;
  - comportement de coexistence avec les écritures déjà présentes ;
  - portée exacte de la réinitialisation des données.
- **Constat du 2026-04-12** : documentation utilisateur rédigée dans `doc/user/import-excel-et-reinitialisation.md`, avec un mode d'emploi orienté tests manuels et la portée exacte du reset.

### BL-003 — Campagne de retest métier sur imports réels

- **Pourquoi** : plusieurs corrections récentes ont modifié l'import fournisseurs, la coexistence compta, les dates et la visibilité UI.
- **Résultat attendu** : une nouvelle passe de tests manuels structurés sur les vrais fichiers historiques avec une liste courte d'écarts résiduels.
- **Sortie attendue** : soit validation fonctionnelle, soit nouveaux items backlog bien découpés.
- **Constat du 2026-04-12** : rejeu réel effectué sur base isolée avec les exports historiques présents dans `data/`, sans écart bloquant ; la procédure import doit simplement refléter les nouveaux compteurs et le besoin de précharger les exercices couvrant toutes les dates réellement présentes dans les fichiers.

### BL-004 — Historique d'import visible dans l'interface

- **Pourquoi** : l'application garde déjà des traces techniques d'import, mais elles ne sont pas encore facilement consultables dans l'UI.
- **Résultat attendu** : un écran ou un panneau permettant de voir les imports passés, leur type, leur date, leur résultat et les principales anomalies.
- **Bénéfice** : faciliter le support, le diagnostic et la compréhension après un import.

### BL-005 — Déduplication comptable avancée

- **Pourquoi** : la coexistence actuelle ignore les doublons exacts, ce qui sécurise le cas principal, mais ne traite pas encore les cas "presque identiques".
- **Résultat attendu** : définir puis implémenter une stratégie explicite pour les doublons métier proches sans créer de faux positifs.
- **Attention** : sujet sensible ; priorité à la sûreté métier avant l'automatisation.

### BL-006 — Warnings de dépréciation FastAPI

- **Pourquoi** : la suite complète remonte encore des warnings autour de `HTTP_422_UNPROCESSABLE_ENTITY`.
- **Résultat attendu** : éliminer ces warnings pour garder une base de tests propre et éviter une casse future lors des montées de version.

### BL-007 — Source de vérité backlog vs issues GitHub

- **Pourquoi** : on peut rester sur un backlog Git simple, ou décider plus tard de dupliquer certains sujets en issues pour le suivi collaboratif.
- **Résultat attendu** : une convention claire pour éviter les doublons et la divergence entre outils.
- **Proposition actuelle** : garder `doc/backlog.md` comme source de vérité tant qu'on reste dans une boucle de travail rapide.

### BL-008 — Import Excel comme validation itérative de convergence

- **Pourquoi** : l'import Excel ne doit pas seulement servir au chargement initial des historiques 2024/2025 ; il doit ensuite devenir un garde-fou qualité pour comparer régulièrement la comptabilité tenue en parallèle dans Excel et dans Solde.
- **Phase 1** : utiliser l'import pour initialiser proprement Solde à partir des fichiers comptables existants `2024` et `2025`.
- **Phase 2** : pendant la période de double saisie Excel + Solde, réimporter régulièrement les fichiers Excel pour vérifier que toutes les écritures et entrées réalisées dans Solde correspondent exactement à celles d'Excel.
- **Résultat attendu** : détecter toute écriture manquante, en trop ou divergente entre Excel et Solde, avec un niveau d'exigence élevé sur l'exactitude des montants, dates, libellés et équilibres.
- **Enjeu** : sujet critique pour la confiance métier et la qualité globale de l'application pendant toute la phase de transition hors Excel.

### BL-009 — Enrichir le plan comptable par défaut à partir des imports réels

- **Pourquoi** : le rejeu réel des fichiers `Gestion` et `Comptabilité` utilise davantage de comptes que ceux actuellement seedés par défaut, ce qui ne bloque pas l'import mais peut dégrader les libellés affichés et l'exactitude des états calculés à partir du plan comptable connu.
- **Constat du 2026-04-12** : sur `35` comptes distincts rencontrés pendant le rejeu complet, `16` ne sont pas présents dans le plan comptable par défaut actuel de `24` comptes.
- **Comptes manquants les plus visibles** : `626500`, `512102`, `106800`, `401103`, `401104`, `416001`, `416002`, `443000`, `616100`, `623400`, `625000`, `625700`, `740000`, `613200`, `623000`, `768100`.
- **Résultat attendu** : proposer un plan comptable par défaut plus proche de la comptabilité réellement tenue dans Excel, au moins pour les comptes récurrents, afin d'améliorer la lisibilité du journal, de la balance, du grand livre et du compte de résultat.
- **Point d'attention** : certains comptes manquants sont des sous-comptes métier ou bancaires ; il faudra décider s'ils doivent être seedés explicitement, dérivés d'un compte parent, ou simplement ajoutés lors de la reprise initiale.
- **Constat du 2026-04-12 (suite)** : enrichissement implémenté dans le seed par défaut avec les comptes récurrents des imports historiques ; les comptes historiques `401103`, `401104`, `416001` et `416002` sont conservés mais seedés inactifs pour préserver les libellés et les types sans les remettre dans les listes actives.

### BL-010 — Stratégie de clôture des exercices historiques importés

- **Pourquoi** : l'import rattache les écritures aux exercices par date, mais la clôture actuelle de Solde génère elle-même des écritures de résultat et le report à nouveau du nouvel exercice ; sur une reprise historique issue d'Excel, il faut éviter de recréer dans Solde des écritures de clôture déjà présentes dans les journaux importés.
- **Question à trancher** : faut-il laisser les exercices historiques ouverts après import, les clôturer administrativement sans nouvelle écriture, ou adapter la clôture pour détecter et respecter l'historique déjà présent ?
- **Résultat attendu** : une stratégie explicite et sûre pour garder un seul exercice courant ouvert dans l'application sans fausser le journal comptable historique.
- **Décision du 2026-04-12** : pendant la reprise, laisser tous les exercices historiques ouverts ; une fois les imports et contrôles terminés, clôturer les anciens exercices via une clôture administrative sans générer de nouvelle écriture de clôture ni de report à nouveau. La clôture comptable standard reste réservée aux exercices réellement tenus dans Solde.

### BL-011 — Exercice courant global et suppression des plafonds arbitraires par écran

- **Pourquoi** : les écrans `Factures`, `Paiements` et `Journal` chargent aujourd'hui un sous-ensemble borné par l'API, puis appliquent tri, filtre texte et pagination localement ; dès que le volume dépasse la limite chargée, le comportement devient incohérent pour l'utilisateur.
- **Constat du 2026-04-12** : un endpoint backend `/accounting/fiscal-years/current` existe déjà, plusieurs écrans comptables acceptent déjà `fiscal_year_id`, mais il n'existe pas encore de store global ni de sélecteur d'exercice partagé dans le shell frontend.
- **Résultat attendu** : un exercice courant sélectionnable globalement, visible depuis les écrans principaux, utilisé comme filtre par défaut pour charger l'intégralité des données du périmètre courant afin que tris, filtres et compteurs reflètent réellement l'exercice affiché.
- **Point d'attention** : cette approche doit distinguer les écrans raisonnablement bornables à un exercice courant de ceux qui nécessitent encore une pagination serveur réelle si un exercice devient volumineux.
- **Constat du 2026-04-12 (suite)** : implémentation livrée avec un store Pinia global d'exercice, un sélecteur partagé dans le layout principal, le branchement des vues comptables sur `fiscal_year_id` existant et le filtrage des écrans `Factures` / `Paiements` par plage de dates métier (`from_date` / `to_date`) sans ajout de colonne en base.
- **Constat du 2026-04-12 (correctif)** : la sélection automatique de l'exercice courant pointait initialement vers le plus ancien exercice ouvert ; le backend retourne désormais l'exercice ouvert couvrant la date du jour, avec repli sur le plus récent exercice ouvert, et le store frontend ignore les anciennes sélections auto-persistées pour éviter de masquer des données valides après import.

### BL-012 — Liste des paiements: référence visible et édition directe

- **Pourquoi** : la liste des paiements n'affichait pas la référence métier et n'offrait plus d'action d'édition, ce qui bloquait les corrections rapides depuis l'écran principal.
- **Résultat attendu** : afficher la colonne `Référence` dans le tableau des paiements et permettre la modification directe d'un paiement existant sans quitter la vue.
- **Constat du 2026-04-12** : correction livrée avec colonne `Référence`, bouton d'édition par ligne et dialogue de modification branché sur l'API `PUT /payments/{id}`.

### BL-013 — Journal de caisse: référence, détail et édition directe

- **Pourquoi** : le journal de caisse n'affichait pas la référence métier et ne permettait ni de consulter le détail d'une écriture ni de la corriger depuis l'écran principal.
- **Résultat attendu** : afficher la référence dans la liste, proposer un panneau de détail et brancher une édition directe d'une écriture existante.
- **Constat du 2026-04-12** : correction livrée avec colonne `Référence`, bouton de détail, bouton d'édition, endpoints backend `GET /cash/entries/{id}` et `PUT /cash/entries/{id}`, ainsi que recalcul cohérent des soldes après modification.

### BL-014 — Journal comptable: lisibilité métier et navigation vers les factures

- **Pourquoi** : le journal exposait surtout des lignes comptables brutes sans libellé de compte, sans référence métier, sans tiers lié et sans action de consultation utile pour l'utilisateur.
- **Résultat attendu** : enrichir le journal avec les libellés de comptes, les références métier, le nom du tiers, le détail d'une écriture, l'édition des écritures manuelles et, quand possible, un accès direct à la facture concernée.
- **Constat du 2026-04-12** : correction livrée avec enrichissement backend du journal, affichage frontend des comptes et contreparties, dialogue de détail, édition des paires manuelles et navigation directe vers les vues de factures client/fournisseur via l'identifiant de facture.

## En cours

- Aucun sujet pour le moment.

## Fait

- **BL-002** — Documentation utilisateur import/reset rédigée dans `doc/user/import-excel-et-reinitialisation.md` pour accompagner les tests manuels de reprise et clarifier la réinitialisation.
- **BL-003** — Campagne de retest métier sur imports réels 2024/2025 rejouée sur base isolée avec les fichiers présents dans `data/` ; aucun écart bloquant constaté, coexistence comptable validée sur les exports réels et procédure mise à jour.
- **BL-009** — Plan comptable par défaut enrichi à partir des comptes réellement rencontrés dans les imports historiques ; les sous-comptes historiques non reconduits (`401103`, `401104`, `416001`, `416002`) sont conservés comme inactifs pour ne pas dégrader les états sur l'historique importé.
- **BL-010** — Stratégie validée et première implémentation livrée : ajout d'une clôture administrative des exercices historiques importés, sans génération d'écritures de clôture ni de report à nouveau, plus documentation opératoire associée.
- **BL-011** — Exercice courant global implémenté dans le frontend avec sélecteur partagé et store dédié ; les écrans comptables utilisent l'exercice sélectionné, et `Factures` / `Paiements` chargent désormais l'ensemble du périmètre métier de l'exercice via des filtres de dates backend plutôt qu'un plafond arbitraire local.
- **BL-012** — Liste des paiements enrichie avec la référence visible dans le tableau et un dialogue d'édition directe pour corriger montant, date, mode de règlement, numéro de chèque, référence et notes depuis l'écran principal.
- **BL-013** — Journal de caisse enrichi avec la référence visible, un dialogue de détail, une édition directe des écritures et un recalcul fiable des soldes après modification.
- **BL-014** — Journal comptable enrichi avec les libellés de comptes, les références métier, les tiers liés, un détail consultable, l'édition des écritures manuelles et une navigation directe vers les factures correspondantes.
