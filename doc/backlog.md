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

1. **BL-023** — revalider les droits réels par rôle et la visibilité des écrans comptables.
2. **BL-024** — clarifier le workflow de saisie des paiements et corriger les remises en banque automatiques.
3. **BL-008** — fiabiliser l'import Excel comme outil de validation itérative de convergence.

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
| BL-023 | 2026-04-13 | Correction | Permissions / Comptabilité | P1 | Clarifier d'abord la cible produit des rôles, puis corriger les droits réels et les incohérences de visibilité du shell comptable (écrans, sélecteur d'exercice, zone utilisateur) |
| BL-024 | 2026-04-13 | Correction | Paiements / Banque | P1 | Clarifier le workflow cible de saisie des paiements et corriger l'automatisme qui remet en banque les paiements `espèces` et `virement` dès leur encodage |

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
- **Pourquoi** : le retest métier après fusion de `BL-022` montre d'abord un problème de définition cible des rôles, puis des incohérences concrètes entre le comportement attendu et le comportement observé. Avant d'implémenter un changement de permissions, il faut clarifier le périmètre produit réel de chaque rôle. Côté symptômes observés, le rôle `secrétaire` semble voir une partie de la comptabilité, la visibilité de certains écrans comptables reste ambiguë selon le profil, et la zone utilisateur du shell (nom d'utilisateur et bouton de déconnexion en bas à gauche) disparaît parfois.
- **Résultat attendu** : disposer d'une matrice d'autorisations explicitement validée côté produit, puis d'un comportement vérifié en conditions réelles pour chaque rôle, avec une visibilité cohérente des écrans comptables, du sélecteur d'exercice et de la zone utilisateur du shell.
- **Précondition** : ne pas corriger les permissions au fil de l'eau sans arbitrage préalable sur la cible produit des rôles ; la discussion de cadrage fait partie du ticket.
- **Questions à trancher** :
	- qu'est-ce qu'un rôle `consultation` doit pouvoir voir exactement parmi journal, grand livre, balance, règles comptables et paramètres ;
	- le rôle `secrétaire` doit-il seulement gérer les flux métier (`contacts`, `factures`, `paiements`) ou aussi consulter une partie des écrans comptables ;
	- faut-il revoir plus largement les rôles actuels (`readonly`, `secretaire`, `tresorier`, `admin`) parce qu'ils ne correspondent pas clairement aux usages métier attendus ;
	- les incohérences observées relèvent-elles d'un problème d'autorisations backend, de menus frontend, de filtrage par exercice courant, ou d'un défaut d'affichage/rendu de la zone utilisateur dans le shell.
- **Critère d'acceptation** : chaque rôle dispose d'un périmètre lisible, testé et conforme à la décision produit, les écrans comptables et le sélecteur d'exercice sont visibles uniquement pour les bons profils, et le nom d'utilisateur ainsi que le bouton de déconnexion restent affichés de façon stable quand la zone utilisateur doit être présente.
- **Point d'attention** : ce sujet dépend directement de `BL-022` mais mérite un ticket dédié car il combine arbitrage produit, contrôle des routes/menus, vérification des vues comptables et correction d'un symptôme intermittent de shell lié à l'utilisateur courant.

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
