# Guide utilisateur - import Excel et réinitialisation

## But

Ce document explique comment utiliser dans Solde :

- l'import Excel `Gestion` ;
- l'import Excel `Comptabilite` ;
- l'historique d'import réversible ;
- le reset sélectif de reprise ;
- la réinitialisation complète de la base.

Il est orienté usage métier et tests manuels.

## Les deux types d'import

### Import `Gestion`

L'import `Gestion` sert à reprendre la gestion courante depuis un classeur historique.

Il peut créer ou alimenter :

- des contacts ;
- des factures ;
- des paiements ;
- des mouvements de caisse ;
- des transactions bancaires ;
- des écritures comptables générées à partir des règles présentes dans Solde.

Sur les fichiers historiques actuellement utilisés, il peut aussi reconstituer des factures fournisseurs et leur règlement quand des références de type `FF-...` sont détectées dans `Banque` ou `Caisse`.

### Import `Comptabilite`

L'import `Comptabilite` sert à reprendre les écritures du `Journal` Excel.

Il ne crée pas de contacts, de factures ni de paiements. Il ajoute uniquement des écritures comptables.

Si des écritures existent déjà dans Solde :

- les doublons exacts sont ignorés ;
- les lignes réellement nouvelles restent importables ;
- certaines proximités avec des écritures manuelles existantes peuvent être seulement signalées en avertissement.

## Avant de commencer

Avant toute reprise ou tout retest manuel, vérifier les points suivants.

1. Travailler sur une base sauvegardée ou restaurable facilement.
2. Utiliser un fichier Excel source inchangé entre deux essais comparables.
3. Créer les exercices comptables couvrant réellement les dates présentes dans les fichiers.
4. Préparer le plan comptable si vous voulez relire les écritures importées.
5. Préparer les règles comptables si vous voulez que `Gestion` génère automatiquement ses écritures.

Important : l'import Excel ne crée pas automatiquement les exercices, le plan comptable ou les règles comptables.

## Workflow recommandé

Quand l'import a été préparé par Solde via le flux réversible, l'ordre recommandé est le suivant :

1. Prévisualiser.
2. Exécuter l'import si le diagnostic est acceptable.
3. Vérifier le résultat métier.
4. Utiliser l'historique d'import pour `undo` ou `redo` tant que le journal réversible reste applicable.

Quand le flux réversible ne suffit pas, ou pour des imports historiques plus anciens non couverts par ce mécanisme, utiliser le reset sélectif décrit plus bas.

## Prévisualisation

La prévisualisation est l'étape obligatoire avant un import.

Elle permet de voir :

- si le fichier est importable dans l'état actuel de la base ;
- combien d'objets ou d'écritures seront probablement créés ;
- quelles feuilles sont reconnues ;
- quelles lignes seront ignorées ;
- quelles lignes bloquent l'import.

Procédure recommandée :

1. Choisir le bon type de fichier : `Gestion` ou `Comptabilite`.
2. Sélectionner le fichier Excel.
3. Lancer la prévisualisation.
4. Vérifier que l'état général permet l'import.
5. Relire les avertissements feuille par feuille.
6. Contrôler les compteurs de lignes ignorées et bloquantes.

Si la prévisualisation est bloquée, il ne faut pas lancer l'import.

## Comment lire les diagnostics

### Avertissements

Un avertissement indique qu'une ligne ou une feuille a été ignorée, ou qu'une adaptation automatique a été appliquée sans bloquer l'import.

### Lignes bloquantes

Une ligne bloquante empêche l'import complet du fichier.

### Réimport exact

Si un même fichier a déjà été importé avec succès, Solde refuse son réimport exact.

Ce comportement évite les doublons involontaires et protège la reprise historique.

## Historique d'import réversible

L'historique d'import réversible est le premier outil à utiliser pour rejouer proprement un import récent préparé par Solde.

Il permet, selon le cas :

- de relire les opérations préparées ;
- d'exécuter un import préparé ;
- d'annuler un import ou une opération ;
- de rejouer une opération annulée.

Ce mécanisme est strict : si l'état courant ne correspond plus à l'état attendu, Solde bloque l'`undo` ou le `redo` pour éviter une annulation incohérente.

## Reset sélectif de reprise

Le reset sélectif est disponible dans la zone de danger des paramètres.

Il sert à supprimer un périmètre d'import ciblé sans effacer toute la base.

### Quand l'utiliser

Utiliser ce reset quand :

- l'import d'origine n'était pas couvert par le journal réversible ;
- l'`undo` strict n'est plus applicable ;
- vous devez rejouer un import historique `Gestion` ou `Comptabilite` pour un exercice précis.

### Comment il est ciblé

Le reset sélectif demande deux choix :

- la filière d'import : `Gestion` ou `Comptabilite` ;
- l'exercice à nettoyer.

Solde construit alors un plan de suppression à partir des traces d'import et affiche une prévisualisation avant confirmation.

### Ce que supprime le reset sélectif

Pour `Gestion`, Solde supprime :

- les objets importés retrouvés dans les traces ;
- les objets dérivés ensuite créés dans Solde à partir de ces objets importés quand ils font partie des dépendances métier connues ;
- les traces d'import associées au périmètre supprimé.

Pour `Comptabilite`, Solde supprime :

- les écritures importées pour l'exercice ciblé ;
- les traces d'import associées.

La prévisualisation liste séparément :

- les objets importés retrouvés ;
- les objets dérivés identifiés ;
- le plan de suppression final.

### Limites à connaître

Le reset sélectif n'est pas un moteur générique de nettoyage universel.

Il applique les règles métier actuellement connues pour la reprise d'import. Il faut donc toujours relire la prévisualisation avant de confirmer.

### Précaution importante

Cette action est irréversible.

Avant de l'utiliser, vérifier que vous travaillez bien sur l'exercice voulu et sur la bonne filière d'import.

## Réinitialisation complète de la base

La réinitialisation complète supprime toutes les données applicatives.

Elle efface notamment :

- les contacts ;
- les factures ;
- les paiements ;
- les écritures comptables ;
- les données de banque et de caisse ;
- les traces d'import.

Après une réinitialisation complète, il faut reconfigurer l'environnement avant de relancer une reprise, en particulier :

- les exercices comptables ;
- le plan comptable ;
- les règles comptables utiles ;
- les éventuels paramétrages de trésorerie d'ouverture.

Cette action doit rester réservée aux démonstrations, essais isolés et reprises complètes sur base jetable ou restaurable.

## Contrôles manuels après import ou reset

Après chaque import, `undo`, reset sélectif ou reset complet, vérifier au minimum :

1. le résumé global de l'opération ;
2. les objets attendus ou supprimés ;
3. les exercices concernés ;
4. les journaux de banque, de caisse et de comptabilité si le périmètre les touche ;
5. l'absence d'effet de bord inattendu sur les autres données conservées.

## En cas de doute

Si un résultat semble incohérent :

1. ne pas rejouer immédiatement sans comprendre ;
2. relire la prévisualisation ou l'historique d'import ;
3. vérifier le bon exercice et le bon type d'import ;
4. repartir d'une base restaurée si vous devez refaire une reprise complète propre.
