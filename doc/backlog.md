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

1. Ajouter chaque nouveau sujet dans le **Récapitulatif des sujets ouverts** avec une formulation courte et concrète.
2. Proposer une **priorité** (`P1`, `P2`, `P3`) avant arbitrage.
3. Passer un sujet en **Prêt** une fois le besoin clarifié.
4. Déplacer en **En cours** quand le travail démarre sur une branche active.
5. Déplacer en **Fait** quand l'implémentation est livrée et considérée comme terminée côté backlog.
6. Suivre les dates avec le format ISO (`YYYY-MM-DD`) : `created`, `started`, `completed`.
7. Ne pas laisser de suite actionnable uniquement dans la conversation si elle doit être retrouvée plus tard.
8. Dans chaque section qui liste des tickets, y compris le récapitulatif des sujets ouverts, conserver l'ordre numérique croissant des identifiants `BL-xxx`.

### Signification des priorités

- `P1` — important à discuter rapidement ; fort impact métier, besoin opérationnel ou risque notable.
- `P2` — utile mais non bloquant ; amélioration à programmer.
- `P3` — confort, finition ou dette technique optionnelle.

### Signification des statuts

- `Bac d'entrée` — besoin capturé, pas encore arbitré.
- `Prêt` — besoin clarifié, prêt à être pris.
- `En cours` — sujet en cours d'implémentation sur une branche active.
- `Fait` — sujet livré et prêt à être fusionné ou déjà intégré.
- Dans ce document, un sujet encore au statut `Bac d'entrée` apparaît uniquement dans le récapitulatif des sujets ouverts, sans entrée dédiée dans `Prêt`, `En cours` ou `Fait`.

### Champs de dates

- `created` — date d'entrée initiale dans le backlog.
- `started` — date de démarrage effectif sur une branche.
- `completed` — date à laquelle le sujet est considéré comme livré côté backlog.
- Toujours utiliser le format ISO `YYYY-MM-DD`.
- Dans `Détail des sujets`, ajouter systématiquement une ligne `Dates` avec uniquement les champs connus pour le statut courant.
- Pour un sujet historique déjà traité avant structuration complète du backlog, approximer `created` à partir de la première trace utile disponible dans l'historique récent du dépôt.

## Priorités proposées pour la prochaine discussion

1. **BL-024** — clarifier le workflow de saisie des paiements et corriger les remises en banque automatiques.
2. **BL-022** — terminer les lots restants sur la gestion des utilisateurs, profils et sécurité de compte.
3. **BL-021** — finaliser le manuel utilisateur illustré avec stabilisation éditoriale et enrichissement visuel.

## Récapitulatif des sujets ouverts

| ID | Créé le | Type | Zone | Priorité proposée | Sujet |
|---|---|---|---|---|---|
| BL-004 | 2026-04-12 | Amélioration | Import Excel / Support | P2 | Afficher un historique d'import exploitable dans l'UI avec type, date, compteurs, diagnostics, et une traçabilité suffisamment fine des objets créés |
| BL-006 | 2026-04-12 | Technique | API / Framework | P3 | Traiter les warnings de dépréciation `HTTP_422_UNPROCESSABLE_ENTITY` remontés par la suite de tests |
| BL-015 | 2026-04-13 | Amélioration | Import Excel / Outillage | P2 | Ajouter un reset sélectif orienté reprise pour rejouer proprement un import par filière ou période sans repartir systématiquement d'un effacement global |
| BL-019 | 2026-04-13 | Documentation | Projet / Exploitation | P1 | Refaire le README et la documentation technique d'installation, mise à jour, pile techno, configuration et exploitation Docker |
| BL-020 | 2026-04-13 | Documentation | Développement | P3 | Documenter clairement comment participer au projet : prérequis, environnement local, commandes utiles, qualité attendue et workflow PR |
| BL-021 | 2026-04-13 | Documentation | Utilisateur / Parcours | P1 | Rédiger un manuel utilisateur illustré et pas à pas aligné sur les écrans réellement disponibles |
| BL-022 | 2026-04-13 | Évolution | Utilisateurs / Sécurité | P1 | Renforcer la gestion des utilisateurs avec des rôles métier plus clairs, la création et l'administration des comptes, l'autonomie sur le profil et un socle de sécurité de compte plus complet |
| BL-024 | 2026-04-13 | Correction | Paiements / Banque | P1 | Clarifier le workflow cible de saisie des paiements et corriger l'automatisme qui remet en banque les paiements `espèces` et `virement` dès leur encodage |
| BL-030 | 2026-04-16 | Décision | Métier / Edition des données | P1 | Définir une politique explicite de modification des objets métier déjà créés ou validés (factures, paiements, achats, etc.) avec règles de recalcul, traçabilité et limites selon le statut |

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

- **Dates** : `created=2026-04-12`, `started=2026-04-19`, `completed=2026-04-19`
- **Pourquoi** : l'import historique a désormais des garde-fous solides, mais la politique cible n'est pas encore entièrement tranchée quand des écritures manuelles, des écritures auto-générées ou des doublons métier proches coexistent déjà en base.
- **Résultat attendu** : une politique explicite, documentée et testée qui dit pour chaque cas de coexistence ce qui doit être bloqué, toléré, ignoré comme doublon ou remonté pour revue manuelle avant d'ouvrir davantage l'import `Comptabilite` en réel.
- **Résultat livré** : la politique de coexistence actuellement implémentée est maintenant explicitée dans `doc/dev/bl-005-politique-coexistence-imports.md` et traduite dans le code et les tests avec trois diagnostics distincts pour les imports `Comptabilite` : `entry-existing` pour le doublon exact, `entry-covered-by-solde` pour une ligne déjà couverte par Solde, et `entry-near-manual` pour une proximité non bloquante avec une écriture `MANUAL` existante.
- **Critère d'acceptation** : à lecture de la preview, un utilisateur doit comprendre sans ambiguïté pourquoi un cas coexistence est bloqué, toléré ou seulement signalé, et la même décision doit être respectée à l'import réel.
- **Livré parce que** : la PR `#20` a été mergée dans `develop` le `2026-04-19` après validation backend/frontend complète, avec documentation dédiée, diagnostics structurés et couverture de tests associée.

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

- **Dates** : `created=2026-04-12`, `started=2026-04-18`, `completed=2026-04-18`
- **Pourquoi** : l'import Excel ne doit pas seulement servir à la reprise initiale 2024/2025 ; il doit aussi devenir un garde-fou qualité pendant la période de double tenue Excel + Solde.
- **Phase 1** : initialiser proprement Solde à partir des fichiers historiques existants.
- **Phase 2** : réimporter régulièrement Excel pour vérifier que les écritures et mouvements saisis dans Solde correspondent exactement à la réalité comptable de référence.
- **Résultat attendu** : détecter toute écriture manquante, en trop ou divergente, avec un haut niveau d'exigence sur montants, dates, libellés et équilibres, et une politique claire sur ce qui reste bloquant versus seulement signalé.
- **Objectif métier clarifié au 2026-04-18** : après un import initial, vérifier que ce qui est ensuite généré dans Solde et ce qui continue à être saisi dans Excel restent cohérents sur les invariants métier essentiels, plutôt que d'exiger une identité aveugle ligne à ligne sur tout l'historique ou d'attendre qu'un seul fichier Excel recouvre à lui seul tout ce qui existe dans Solde.
- **Invariants métier à contrôler** :
	- les factures clientes sont cohérentes dans les deux sens, mais sur des périmètres différents : côté `Solde -> Excel`, seules les factures appartenant à la vraie période/exercice du fichier doivent être attendues dans Excel ; côté `Excel -> Solde`, toutes les factures encore présentes dans Excel, même anciennes car non soldées, doivent exister aussi dans Solde ;
	- les soldes des comptes de trésorerie sont cohérents entre Solde et Excel (`Banque`, `Caisse`, remises/chèques à déposer) ;
	- les soldes comptables des comptes structurants sont identiques entre Solde et Excel (`clients`, `fournisseurs`, `banque`, `caisse`, `chèques à déposer`, autres comptes pivots de rapprochement), sans exiger que le détail des écritures soit identique ligne à ligne si les deux systèmes modélisent différemment une même opération ;
	- les paiements/règlements sont cohérents avec les factures ouvertes et soldées : pas de facture marquée payée d'un côté et impayée de l'autre, pas de règlement orphelin ou dupliqué ;
	- les comparaisons métier qui dépendent d'écritures dérivées doivent être raisonnées sur l'ensemble `Gestion + Comptabilite`, et non sur un seul fichier pris isolément, en particulier quand `Comptabilite` porte des ventilations ou des splits absents de `Gestion` ;
	- les écarts acceptables doivent être explicitement normalisés par politique métier (différences de granularité, projections fournisseur, écritures d'ouverture, reports historiques encore ouverts), et tout le reste doit ressortir comme divergence réelle ;
	- la cible finale n'est pas l'absence totale d'écart brut, mais le fait que tous les écarts restants soient prévisibles, explicables et progressivement réduits à mesure que les règles métier de comparaison sont enrichies.
- **Décisions de cadrage issues de `BL-026`** :
	- prévoir deux modes de comparaison distincts : `convergence globale` pour comparer l'état final Excel et l'état final Solde, y compris les écritures d'ouverture et les écritures importées depuis `Comptabilite`, et `validation du moteur Gestion` pour comparer seulement les écritures générées par `Gestion` avec les écritures Excel correspondant aux mêmes événements métier ;
	- ne pas imposer une identité ligne à ligne comme unique cible : certaines différences de structure doivent être rapprochées par des règles métier explicites ;
	- pour les fournisseurs, considérer comme cas normalisable le fait qu'Excel porte souvent un paiement direct (`charge -> banque/caisse`) alors que Solde modélise `facture fournisseur -> règlement` ;
	- pour les factures clients mixtes de type `cs+a`, considérer au contraire que la ventilation multi-comptes observée dans Excel exprime une réalité comptable cible et non un simple artefact de rapprochement ;
	- sur les salaires, ne pas ouvrir de sujet correctif tant qu'aucun écart métier de montant n'est démontré ; au besoin, formaliser seulement une convention de date et de regroupement pour la comparaison.
	- pour les factures clients, la comparaison `Solde -> Excel` ne doit pas prendre comme borne la première ou la dernière facture visible dans le classeur, car `Gestion 2025` peut conserver quelques factures beaucoup plus anciennes encore impayées ; le périmètre des `extra_in_solde` doit être borné par la vraie plage de l'exercice du fichier, tandis que la comparaison inverse `Excel -> Solde` doit continuer à vérifier toutes les factures effectivement présentes dans le classeur, y compris les anciennes restées ouvertes ; la même asymétrie de périmètre devra être confirmée ou non pour les autres domaines (`Paiements`, `Caisse`, `Banque`).
	- pour rendre cette règle opérationnelle sur `Factures`, un fichier nommé `Gestion YYYY` doit être interprété comme l'exercice démarrant au mois `fiscal_year_start_month` de l'année `YYYY` et se terminant la veille du même mois l'année suivante ; si le nom du fichier ne permet pas de déduire l'exercice, la comparaison peut retomber provisoirement sur les dates visibles dans le classeur.
	- pour `Paiements / règlements`, la comparaison bidirectionnelle doit suivre la même fenêtre d'exercice `Gestion YYYY` pour le périmètre temporel principal, y compris quand cet exercice déborde sur l'année civile suivante ; le contrôle complémentaire des paiements rattachés à des factures anciennes encore ouvertes reste un sujet distinct.
	- pour `Banque`, le sens `Solde -> Excel` doit suivre la plage réelle couverte par le relevé visible dans le classeur, et cette plage peut recouvrir plusieurs années civiles même si aucune ligne n'existe dans l'une d'elles ; les `extra_in_solde` doivent donc être cherchés sur toute la fenêtre de dates, pas seulement sur les années explicitement présentes dans les lignes du fichier.
	- pour `Caisse`, le sens `Solde -> Excel` doit suivre la plage réelle couverte par le registre visible dans le classeur, avec la même vigilance que pour `Banque` sur les années intermédiaires absentes des lignes affichées ; les `extra_in_solde` doivent être cherchés sur toute la fenêtre de dates, en excluant toujours le solde d'ouverture système.
- **Grille de contrôle cible par domaine** :
	- `Factures` :
	  - **Source de vérité** : `Gestion` pour la présence des pièces ouvertes/soldées ; `Comptabilite` pour les ventilations dérivées quand une facture `cs+a` ou une règle de projection produit plusieurs lignes comptables.
	  - **Sens de comparaison** : `Excel -> Solde` sur toutes les factures encore visibles dans le fichier ; `Solde -> Excel` seulement sur la vraie période/exercice du fichier.
	  - **Invariants à vérifier** : existence des factures, montant total, statut métier (`ouverte`, `partielle`, `soldée`), reste dû, rattachement au bon contact.
	  - **Écarts acceptables** : factures historiques encore ouvertes hors période d'exercice ; différences de ventilation comptable si le total et le reste dû restent cohérents.
	- `Paiements / règlements` :
	  - **Source de vérité** : `Gestion` pour les paiements clients et les règlements simples ; `Gestion + Compta` quand la contrepartie comptable doit être reconstituée.
	  - **Sens de comparaison** : bidirectionnel sur la période du fichier, avec contrôle complémentaire des paiements rattachés à des factures encore ouvertes dans Excel.
	  - **Invariants à vérifier** : pas de règlement orphelin, pas de doublon significatif, même facture soldée/non soldée des deux côtés, mêmes montants encaissés/décaisés par pièce.
	  - **Écarts acceptables** : différences de granularité technique tant que le total réglé par facture et le statut de solde restent identiques.
	- `Banque` :
	  - **Source de vérité** : `Gestion` pour les mouvements bancaires importés ; `Comptabilite` pour vérifier les soldes de comptes et les projections induites.
	  - **Sens de comparaison** : `Excel -> Solde` sur tous les mouvements du fichier ; `Solde -> Excel` borné à la période du relevé/exercice contrôlé.
	  - **Invariants à vérifier** : même solde bancaire final, mêmes mouvements significatifs non rapprochés, mêmes remises/chèques en transit.
	  - **Écarts acceptables** : lignes descriptives de solde, écritures d'ouverture, regroupements techniques explicitement normalisés.
	- `Caisse` :
	  - **Source de vérité** : `Gestion` pour les mouvements de caisse ; `Comptabilite` pour la cohérence du compte de caisse et des projections associées.
	  - **Sens de comparaison** : bidirectionnel sur la période du fichier, avec borne métier d'exercice et exclusion explicite du solde d'ouverture système.
	  - **Invariants à vérifier** : même solde de caisse, mêmes entrées/sorties significatives, pas d'écart inexpliqué sur les remises d'espèces ou les décaissements fournisseurs.
	  - **Écarts acceptables** : solde initial, prévisions de remise d'espèces ou regroupements normalisés par politique métier.
	- `Comptabilité / comptes pivots` :
	  - **Source de vérité** : `Comptabilite` pour les écritures de référence ; `Gestion` sert d'entrée métier mais ne suffit pas à lui seul pour comparer les écritures dérivées.
	  - **Sens de comparaison** : comparaison des soldes et des groupes d'écritures sur la période, pas identité brute ligne à ligne si les deux systèmes modélisent différemment la même opération.
	  - **Invariants à vérifier** : mêmes soldes sur les comptes structurants (`clients`, `fournisseurs`, `banque`, `caisse`, `chèques à déposer`, autres comptes de rapprochement), mêmes équilibres par groupe métier important.
	  - **Écarts acceptables** : une opération détaillée en `2` écritures dans Excel et `4` dans Solde si le résultat comptable final, les soldes et le sens des comptes restent identiques.
	- `Écarts résiduels` :
	  - **Objectif** : tout écart restant doit être classé comme `attendu et expliqué par une règle métier`, `toléré mais à surveiller`, ou `anomalie réelle`.
	  - **Critère de maturité BL-008** : les écarts non expliqués doivent tendre vers zéro, et chaque nouvelle passe de recette doit enrichir les règles de comparaison pour rendre les écarts restants prévisibles et compréhensibles.
- **Premier lot visé** :
	- formaliser ces deux modes de validation (`convergence globale` et `validation du moteur Gestion`) et leurs périmètres respectifs ;
	- formaliser un contrat de comparaison par domaine (`Factures`, `Paiements`, `Caisse`, `Banque`, `Journal`) ;
	- ajouter un mode de comparaison sans écriture, probablement adossé à la preview existante ;
	- catégoriser les écarts avec des codes stables (`missing-in-solde`, `extra-in-solde`, `amount-mismatch`, `date-mismatch`, `ambiguous-match`, `ignored-by-policy`, `blocked-by-coexistence`) ;
	- porter explicitement des règles de projection ou de normalisation pour les cas attendus (`facture fournisseur + règlement` côté Solde vs paiement direct côté Excel, ouvertures d'exercice, autres écarts de granularité assumés) ;
	- produire un rapport exploitable avec résumé global, détail par feuille et exemples d'écarts ;
	- cibler d'abord la chaîne réelle `Gestion 2024` / `Gestion 2025` avant toute généralisation plus large.
- **Critère d'acceptation** : on doit pouvoir répondre, sans rien persister, à quatre questions simples pour chacun des deux modes : qu'est-ce qui manque dans Solde, qu'est-ce qui est en trop, qu'est-ce qui diverge, et qu'est-ce qui est ignoré volontairement selon la politique métier.
- **Hors périmètre initial** : pas de correction automatique des écarts, pas d'ouverture large de l'import `Comptabilite` en réel tant que `BL-005` n'est pas tranché, et pas d'outil générique de réconciliation déconnecté du cas de reprise réel.
- **Enjeu** : sujet critique pour la confiance métier pendant toute la transition hors Excel.
- **Résultat livré au 2026-04-18** : les deux premiers lots prévus sont désormais intégrés dans `develop` dans la preview sans écriture : `Gestion` expose le delta `Excel -> Solde` avec le sens inverse `extra_in_solde`, `Comptabilite` expose un mode `convergence globale` bidirectionnel, et une recette locale rejouable est désormais documentée dans `doc/dev/bl-008-recette-convergence.md` via `scripts/run_excel_convergence_preview.py`.

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

- **Dates** : `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14`
- **Pourquoi** : malgré la forte couverture i18n actuelle, il reste encore des libellés incohérents, des formulations hétérogènes et potentiellement quelques textes en dur qui dégradent la perception de qualité.
- **Résultat attendu** : auditer puis corriger les libellés visibles pour que les écrans utilisent des clés i18n cohérentes, un vocabulaire homogène et une microcopie claire du login jusqu'aux vues métier.
- **Livré parce que** : les écrans `Banque`, `Caisse` et `Salaires` utilisent maintenant des clés i18n cohérentes pour les compteurs, états vides et libellés visibles auparavant hétérogènes ou codés en dur.
- **Point d'attention** : viser d'abord les incohérences utilisateur visibles ; éviter de renommer massivement des clés stables si le gain produit est faible.

### BL-017 — Formats de dates et périodes en français

- **Dates** : `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14`
- **Pourquoi** : certaines dates ou périodes restent affichées dans un format trop technique ou ambigu, parfois plus proche d'une lecture ISO ou américaine que d'un usage métier français.
- **Résultat attendu** : uniformiser l'affichage des dates, mois et périodes au format français dans les tableaux, détails, dialogues et exports lisibles, tout en conservant les formats ISO pour les API et les échanges techniques.
- **Livré parce que** : un helper partagé formate désormais les mois en français et il est appliqué sur `Salaires` et le tableau mensuel du `Dashboard`, tout en conservant les formats ISO pour les filtres techniques et les appels API.
- **Point d'attention** : distinguer clairement stockage/échange et présentation UI pour éviter les régressions côté backend ou formulaires.

### BL-018 — Lisibilité des écrans de liste : tri, filtre et états de vue

- **Dates** : `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14`
- **Pourquoi** : plusieurs écrans disposent déjà d'un filtre générique ou d'améliorations visuelles, mais l'expérience reste inégale selon les vues pour le tri, la lisibilité des colonnes, les états vides, le chargement et la compréhension du périmètre affiché.
- **Résultat attendu** : définir puis appliquer un socle UX commun pour les écrans de liste afin que recherche, tri, colonnes utiles, états vides, compteurs et chargement soient plus clairs et cohérents d'un écran à l'autre.
- **Livré parce que** : un socle DataTable partagé a été introduit pour les filtres texte, dates, intervalles numériques et multi-sélection, avec compteurs d'état harmonisés, tri/filtrage cohérents sur les principales vues de liste, prise en charge des saisies de date FR/ISO dans les filtres et retrait explicite du tri/filtrage sur les tableaux fixes `bilan` et `résultat`.
- **Point d'attention** : éviter l'uniformisation aveugle ; certaines vues métier auront toujours besoin d'adaptations spécifiques.

### BL-019 — README et documentation technique d'exploitation

- **Dates** : `created=2026-04-13`
- **Pourquoi** : la documentation projet existe mais reste encore trop dispersée ou trop implicite pour quelqu'un qui doit installer, mettre à jour ou exploiter Solde sans relire tout le dépôt.
- **Résultat attendu** : un README plus clair et une documentation technique structurée couvrant au minimum l'installation, la mise à jour, la pile technologique, la configuration, Docker, les volumes de données, les sauvegardes et les points d'exploitation courants.
- **État actuel** : le `README.md` couvre déjà le démarrage Docker/local, les variables d'environnement, la structure du dépôt et les liens de documentation ; il manque encore la documentation d'exploitation structurée attendue sur la mise à jour, les volumes de données, les sauvegardes et les opérations courantes.
- **Priorisation proposée** : lot rapide et structurant ; c'est le meilleur point d'entrée documentation à livrer vite car il clarifie aussi le cadre pour les docs plus détaillées.
- **Séquence recommandée** : commencer par clarifier le README, puis extraire les détails longs vers une doc technique dédiée plutôt que tout entasser en page d'accueil.
- **Point d'attention** : distinguer ce qui relève du guide d'exploitation réel de ce qui relève des détails purement développeur, pour éviter un README surchargé.

### BL-020 — Documentation de développement et contribution

- **Dates** : `created=2026-04-13`
- **Pourquoi** : contribuer efficacement au projet suppose aujourd'hui de reconstituer les prérequis et les conventions depuis plusieurs fichiers, ce qui freine la reprise de contexte et la qualité des contributions.
- **Résultat attendu** : une documentation développeur claire expliquant les prérequis, la mise en route locale, les commandes de build/test/lint, la qualité attendue, l'organisation du dépôt, le workflow de contribution et les attentes avant PR.
- **État actuel** : le `README.md` fournit déjà une mise en route locale minimale et les commandes de base, et `doc/dev/gestion-utilisateurs-et-permissions.md` documente un sous-ensemble fonctionnel utile ; il manque encore une documentation développeur centrale sur le workflow de contribution, les commandes qualité réellement utilisées et les attentes avant PR.
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

- **Dates** : `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14`
- **Pourquoi** : le retest métier après fusion de `BL-022` montre d'abord un problème de définition cible des rôles, puis des incohérences concrètes entre le comportement attendu et le comportement observé. Avant d'implémenter un changement de permissions, il faut clarifier le périmètre produit réel de chaque rôle. Côté symptômes observés, le rôle `secrétaire` semble voir une partie de la comptabilité, la visibilité de certains écrans comptables reste ambiguë selon le profil, et la zone utilisateur du shell (nom d'utilisateur et bouton de déconnexion en bas à gauche) disparaît parfois.
- **Résultat attendu** : disposer d'une matrice d'autorisations explicitement validée côté produit, puis d'un comportement vérifié en conditions réelles pour chaque rôle, avec une visibilité cohérente des écrans comptables, du sélecteur d'exercice et de la zone utilisateur du shell.
- **Précondition** : ne pas corriger les permissions au fil de l'eau sans arbitrage préalable sur la cible produit des rôles ; la discussion de cadrage fait partie du ticket.
- **Avancement actuel** : le cadrage initial a été formalisé dans `doc/dev/bl-023-cadrage-roles-et-matrice-acces.md`, puis la cible produit a été validée et implémentée : séparation visible `Gestion` / `Comptabilité` dans la navigation, nouveaux guards frontend par domaine, renommage métier `Gestionnaire` / `Comptable`, masquage du rôle `readonly` dans les options usuelles d'administration, alignement des permissions backend sur la matrice cible et ajout de tests ciblés sur les rôles.
- **Résultat livré** : la matrice produit validée est maintenant appliquée dans le code. La partie `Gestion` est accessible à `Gestionnaire`, `Comptable` et `Administrateur`, la partie `Comptabilité` est réservée à `Comptable` et `Administrateur`, la navigation est séparée visuellement par section, le sélecteur d'exercice reste disponible pour les profils métier qui consultent des écrans filtrés par exercice, et la zone utilisateur du shell reste visible avec un libellé stable sans être repoussée en bas par la hauteur des vues.
- **Point d'attention** : le rôle technique `readonly` reste présent pour compatibilité, mais n'est plus proposé comme rôle produit normal dans l'interface d'administration. Une éventuelle suppression complète ou migration explicite reste un sujet distinct.

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

### BL-026 — Valider les imports Excel par rapprochement chiffré sur 2024 et 2025

- **Dates** : `created=2026-04-15`, `started=2026-04-15`, `completed=2026-04-16`
- **Pourquoi** : après la fiabilisation de la mécanique d'import, il faut maintenant confirmer sur le cas réel que les données visibles dans Solde correspondent bien aux fichiers Excel sources, aussi bien côté `Gestion` que côté `Comptabilité`, et cela sur les deux exercices historiques.
- **Résultat attendu** : disposer d'une validation explicite, exercice par exercice, des chiffres importés dans Solde par rapport aux fichiers Excel `2024` et `2025`, avec une liste claire des écarts constatés ou la confirmation qu'il n'y en a pas.
- **Résultat livré** : le cadrage de recette a été formalisé dans `doc/dev/bl-026-cadrage-validation-imports-excel.md` et un constat exploitable a été produit dans `doc/dev/bl-026-constat-validation-imports.md` pour l'exercice `2024`, avec distinction entre chiffres conformes, écarts justifiés de modélisation et sujets à corriger. Le ticket est clos comme ticket de constat et d'orientation ; la poursuite de la validation comptable stricte est désormais renvoyée vers `BL-008`, et l'alignement du comportement comptable attendu sur les factures clients mixtes vers `BL-029`.
- **Périmètre minimal** :
	- comparer les chiffres de `Gestion` visibles dans l'application avec ceux des fichiers Excel correspondants pour `2024` et `2025` ;
	- comparer les chiffres de `Comptabilité` visibles dans l'application avec ceux des fichiers Excel correspondants pour `2024` et `2025` ;
	- expliciter la méthode de rapprochement retenue par écran ou par état (totaux, comptes, journaux, soldes, volumes) ;
	- consigner tout écart résiduel avec un diagnostic exploitable pour décider s'il s'agit d'un bug, d'un problème de données source ou d'un écart de lecture métier.
- **Critère d'acceptation** : pour chacun des deux exercices, on peut produire un constat de validation lisible indiquant ce qui a été comparé, quels chiffres concordent entre Excel et Solde, et quels écarts restent ouverts le cas échéant.
- **Point d'attention** : ce ticket est complémentaire de `BL-008` ; la clôture de `BL-026` ne signifie pas que la convergence comptable Excel/Solde est entièrement démontrée, mais que les écarts restants ont été suffisamment qualifiés pour être repris dans des tickets plus ciblés.

### BL-027 — Gérer une ouverture du système explicite pour Banque et Caisse

- **Dates** : `created=2026-04-15`, `started=2026-04-15`, `completed=2026-04-16`
- **Pourquoi** : pendant la validation `BL-026`, il apparaît que le premier exercice importé a besoin d'un point de départ explicite côté gestion pour `Banque` et `Caisse`, distinct de l'ouverture comptable de l'exercice. Aujourd'hui, les lignes Excel de `solde initial` sont traitées comme des lignes ignorées, ce qui ne permet pas de représenter proprement l'état hérité du système avant le premier exercice suivi.
- **Résultat attendu** : définir puis implémenter une notion d'`ouverture du système` pour `Banque` et `Caisse`, injectée une seule fois sur le plus ancien exercice importé, contribuant aux soldes cumulés, et identifiée visiblement comme donnée spéciale dans l'interface (badge, type ou rendu distinct).
- **Résultat livré** : une ouverture du système dédiée peut être configurée côté paramètres pour la `Banque` et la `Caisse`, avec une date par défaut calée sur le plus ancien exercice ; ces écritures sont stockées avec une source explicite `system_opening`, intégrées aux soldes, affichées distinctement dans les vues de trésorerie, et exclues des comparaisons d'import pour éviter les doublons ; le constat `BL-026` confirme ensuite le comportement attendu sur les chiffres visibles.
- **Périmètre initial** :
	- gérer explicitement un solde d'ouverture `Banque` sur le premier exercice importé ;
	- gérer explicitement un solde d'ouverture `Caisse` sur le premier exercice importé ;
	- rendre ces lignes distinguables des mouvements normaux dans les écrans de trésorerie ;
	- éviter toute réinjection automatique du même concept sur les exercices suivants.
- **Critère d'acceptation** : après import du plus ancien exercice, les écrans `Banque` et `Caisse` affichent un point de départ cohérent et identifié comme `ouverture du système`, les soldes des exercices suivants héritent correctement de ce point de départ sans doublon, et les chiffres `BL-026` peuvent être remesurés proprement pour la trésorerie.
- **Livré parce que** : le commit `1faa72a` du `2026-04-15` introduit l'ouverture du système et sa gestion d'import, puis le constat `BL-026` du `2026-04-16` documente explicitement son application sur `Banque` et `Caisse`.

### BL-029 — Saisie des factures clients pilotée par types de lignes

- **Dates** : `created=2026-04-16`, `started=2026-04-16`, `completed=2026-04-19`
- **Pourquoi** : le modèle actuel demande encore un label global de facture (`cs`, `a`, `cs+a`, `general`) alors que le besoin métier cible est plus fin : l'utilisateur pense d'abord en lignes de facture, chacune portant un type métier (`cours`, `adhésion`, `autres`), puis attend que Solde calcule le total et la ventilation comptable à partir de cette saisie ; les remises doivent rester visibles sur la facture mais être portées par des lignes négatives du même type métier, pas par une catégorie séparée. Le sous-sujet exploré auparavant comme `BL-028` est absorbé ici, car il n'est pas testable isolément sur `Gestion 2024` faute de détail source exploitable pour des factures mixtes.
- **Résultat attendu** : une création de facture client où l'utilisateur saisit le client et les lignes, choisit un type par ligne, voit le total calculé automatiquement, et obtient à validation des écritures comptables dérivées de la composition réelle de la facture sans dépendre d'un label global saisi à la main.
- **Règle métier cible actuellement privilégiée** :
	- les seuls types de lignes métier exposés sont `cours`, `adhésion` et `autres` ;
	- une remise est saisie comme une seconde ligne négative du même type métier que la ligne remisée ;
	- le client voit toutes les lignes, y compris la remise, mais la ventilation comptable travaille sur le net agrégé par type métier ;
	- une facture ne doit jamais aboutir à un total négatif.
- **Conséquence de cadrage** :
	- on ne garde plus de ticket autonome pour une ventilation `cs+a` dépendant d'un détail explicite dans `Gestion 2024` ;
	- le travail utile déjà engagé sur la ventilation à partir des lignes de facture est poursuivi directement dans `BL-029` ;
	- la logique future d'enrichissement a posteriori depuis `Comptabilité` reste traitée séparément dans `BL-030`.
- **Comportement d'import cible** :
	- import `Gestion` : si le libellé indique `cs`, créer une ligne `cours` ; s'il indique `a`, créer une ligne `adhésion` ; sinon créer une ligne `autres` ;
	- import `Gestion` : ne pas inventer de remise ni de ventilation détaillée absente de la source ;
	- import `Comptabilité` : quand une facture déjà présente porte une ligne `autres`, autoriser un enrichissement ou une clarification automatique de cette ligne si les comptes produits utilisés dans les écritures permettent une déduction sûre ;
	- en cas de rapprochement ambigu entre `Gestion` et `Comptabilité`, ne rien réécrire silencieusement.
- **Questions à trancher** :
	- faut-il supprimer complètement le label global utilisateur au profit d'un calcul depuis les lignes ;
	- comment modéliser les lignes `autres` côté comptable ;
	- jusqu'où autoriser l'import `Comptabilité` à requalifier automatiquement une ligne `autres` ;
	- quelle traçabilité garder entre ligne créée depuis `Gestion`, ligne enrichie via `Comptabilité` et ligne corrigée manuellement ;
	- quelle règle appliquer si une facture mélange `cours`, `adhésion` et `autres`, avec ou sans lignes négatives de remise.
- **Critère d'acceptation** : un utilisateur peut créer une facture client complète sans se poser de question sur le label comptable global ; le total affiché correspond exactement aux lignes saisies et les écritures générées à validation reflètent cette décomposition ligne par ligne.
- **Point d'attention** : l'import `Comptabilité` deviendrait alors non seulement un import d'écritures, mais aussi un mécanisme d'enrichissement métier des factures déjà créées ; il faudra l'encadrer par des règles de sûreté et de coexistence explicites.
- **Résultat livré** : l'implémentation a été fusionnée dans `develop` via le merge de la PR `#18`, puis la recette métier utilisateur a été confirmée sur les scénarios prévus ; la saisie par lignes typées sert désormais de source de vérité pour le total, le libellé dérivé et la ventilation comptable des factures clientes.
- **Implémenté dans ce lot** :
	- ajout d'un type de ligne de facture client (`cours`, `adhésion`, `autres`) en base, API et logique métier ;
	- calcul du total, du label dérivé et de la ventilation comptable directement à partir des lignes, avec support des remises via lignes négatives ;
	- import `Gestion` revu pour créer systématiquement des lignes typées sans inventer de détail absent ;
	- import `Comptabilité` revu pour clarifier de façon sûre une facture mixte existante quand les écritures permettent d'en déduire la ventilation ;
	- formulaire frontend de facture client revu pour supprimer la saisie du label global et piloter la facture par types de lignes ;
	- migration Alembic, tests backend/frontend et backlog mis à jour.
- **Validation technique réalisée** : la suite `pytest tests/`, le `type-check` frontend, `eslint` ciblé et `prettier --check` sur les fichiers frontend touchés sont passés localement avant push.
- **Validation métier réalisée** : la recette utilisateur a été confirmée après fusion, ce qui clôt le ticket côté backlog.

### BL-030 — Politique de modification des objets métier validés

- **Dates** : `created=2026-04-16`
- **Pourquoi** : plusieurs objets métier ont déjà un cycle de vie implicite (`draft`, `sent`, `paid`, écritures auto-générées, imports historiques), mais la règle cible de modification reste floue dès qu'un objet a déjà produit des effets comptables ou des dépendances fonctionnelles.
- **Résultat attendu** : une politique explicite qui dit, selon le type d'objet et son statut, ce qui est modifiable directement, ce qui doit régénérer des effets dérivés, ce qui doit être historisé, et ce qui doit être interdit ou remplacé par une opération métier distincte.
- **Questions à trancher** :
	- peut-on modifier librement une facture `draft`, `sent` ou `paid` ;
	- faut-il régénérer, annuler puis recréer, ou historiser les écritures comptables dérivées après modification ;
	- quelle différence de traitement entre correction mineure, changement de montant et annulation métier ;
	- faut-il prévoir plus tard des mécanismes dédiés (`avoir`, annulation, revalidation, journal d'audit`) au lieu d'une édition directe uniforme ;
	- qu'a-t-on le droit de réécrire automatiquement lorsqu'un import `Comptabilité` vient clarifier une facture créée plus tôt depuis `Gestion`.
- **Critère d'acceptation** : pour chaque grande famille d'objets métier, un utilisateur et un développeur peuvent répondre sans ambiguïté à la question "que se passe-t-il si je modifie cet objet maintenant ?".
- **Point d'attention** : la traçabilité et la cohérence comptable doivent primer sur la simplicité apparente d'une édition directe, y compris quand la modification vient d'un rapprochement automatique entre imports `Gestion` et `Comptabilité`.

## Prêt

- Aucun sujet pour le moment.

## En cours

- **BL-021** — `created=2026-04-13`, `started=2026-04-13` — Les lots 1 à 3 du manuel utilisateur sont livrés, mais le lot 4 reste à réaliser pour finaliser la stabilisation éditoriale et l'enrichissement visuel.
- **BL-022** — `created=2026-04-13`, `started=2026-04-13` — Les lots 1 et 2 sont intégrés dans `develop` ; les lots suivants restent à traiter et le retest des droits réels a été traité séparément dans `BL-023`, désormais terminé.

## Fait

- **BL-001** — `created=2026-04-12`, `completed=2026-04-12` — Le backlog sert désormais de support de suivi versionné avec priorités, statuts et mises à jour explicites.
- **BL-002** — `created=2026-04-12`, `completed=2026-04-12` — La documentation utilisateur import/reset a été rédigée dans `doc/user/import-excel-et-reinitialisation.md`.
- **BL-003** — `created=2026-04-12`, `completed=2026-04-12` — La campagne de retest sur imports réels 2024/2025 a été rejouée sans écart bloquant.
- **BL-005** — `created=2026-04-12`, `started=2026-04-19`, `completed=2026-04-19` — La politique de coexistence effectivement implémentée pour les imports `Comptabilite` est désormais documentée, testée et intégrée dans `develop`, avec distinction explicite entre doublon exact, ligne déjà couverte par Solde et proximité non bloquante avec une écriture `MANUAL`.
- **BL-007** — `created=2026-04-12`, `completed=2026-04-13` — La convention est arrêtée pour le mode de travail actuel : `doc/backlog.md` reste la source de vérité, sans synchronisation systématique avec des issues GitHub à ce stade.
- **BL-008** — `created=2026-04-12`, `started=2026-04-18`, `completed=2026-04-18` — Le premier lot de convergence BL-008 est désormais intégré dans `develop` avec preview bidirectionnelle par domaine, détails `extra_in_solde`, filtre de période dédié à la comparaison et recette locale rejouable.
- **BL-009** — `created=2026-04-12`, `completed=2026-04-12` — Le plan comptable par défaut a été enrichi à partir des comptes réellement rencontrés dans les imports historiques.
- **BL-010** — `created=2026-04-12`, `completed=2026-04-12` — Une stratégie sûre de clôture administrative des exercices historiques importés a été définie et livrée.
- **BL-011** — `created=2026-04-12`, `completed=2026-04-12` — L'exercice courant global et son sélecteur partagé ont été livrés sur les écrans comptables concernés.
- **BL-012** — `created=2026-04-12`, `completed=2026-04-12` — La liste des paiements affiche la référence métier et permet l'édition directe.
- **BL-013** — `created=2026-04-12`, `completed=2026-04-12` — Le journal de caisse propose désormais référence, détail et édition directe.
- **BL-014** — `created=2026-04-12`, `completed=2026-04-12` — Le journal comptable est enrichi pour la lecture métier, le détail et la navigation vers les factures.
- **BL-016** — `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14` — Les microcopies et états visibles les plus incohérents ont été harmonisés sur `Banque`, `Caisse` et `Salaires` via des clés i18n dédiées.
- **BL-017** — `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14` — L'affichage des mois et périodes métier est maintenant uniformisé au format français sur `Salaires` et le `Dashboard` sans changer les formats d'échange ISO.
- **BL-018** — `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14` — Les écrans de liste principaux partagent maintenant un socle commun de tri, filtres et compteurs d'état, avec filtres de date FR/ISO et exclusion explicite des tableaux fixes `bilan` / `résultat`.
- **BL-023** — `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14` — Les rôles métier `Gestionnaire` / `Comptable` / `Administrateur` sont maintenant alignés entre docs, navigation, guards frontend et permissions backend, avec séparation visible `Gestion` / `Comptabilité` et couverture de test ciblée.
- **BL-025** — `created=2026-04-13`, `started=2026-04-13`, `completed=2026-04-13` — Le grand livre est maintenant borné à l'exercice choisi, sans option multi-exercices, avec un solde d'ouverture cohérent quand la période démarre en cours d'exercice.
- **BL-026** — `created=2026-04-15`, `started=2026-04-15`, `completed=2026-04-16` — Le ticket a livré un cadrage de recette et un constat exploitable sur la reprise `2024`, puis a été clos une fois les écarts résiduels requalifiés en différences de modélisation assumées ou en suites dédiées (`BL-008`, `BL-029`).
- **BL-029** — `created=2026-04-16`, `started=2026-04-16`, `completed=2026-04-19` — La saisie des factures clients par lignes typées, le calcul dérivé du total et de la ventilation comptable, et les adaptations d'import `Gestion` / `Comptabilité` sont maintenant intégrés dans `develop` et validés côté recette métier utilisateur.
