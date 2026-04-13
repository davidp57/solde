# Backlog — Solde ⚖️

## But

Ce document est la source de vérité des changements à discuter puis à planifier hors roadmap de jalons :

- corrections découvertes en test ou en usage réel ;
- améliorations UX ;
- évolutions fonctionnelles ;
- dette technique ciblée ;
- suites à donner aux points remontés pendant les échanges avec l'utilisateur.

Il reste volontairement léger, versionné dans Git, et relu en même temps que le code.

Tout sujet concret qui doit survivre au-delà de la séance en cours doit être capturé ici avec un statut explicite et mis à jour au fil du travail.

## Règles de fonctionnement

1. Ajouter chaque nouveau sujet dans **Bac d'entrée** avec une formulation courte et concrète.
2. Proposer une **priorité** (`P1`, `P2`, `P3`) avant arbitrage.
3. Passer un sujet en **Prêt** une fois le besoin clarifié.
4. Déplacer en **En cours** quand le travail démarre sur une branche active.
5. Déplacer en **Fait** quand l'implémentation est livrée et considérée comme terminée côté backlog.
6. Suivre les dates avec le format ISO (`YYYY-MM-DD`) : `created`, `started`, `completed`.
7. Ne pas laisser de suite actionnable uniquement dans la conversation si elle doit être retrouvée plus tard.

### Signification des priorités

- `P1` — important à discuter rapidement ; fort impact métier, besoin opérationnel ou risque notable.
- `P2` — utile mais non bloquant ; amélioration à programmer.
- `P3` — confort, finition ou dette technique optionnelle.

### Signification des statuts

- `Bac d'entrée` — besoin capturé, pas encore arbitré.
- `Prêt` — besoin clarifié, prêt à être pris.
- `En cours` — sujet en cours d'implémentation sur une branche active.
- `Fait` — sujet livré et prêt à être fusionné ou déjà intégré.

### Champs de dates

- `created` — date d'entrée initiale dans le backlog.
- `started` — date de démarrage effectif sur une branche.
- `completed` — date à laquelle le sujet est considéré comme livré côté backlog.
- Toujours utiliser le format ISO `YYYY-MM-DD`.
- Dans `Détail des sujets`, ajouter systématiquement une ligne `Dates` avec uniquement les champs connus pour le statut courant.
- Pour un sujet historique déjà traité avant structuration complète du backlog, approximer `created` à partir de la première trace utile disponible dans l'historique récent du dépôt.

## Priorités proposées pour la prochaine discussion

1. **BL-025** — corriger le report à nouveau et les soldes faux dans le grand livre multi-exercices.
2. **BL-023** — revalider les droits réels par rôle et la visibilité des écrans comptables.
3. **BL-024** — clarifier le workflow de saisie des paiements et corriger les remises en banque automatiques.

## Bac d'entrée

| ID | Créé le | Type | Zone | Priorité proposée | Sujet |
|---|---|---|---|---|---|
| BL-004 | 2026-04-12 | Amélioration | Import Excel / Support | P2 | Afficher un historique d'import exploitable dans l'UI avec type, date, compteurs, diagnostics, et une traçabilité suffisamment fine des objets créés |
| BL-005 | 2026-04-12 | Décision | Comptabilité / Import | P1 | Formaliser la politique de coexistence entre imports Excel, écritures manuelles ou auto-générées déjà présentes, et doublons métier proches |
| BL-006 | 2026-04-12 | Technique | API / Framework | P3 | Traiter les warnings de dépréciation `HTTP_422_UNPROCESSABLE_ENTITY` remontés par la suite de tests |
| BL-008 | 2026-04-12 | Amélioration | Import Excel / Qualité | P1 | Faire évoluer l'import Excel pour qu'il serve d'abord à l'initialisation depuis les fichiers 2024/2025, puis à une validation itérative régulière entre Excel et Solde sans manque ni divergence |
| BL-015 | 2026-04-13 | Amélioration | Import Excel / Outillage | P2 | Ajouter un reset sélectif orienté reprise pour rejouer proprement un import par filière ou période sans repartir systématiquement d'un effacement global |
| BL-016 | 2026-04-13 | Amélioration | Frontend / i18n | P2 | Harmoniser les libellés UI, supprimer les textes en dur restants et rendre la microcopie plus cohérente d'un écran à l'autre |
| BL-017 | 2026-04-13 | Amélioration | Frontend / Localisation | P2 | Uniformiser l'affichage des dates et périodes au format français dans toute l'interface sans changer les formats d'échange API |
| BL-018 | 2026-04-13 | Amélioration | Frontend / UX listes | P2 | Consolider les écrans de liste pour rendre tri, filtre, colonnes et états de vue plus clairs et cohérents |
| BL-019 | 2026-04-13 | Documentation | Projet / Exploitation | P1 | Refaire le README et la documentation technique d'installation, mise à jour, pile techno, configuration et exploitation Docker |
| BL-020 | 2026-04-13 | Documentation | Développement | P3 | Documenter clairement comment participer au projet : prérequis, environnement local, commandes utiles, qualité attendue et workflow PR |
| BL-022 | 2026-04-13 | Évolution | Utilisateurs / Sécurité | P1 | Renforcer la gestion des utilisateurs avec des rôles métier plus clairs, la création et l'administration des comptes, l'autonomie sur le profil et un socle de sécurité de compte plus complet |
| BL-023 | 2026-04-13 | Correction | Permissions / Comptabilité | P1 | Revalider les droits réels des rôles `consultation` et `secrétaire`, restaurer la visibilité attendue des écrans comptables pour l'admin et rendre à nouveau visible le choix d'exercice |
| BL-024 | 2026-04-13 | Correction | Paiements / Banque | P1 | Clarifier le workflow cible de saisie des paiements et corriger l'automatisme qui remet en banque les paiements `espèces` et `virement` dès leur encodage |
| BL-025 | 2026-04-13 | Correction | Comptabilité / Exercices | P1 | Corriger le cumul des écritures d'ouverture entre exercices dans le grand livre pour retrouver des soldes justes comptablement |

## Détail des sujets

### BL-001 — Stabiliser la méthode de triage du backlog

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Pourquoi** : éviter que les retours de tests, idées d'amélioration et changements de cap restent seulement dans l'historique de conversation.
- **Résultat attendu** : une règle simple d'entrée dans le backlog, de priorisation et de mise à jour au fil du travail.
- **Livré parce que** : le backlog est maintenant utilisé comme support de suivi versionné, avec statuts, priorités et mises à jour récurrentes.

### BL-002 — Documentation utilisateur import/reset

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Pourquoi** : l'écran d'import a été clarifié, mais il fallait une documentation utilisateur durable et centralisée.
- **Résultat attendu** : une documentation en français expliquant la différence entre import `Gestion` et `Comptabilité`, le lien avec les exercices, le rôle du plan comptable et des règles, la coexistence comptable et la portée exacte de la réinitialisation.
- **Livré parce que** : la documentation utilisateur a été rédigée dans `doc/user/import-excel-et-reinitialisation.md` avec un mode d'emploi orienté reprise et tests manuels.

### BL-003 — Campagne de retest métier sur imports réels

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Pourquoi** : plusieurs corrections récentes ont modifié l'import fournisseurs, la coexistence comptable, les dates et la lisibilité UI.
- **Résultat attendu** : une nouvelle passe de tests manuels structurés sur les fichiers historiques réels, avec une liste courte d'écarts résiduels.
- **Livré parce que** : le rejeu réel sur base isolée a confirmé l'absence d'écart bloquant ; la procédure a seulement été ajustée pour refléter les nouveaux compteurs et le besoin de précharger les exercices couvrant toutes les dates utiles.

### BL-004 — Historique d'import visible dans l'interface

- **Dates** : `created=2026-04-12`
- **Pourquoi** : l'application conserve déjà des traces techniques d'import, mais elles restent peu visibles pour l'utilisateur.
- **Résultat attendu** : un écran ou panneau affichant les imports passés, leur type, leur date, leur résultat, les principales anomalies, et un niveau de traçabilité suffisant pour comprendre quels objets ont été créés.
- **Point d'attention** : décider si le résumé sérialisé actuel dans `import_logs` suffit, ou si certains objets créés doivent être reliés explicitement à leur import source pour faciliter le support.

### BL-005 — Politique de coexistence import / écritures existantes

- **Dates** : `created=2026-04-12`
- **Pourquoi** : l'import historique a désormais des garde-fous solides, mais la politique cible n'est pas encore entièrement tranchée quand des écritures manuelles, des écritures auto-générées ou des doublons métier proches coexistent déjà en base.
- **Résultat attendu** : une politique explicite, documentée et testée qui dit pour chaque cas de coexistence ce qui doit être bloqué, toléré, ignoré comme doublon ou remonté pour revue manuelle avant d'ouvrir davantage l'import `Comptabilite` en réel.
- **Cas à trancher explicitement** :
	- import `Comptabilite` alors que des écritures auto-générées issues de la gestion existent déjà ;
	- import `Comptabilite` alors que des écritures `MANUAL` existent déjà sur la même période ;
	- réimport ou import tardif d'une donnée métier déjà présente mais pas strictement identique ;
	- doublon exact versus doublon métier proche ;
	- écart ambigu qui ne peut pas être classé de façon sûre sans validation humaine.
- **Sorties attendues de la décision** :
	- une matrice de règles simple du type `bloquer / autoriser / ignorer / signaler` par famille de cas ;
	- une traduction homogène de ces règles dans la preview, l'import réel et les diagnostics structurés ;
	- des catégories stables côté rapport pour distinguer clairement `blocked-by-coexistence`, `ignored-as-duplicate`, `manual-review-required` et les cas autorisés.
- **Critère d'acceptation** : à lecture de la preview, un utilisateur doit comprendre sans ambiguïté pourquoi un cas coexistence est bloqué, toléré ou seulement signalé, et la même décision doit être respectée à l'import réel.
- **Point d'attention** : la sûreté métier prime sur l'automatisation agressive ; en cas d'ambiguïté non triviale, la règle par défaut doit être le blocage ou la revue manuelle, jamais l'import silencieux.

### BL-006 — Warnings de dépréciation FastAPI

- **Dates** : `created=2026-04-12`
- **Pourquoi** : la suite complète remonte encore des warnings autour de `HTTP_422_UNPROCESSABLE_ENTITY`.
- **Résultat attendu** : éliminer ces warnings pour garder une base de tests propre et limiter le risque de casse lors des montées de version.

### BL-007 — Source de vérité backlog vs issues GitHub

- **Dates** : `created=2026-04-12`, `completed=2026-04-13`
- **Pourquoi** : il faut éviter une divergence future entre backlog Git et éventuelles issues GitHub.
- **Résultat attendu** : une convention claire sur l'outil qui fait foi et les cas où un doublon assumé serait acceptable.
- **Livré parce que** : la convention de travail actuelle est suffisamment claire pour l'instant : `doc/backlog.md` reste la source de vérité, et un éventuel relais vers des issues GitHub ne sera rouvert que si le mode de collaboration change.

### BL-008 — Import Excel comme validation itérative de convergence

- **Dates** : `created=2026-04-12`
- **Pourquoi** : l'import Excel ne doit pas seulement servir à la reprise initiale 2024/2025 ; il doit aussi devenir un garde-fou qualité pendant la période de double tenue Excel + Solde.
- **Phase 1** : initialiser proprement Solde à partir des fichiers historiques existants.
- **Phase 2** : réimporter régulièrement Excel pour vérifier que les écritures et mouvements saisis dans Solde correspondent exactement à la réalité comptable de référence.
- **Résultat attendu** : détecter toute écriture manquante, en trop ou divergente, avec un haut niveau d'exigence sur montants, dates, libellés et équilibres, et une politique claire sur ce qui reste bloquant versus seulement signalé.
- **Premier lot visé** :
	- formaliser un contrat de comparaison par domaine (`Factures`, `Paiements`, `Caisse`, `Banque`, `Journal`) ;
	- ajouter un mode de comparaison sans écriture, probablement adossé à la preview existante ;
	- catégoriser les écarts avec des codes stables (`missing-in-solde`, `extra-in-solde`, `amount-mismatch`, `date-mismatch`, `ambiguous-match`, `ignored-by-policy`, `blocked-by-coexistence`) ;
	- produire un rapport exploitable avec résumé global, détail par feuille et exemples d'écarts ;
	- cibler d'abord la chaîne réelle `Gestion 2024` / `Gestion 2025` avant toute généralisation plus large.
- **Critère d'acceptation** : on doit pouvoir répondre, sans rien persister, à quatre questions simples : qu'est-ce qui manque dans Solde, qu'est-ce qui est en trop, qu'est-ce qui diverge, et qu'est-ce qui est ignoré volontairement selon la politique métier.
- **Hors périmètre initial** : pas de correction automatique des écarts, pas d'ouverture large de l'import `Comptabilite` en réel tant que `BL-005` n'est pas tranché, et pas d'outil générique de réconciliation déconnecté du cas de reprise réel.
- **Enjeu** : sujet critique pour la confiance métier pendant toute la transition hors Excel.

### BL-009 — Enrichir le plan comptable par défaut à partir des imports réels

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Pourquoi** : le rejeu réel des fichiers `Gestion` et `Comptabilité` faisait apparaître davantage de comptes que ceux seedés par défaut.
- **Résultat attendu** : un plan comptable par défaut plus proche des comptes réellement utilisés, pour améliorer journal, balance, grand livre et compte de résultat.
- **Livré parce que** : le seed par défaut a été enrichi avec les comptes récurrents observés ; les sous-comptes historiques `401103`, `401104`, `416001` et `416002` sont conservés comme inactifs pour préserver les libellés et les états sur l'historique importé.

### BL-010 — Stratégie de clôture des exercices historiques importés

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Pourquoi** : lors d'une reprise historique, il faut éviter de recréer dans Solde des écritures de clôture et de report à nouveau déjà présentes dans Excel.
- **Résultat attendu** : une stratégie explicite et sûre pour garder un seul exercice courant ouvert sans fausser le journal historique.
- **Livré parce que** : la stratégie retenue consiste à laisser les exercices historiques ouverts pendant la reprise, puis à les clôturer administrativement sans générer de nouvelles écritures de clôture ni de report à nouveau.

### BL-011 — Exercice courant global et suppression des plafonds arbitraires par écran

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Pourquoi** : plusieurs écrans chargeaient un sous-ensemble borné puis filtraient localement, ce qui devenait incohérent dès que le volume augmentait.
- **Résultat attendu** : un exercice courant global, visible et partagé, servant de filtre métier par défaut sur les écrans principaux.
- **Livré parce que** : un store global d'exercice, un sélecteur partagé et le branchement des écrans comptables sur l'exercice courant ont été mis en place, avec correction du choix automatique de l'exercice ouvert couvrant la date du jour.

### BL-012 — Liste des paiements : référence visible et édition directe

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Pourquoi** : la liste des paiements ne montrait plus la référence métier et ne permettait plus de correction rapide depuis l'écran principal.
- **Résultat attendu** : afficher la colonne `Référence` et permettre l'édition directe d'un paiement existant.
- **Livré parce que** : la vue expose maintenant la référence, un bouton d'édition par ligne et un dialogue de modification branché sur `PUT /payments/{id}`.

### BL-013 — Journal de caisse : référence, détail et édition directe

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Pourquoi** : le journal de caisse n'affichait pas la référence métier et ne permettait ni consultation détaillée ni correction rapide.
- **Résultat attendu** : afficher la référence, proposer un détail consultable et permettre l'édition directe d'une écriture.
- **Livré parce que** : la vue dispose maintenant d'une référence visible, d'un panneau de détail, d'une édition directe et d'un recalcul cohérent des soldes après modification.

### BL-014 — Journal comptable : lisibilité métier et navigation vers les factures

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Pourquoi** : le journal exposait surtout des lignes comptables brutes, peu utiles sans libellé, référence métier, tiers lié ou action de consultation.
- **Résultat attendu** : enrichir le journal avec les libellés de comptes, les références métier, le nom du tiers, le détail d'écriture, l'édition des écritures manuelles et, quand c'est possible, un accès direct à la facture concernée.
- **Livré parce que** : le backend et le frontend ont été enrichis pour fournir ces informations, consulter le détail, éditer les paires manuelles et naviguer directement vers les factures correspondantes.

### BL-015 — Reset sélectif orienté reprise d'import

- **Dates** : `created=2026-04-13`
- **Pourquoi** : le reset global actuel est utile pour les essais complets, mais il reste trop brutal quand on veut simplement rejouer une filière d'import, un exercice ou une séquence de reprise précise.
- **Résultat attendu** : proposer un reset plus fin, compréhensible et sûr, capable de supprimer uniquement le périmètre utile à rejouer tout en explicitant le traitement des journaux d'import et des dépendances métier.
- **Point d'attention** : ce sujet ne doit pas fragiliser l'intégrité des données ; il faut privilégier des scénarios de reset explicitement cadrés plutôt qu'un outil générique trop puissant.

### BL-016 — Harmonisation i18n et microcopie UI

- **Dates** : `created=2026-04-13`
- **Pourquoi** : malgré la forte couverture i18n actuelle, il reste encore des libellés incohérents, des formulations hétérogènes et potentiellement quelques textes en dur qui dégradent la perception de qualité.
- **Résultat attendu** : auditer puis corriger les libellés visibles pour que les écrans utilisent des clés i18n cohérentes, un vocabulaire homogène et une microcopie claire du login jusqu'aux vues métier.
- **Point d'attention** : viser d'abord les incohérences utilisateur visibles ; éviter de renommer massivement des clés stables si le gain produit est faible.

### BL-017 — Formats de dates et périodes en français

- **Dates** : `created=2026-04-13`
- **Pourquoi** : certaines dates ou périodes restent affichées dans un format trop technique ou ambigu, parfois plus proche d'une lecture ISO ou américaine que d'un usage métier français.
- **Résultat attendu** : uniformiser l'affichage des dates, mois et périodes au format français dans les tableaux, détails, dialogues et exports lisibles, tout en conservant les formats ISO pour les API et les échanges techniques.
- **Point d'attention** : distinguer clairement stockage/échange et présentation UI pour éviter les régressions côté backend ou formulaires.

### BL-018 — Lisibilité des écrans de liste : tri, filtre et états de vue

- **Dates** : `created=2026-04-13`
- **Pourquoi** : plusieurs écrans disposent déjà d'un filtre générique ou d'améliorations visuelles, mais l'expérience reste inégale selon les vues pour le tri, la lisibilité des colonnes, les états vides, le chargement et la compréhension du périmètre affiché.
- **Résultat attendu** : définir puis appliquer un socle UX commun pour les écrans de liste afin que recherche, tri, colonnes utiles, états vides, compteurs et chargement soient plus clairs et cohérents d'un écran à l'autre.
- **Point d'attention** : éviter l'uniformisation aveugle ; certaines vues métier auront toujours besoin d'adaptations spécifiques.

### BL-019 — README et documentation technique d'exploitation

- **Dates** : `created=2026-04-13`
- **Pourquoi** : la documentation projet existe mais reste encore trop dispersée ou trop implicite pour quelqu'un qui doit installer, mettre à jour ou exploiter Solde sans relire tout le dépôt.
- **Résultat attendu** : un README plus clair et une documentation technique structurée couvrant au minimum l'installation, la mise à jour, la pile technologique, la configuration, Docker, les volumes de données, les sauvegardes et les points d'exploitation courants.
- **Priorisation proposée** : lot rapide et structurant ; c'est le meilleur point d'entrée documentation à livrer vite car il clarifie aussi le cadre pour les docs plus détaillées.
- **Séquence recommandée** : commencer par clarifier le README, puis extraire les détails longs vers une doc technique dédiée plutôt que tout entasser en page d'accueil.
- **Point d'attention** : distinguer ce qui relève du guide d'exploitation réel de ce qui relève des détails purement développeur, pour éviter un README surchargé.

### BL-020 — Documentation de développement et contribution

- **Dates** : `created=2026-04-13`
- **Pourquoi** : contribuer efficacement au projet suppose aujourd'hui de reconstituer les prérequis et les conventions depuis plusieurs fichiers, ce qui freine la reprise de contexte et la qualité des contributions.
- **Résultat attendu** : une documentation développeur claire expliquant les prérequis, la mise en route locale, les commandes de build/test/lint, la qualité attendue, l'organisation du dépôt, le workflow de contribution et les attentes avant PR.
- **Priorisation proposée** : lot utile mais moins urgent ; à traiter après le cadrage README/doc technique et sans concurrencer le manuel utilisateur.
- **Séquence recommandée** : s'appuyer sur les commandes et conventions déjà stabilisées dans le dépôt, puis documenter le workflow réel de contribution sans créer de nouvelle couche procédurale artificielle.
- **Point d'attention** : cette documentation doit rester fidèle aux commandes réellement utilisées dans le dépôt, pas à un idéal théorique.

### BL-021 — Manuel utilisateur illustré et pas à pas

- **Dates** : `created=2026-04-13`, `started=2026-04-13`
- **Pourquoi** : la documentation utilisateur est la plus critique pour l'adoption réelle de Solde, car les utilisateurs visés ne sont pas nécessairement informaticiens et ont besoin d'un guidage concret, rassurant et progressif.
- **Résultat attendu** : un manuel utilisateur en français, très clair, illustré par des captures d'écran, couvrant pas à pas les actions principales comme saisir une facture client, enregistrer un paiement client, saisir un achat avec facture, gérer la caisse, consulter la banque, utiliser les imports et comprendre les principaux écrans comptables.
- **Critère d'acceptation** : un utilisateur non technique doit pouvoir suivre le guide pour exécuter les scénarios métier essentiels sans aide orale complémentaire.
- **Avancement actuel** : les lots 1 à 3 texte sont rédigés dans `doc/user/README.md` et `doc/user/manuel-utilisateur.md`, avec un périmètre volontairement calé sur les écrans réellement disponibles aujourd'hui et un renvoi complémentaire vers `doc/user/import-excel-et-reinitialisation.md` pour l'import Excel ; le lot 4 de stabilisation éditoriale et d'enrichissement visuel reste à faire.
- **Priorisation proposée** : chantier éditorial majeur et prioritaire côté valeur utilisateur ; il faut l'attaquer tôt, mais avec une stratégie incrémentale plutôt qu'un objectif “manuel complet” monolithique.
- **Séquence recommandée** : commencer par un socle de parcours essentiels (`facture client`, `paiement client`, `achat fournisseur`, `caisse`, `banque`, `import Excel`), puis enrichir ensuite avec les écrans comptables avancés et les cas plus rares.
- **Table des matières cible** :
	- introduction : à quoi sert Solde et à qui s'adresse l'application ;
	- premiers pas : connexion, repères de navigation, vocabulaire simple, exercice courant ;
	- gérer les contacts ;
	- créer une facture client ;
	- enregistrer un paiement client ;
	- saisir un achat fournisseur avec sa facture ;
	- gérer la caisse ;
	- gérer la banque et les remises ;
	- utiliser les imports Excel ;
	- consulter les écrans comptables ;
	- corriger une erreur fréquente ou revenir en arrière ;
	- questions fréquentes et glossaire métier.
- **Ordre de rédaction recommandé** :
	- lot 1 : `connexion et repères`, `contacts`, `facture client`, `paiement client` ;
	- lot 2 : `achat fournisseur`, `caisse`, `banque et remises` ;
	- lot 3 : `import Excel`, `lecture des écrans comptables`, `FAQ`, `glossaire` ;
	- lot 4 : stabilisation éditoriale et enrichissement visuel avec captures homogènes, encadrés d'alerte et version imprimable si utile.
- **Format attendu par chapitre** :
	- objectif simple ;
	- prérequis éventuels ;
	- étapes numérotées ;
	- capture(s) annotée(s), ajoutées seulement en fin de chantier quand les écrans sont suffisamment stabilisés ;
	- résultat attendu ;
	- erreurs fréquentes ou points d'attention.
- **Point d'attention** : ce manuel doit privilégier les parcours métier concrets, le vocabulaire simple et les écrans réels de l'application, plutôt qu'une description abstraite des fonctionnalités ; les captures doivent arriver en dernière étape pour éviter une maintenance inutile tant que l'UI continue d'évoluer.

### BL-022 — Gestion des utilisateurs, rôles et sécurité de compte

- **Dates** : `created=2026-04-13`, `started=2026-04-13`
- **Pourquoi** : l'authentification existe déjà, mais la gestion des utilisateurs reste encore trop limitée pour un usage réel durable avec plusieurs profils, une administration claire des comptes et des attentes minimales de sécurité.
- **Résultat attendu** : faire évoluer la gestion des comptes pour couvrir un vrai cycle de vie utilisateur : rôles métier lisibles, création et administration des comptes, autonomie minimale des utilisateurs sur leur propre profil et mécanismes de sécurité cohérents pour l'accès au compte.
- **Périmètre fonctionnel visé** :
	- revoir les rôles pour coller aux usages métier cibles (`admin`, `gestionnaire`, `comptable`) avec une matrice d'autorisations compréhensible ;
	- permettre la création, l'activation, la désactivation et la gestion courante des comptes ;
	- permettre à chaque utilisateur de consulter et modifier son profil dans un périmètre maîtrisé ;
	- couvrir au minimum le changement de mot de passe, la réinitialisation ou récupération de compte, et les garde-fous usuels d'authentification.
- **Questions à trancher** :
	- comment faire correspondre les rôles actuels aux rôles métier attendus sans casser les règles d'autorisation déjà en place ;
	- quelle part de gestion du profil est laissée à l'utilisateur lui-même versus à l'administrateur ;
	- quel mécanisme réaliste retenir pour le mot de passe perdu dans un contexte associatif auto-hébergé.
- **Critère d'acceptation** : un administrateur doit pouvoir gérer les comptes et leurs rôles sans intervention technique, et un utilisateur doit pouvoir accéder à son compte, gérer son profil essentiel et récupérer ou faire réinitialiser son accès selon un processus clair et sûr.
- **État de départ actuel** : l'application dispose déjà d'une authentification JWT, d'un utilisateur courant, d'une création de compte réservée à l'admin et de rôles techniques (`readonly`, `secretaire`, `tresorier`, `admin`), mais pas encore d'interface complète ni de cycle de vie cohérent du compte.
- **Avancement actuel** : les lots 1 et 2 sont désormais intégrés dans `develop` avec la documentation des rôles et l'administration des comptes ; le retest métier laisse toutefois ouverte la question de la matrice d'autorisations réellement observée, capturée séparément dans `BL-023`.
- **Lotissement recommandé** :
	- lot 1 : clarifier la cible produit des rôles et produire une matrice d'autorisations lisible ;
	- lot 2 : ajouter l'administration des comptes (`liste`, `création`, `activation/désactivation`, changement de rôle) ;
	- lot 3 : ajouter l'espace `mon profil` pour consultation et modification des données autorisées par l'utilisateur lui-même ;
	- lot 4 : compléter la sécurité de compte (`changer le mot de passe`, `mot de passe oublié` ou procédure de réinitialisation adaptée au contexte d'hébergement, garde-fous de session) ;
	- lot 5 : aligner la documentation utilisateur et admin sur ces nouveaux parcours.
- **Séquence recommandée** : commencer par les rôles et l'administration, puis seulement ouvrir l'autonomie utilisateur et la récupération d'accès, car ces deux derniers points dépendent directement du modèle d'autorisation retenu.
- **Format attendu des livrables** :
	- une décision produit sur les rôles cibles ;
	- une matrice permissions par rôle et par écran ou action critique ;
	- les écrans et API d'administration correspondants ;
	- une procédure de récupération d'accès adaptée à un contexte associatif auto-hébergé ;
	- les tests et la documentation associés.
- **Point d'attention** : ce sujet touche à la sécurité et aux permissions ; toute simplification produit doit rester cohérente avec le modèle d'autorisation backend déjà en place.

### BL-023 — Revalider les droits réels par rôle et la visibilité des écrans comptables

- **Dates** : `created=2026-04-13`
- **Pourquoi** : le retest métier après fusion de `BL-022` fait apparaître des incohérences entre les droits attendus et ceux réellement observés : un profil `secrétaire` semble voir la comptabilité alors que ce n'était pas l'intention perçue, l'admin ne voit plus les règles comptables, le journal paraît vide, et plus personne ne voit le choix d'exercice.
- **Résultat attendu** : disposer d'une matrice d'autorisations vérifiée en conditions réelles, alignée avec la cible produit, et rétablir la visibilité attendue des écrans et du sélecteur d'exercice pour les bons profils.
- **Questions à trancher** :
	- qu'est-ce qu'un rôle `consultation` doit pouvoir voir exactement parmi journal, grand livre, balance, règles comptables et paramètres ;
	- le rôle `secrétaire` doit-il seulement gérer les flux métier (`contacts`, `factures`, `paiements`) ou aussi consulter une partie des écrans comptables ;
	- l'absence de règles comptables, de journal et de choix d'exercice vient-elle d'un problème d'autorisations, de navigation ou de filtrage par exercice courant.
- **Critère d'acceptation** : chaque rôle dispose d'un périmètre lisible, testé et conforme à la décision produit, l'admin retrouve les écrans comptables attendus, et le sélecteur d'exercice redevient visible et exploitable là où il doit l'être.
- **Point d'attention** : ce sujet dépend directement de `BL-022` mais mérite un ticket dédié car il combine arbitrage produit, contrôle des routes/menus et vérification des vues comptables.

### BL-024 — Clarifier la saisie des paiements et corriger les remises en banque automatiques

- **Dates** : `created=2026-04-13`
- **Pourquoi** : en usage réel, il n'est pas clair comment un paiement doit être saisi dans l'application, et les paiements de type `espèces` ou `virement` semblent être remis en banque automatiquement dès leur encodage, ce qui pose une question de justesse métier et comptable.
- **Résultat attendu** : définir un workflow cible simple pour la création, la consultation et l'éventuelle remise en banque des paiements, puis corriger l'application pour que chaque mode de paiement suive le bon traitement.
- **Questions à trancher** :
	- dans quel écran un utilisateur est-il censé encoder un paiement au quotidien ;
	- quels types de paiement doivent générer une remise en banque automatique, une remise manuelle ultérieure ou aucune remise ;
	- faut-il distinguer plus clairement `encaissement`, `dépôt bancaire`, `paiement fournisseur` et `mouvement de caisse` dans l'interface.
- **Critère d'acceptation** : un utilisateur comprend où saisir un paiement, le fait sans détour, et les écritures ou remises générées correspondent au comportement métier attendu pour chaque mode de règlement.
- **Point d'attention** : ce sujet touche à la fois l'UX des écrans `paiements`, la logique de banque/caisse et la génération des écritures comptables associées.

### BL-025 — Corriger le report à nouveau et les soldes du grand livre multi-exercices

- **Dates** : `created=2026-04-13`, `started=2026-04-13`, `completed=2026-04-13`
- **Pourquoi** : le grand livre du compte `512102` cumule au moins deux écritures d'ouverture d'exercice (`2024` et `2025`), ce qui fausse le solde affiché ; le problème est probablement plus large et remet en cause la justesse comptable des vues par compte.
- **Résultat attendu** : rétablir un calcul juste des soldes et des écritures d'ouverture dans le grand livre, en respectant une lecture strictement bornée à l'exercice choisi, sans option `tous les exercices` sur cette vue.
- **Décision produit actée** : le grand livre doit toujours afficher uniquement les transactions de l'exercice choisi ; il ne doit pas proposer `tous les exercices`, car cette agrégation rend ambigu le solde dès qu'un report à nouveau existe.
- **Questions à trancher** :
	- comment calculer le `solde d'ouverture` quand l'utilisateur borne en plus la vue avec une date de début à l'intérieur de l'exercice ;
	- le problème touche-t-il aussi le journal, la balance et d'autres comptes au-delà de `512102` ;
	- faut-il exposer séparément, plus tard, une vue d'historique brute multi-exercices distincte du grand livre.
- **Critère d'acceptation** : pour un exercice donné, le grand livre n'affiche que les écritures rattachées à cet exercice, y compris son report à nouveau éventuel, et présente un solde cohérent sans cumul indu entre ouvertures d'exercices successifs.
- **Point d'attention** : c'est un sujet comptable critique à traiter avant de faire confiance aux états ; il faudra le recouper avec `BL-010` et les choix de clôture des exercices historiques.

## Prêt

- Aucun sujet pour le moment.

## En cours

- **BL-021** — `created=2026-04-13`, `started=2026-04-13` — Les lots 1 à 3 du manuel utilisateur sont livrés, mais le lot 4 reste à réaliser pour finaliser la stabilisation éditoriale et l'enrichissement visuel.
- **BL-022** — `created=2026-04-13`, `started=2026-04-13` — Les lots 1 et 2 sont intégrés dans `develop` ; les lots suivants restent à traiter et le retest des droits réels est suivi dans `BL-023`.

## Fait

- **BL-001** — `created=2026-04-12`, `completed=2026-04-12` — Le backlog sert désormais de support de suivi versionné avec priorités, statuts et mises à jour explicites.
- **BL-002** — `created=2026-04-12`, `completed=2026-04-12` — La documentation utilisateur import/reset a été rédigée dans `doc/user/import-excel-et-reinitialisation.md`.
- **BL-003** — `created=2026-04-12`, `completed=2026-04-12` — La campagne de retest sur imports réels 2024/2025 a été rejouée sans écart bloquant.
- **BL-007** — `created=2026-04-12`, `completed=2026-04-13` — La convention est arrêtée pour le mode de travail actuel : `doc/backlog.md` reste la source de vérité, sans synchronisation systématique avec des issues GitHub à ce stade.
- **BL-009** — `created=2026-04-12`, `completed=2026-04-12` — Le plan comptable par défaut a été enrichi à partir des comptes réellement rencontrés dans les imports historiques.
- **BL-010** — `created=2026-04-12`, `completed=2026-04-12` — Une stratégie sûre de clôture administrative des exercices historiques importés a été définie et livrée.
- **BL-025** — `created=2026-04-13`, `started=2026-04-13`, `completed=2026-04-13` — Le grand livre est maintenant borné à l'exercice choisi, sans option multi-exercices, avec un solde d'ouverture cohérent quand la période démarre en cours d'exercice.
- **BL-011** — `created=2026-04-12`, `completed=2026-04-12` — L'exercice courant global et son sélecteur partagé ont été livrés sur les écrans comptables concernés.
- **BL-012** — `created=2026-04-12`, `completed=2026-04-12` — La liste des paiements affiche la référence métier et permet l'édition directe.
- **BL-013** — `created=2026-04-12`, `completed=2026-04-12` — Le journal de caisse propose désormais référence, détail et édition directe.
- **BL-014** — `created=2026-04-12`, `completed=2026-04-12` — Le journal comptable est enrichi pour la lecture métier, le détail et la navigation vers les factures.
||||||| parent of 8704648 (feat(import): improve replay and accounting workflows)
=======
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
>>>>>>> 8704648 (feat(import): improve replay and accounting workflows)
