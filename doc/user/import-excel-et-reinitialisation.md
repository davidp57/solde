# Guide utilisateur - import Excel et réinitialisation

## But

Ce document explique comment utiliser l'import Excel dans Solde pour :

- initialiser l'application à partir des fichiers historiques existants ;
- contrôler le résultat d'un import avant validation ;
- comprendre les messages affichés par la prévisualisation et par l'import ;
- savoir exactement ce que fait la réinitialisation des données.

Ce guide est orienté usage métier et tests manuels. Il complète le manuel utilisateur principal quand vous devez travailler sur une reprise historique ou un contrôle d'import.

## Les deux types d'import

### Import `Gestion`

L'import `Gestion` sert à reprendre les données de gestion courante contenues dans un classeur historique.

Il peut créer :

- des contacts ;
- des factures ;
- des paiements ;
- des mouvements de caisse ;
- des mouvements bancaires ;
- des écritures comptables générées à partir des règles comptables configurées dans Solde.

Sur les fichiers historiques actuellement utilisés, l'import `Gestion` peut aussi reconstituer des factures fournisseurs et leur règlement quand il détecte des références de type `FF-...` dans les feuilles `Banque` ou `Caisse`.

### Import `Comptabilité`

L'import `Comptabilité` sert à importer les écritures du `Journal` Excel comme écritures comptables supplémentaires.

Il ne crée pas de contacts, de factures ni de paiements. Il ajoute uniquement des écritures comptables manuelles.

Si des écritures ont déjà été générées dans Solde depuis la gestion, l'import `Comptabilité` reste autorisé :

- les doublons exacts sont ignorés ;
- seules les écritures nouvelles sont ajoutées.

## Avant de commencer

Avant toute reprise ou tout test manuel, vérifiez les points suivants.

1. Travaillez sur une base sauvegardée ou restaurable facilement.
2. Utilisez un fichier Excel source non modifié entre deux essais, sinon le garde-fou de réimport exact devient moins utile.
3. Créez d'abord les exercices comptables couvrant toutes les dates réellement présentes dans les fichiers à importer.
4. Préparez le plan comptable si vous voulez relire et contrôler correctement les écritures importées.
5. Préparez les règles comptables si vous voulez que l'import `Gestion` génère automatiquement les écritures correspondantes.

Important : l'import Excel ne crée pas automatiquement :

- les exercices comptables ;
- le plan comptable ;
- les règles comptables.

## Comment utiliser la prévisualisation

La prévisualisation est l'étape obligatoire avant un import.

Elle permet de voir :

- si le fichier est importable dans l'état actuel de la base ;
- combien d'objets ou d'écritures seront probablement créés ;
- quelles feuilles sont reconnues ;
- quelles lignes seront ignorées ;
- quelles lignes bloquent l'import.

Procédure recommandée :

1. Choisir le bon type de fichier : `Gestion` ou `Comptabilité`.
2. Sélectionner le fichier Excel.
3. Lancer la prévisualisation.
4. Vérifier que l'état général permet l'import.
5. Relire les avertissements feuille par feuille.
6. Contrôler les compteurs de lignes ignorées et bloquantes.

Si la prévisualisation est bloquée, il ne faut pas lancer l'import. Il faut d'abord corriger la donnée source ou la stratégie de reprise.

## Comment interpréter les diagnostics

### Avertissements

Un avertissement indique qu'une ligne ou une feuille a été ignorée, ou qu'une adaptation automatique a été appliquée sans bloquer l'import.

### Lignes bloquantes

Une ligne bloquante empêche l'import complet du fichier.

### Réimport exact

Si un même fichier a déjà été importé avec succès, Solde refuse son réimport exact.

Ce comportement est volontaire. Il évite les doublons involontaires et protège la reprise historique.

## Réinitialisation des données

La réinitialisation des données est une action d'administration destinée surtout aux démonstrations et aux tests de reprise.

Elle supprime toutes les données applicatives, y compris :

- les contacts ;
- les factures ;
- les paiements ;
- les écritures comptables ;
- les données de banque et de caisse ;
- l'historique d'import.

Conséquence importante : après une réinitialisation, il faut reconfigurer l'environnement avant de relancer un import, en particulier les exercices comptables, le plan comptable et les règles comptables utiles.

Cette action est irréversible. Elle ne doit pas être utilisée sur une base que vous souhaitez conserver en l'état.

## En cas de doute

Si un import donne un résultat inattendu :

1. ne relancez pas immédiatement sans comprendre ce qui s'est passé ;
2. relisez la prévisualisation ;
3. vérifiez les lignes ignorées et bloquantes ;
4. vérifiez que les exercices nécessaires existent bien ;
5. repartez d'une base restaurée si vous devez refaire une reprise complète propre.# Guide utilisateur — import Excel et réinitialisation

## But

Ce document explique comment utiliser l'import Excel dans Solde pour :

- initialiser l'application à partir des fichiers historiques existants ;
- contrôler le résultat d'un import avant validation ;
- comprendre les messages affichés par la prévisualisation et par l'import ;
- savoir exactement ce que fait la réinitialisation des données.

Ce guide est orienté usage métier et tests manuels. Il complète la documentation technique, mais n'a pas besoin d'être lu comme une spécification.

## Les deux types d'import

### Import `Gestion`

L'import `Gestion` sert à reprendre les données de gestion courante contenues dans un classeur historique.

Il peut créer :

- des contacts ;
- des factures ;
- des paiements ;
- des mouvements de caisse ;
- des mouvements bancaires ;
- des écritures comptables générées à partir des règles comptables configurées dans Solde.

Sur les fichiers historiques actuellement utilisés, l'import `Gestion` peut aussi reconstituer des factures fournisseurs et leur règlement quand il détecte des références de type `FF-...` dans les feuilles `Banque` ou `Caisse`.

### Import `Comptabilité`

L'import `Comptabilité` sert à importer les écritures du `Journal` Excel comme écritures comptables supplémentaires.

Il ne crée pas de contacts, de factures ni de paiements. Il ajoute uniquement des écritures comptables manuelles.

Si des écritures ont déjà été générées dans Solde depuis la gestion, l'import `Comptabilité` reste autorisé :

- les doublons exacts sont ignorés ;
- seules les écritures nouvelles sont ajoutées.

## Avant de commencer

Avant toute reprise ou tout test manuel, vérifier les points suivants.

1. Travailler sur une base sauvegardée ou restaurable facilement.
2. Utiliser un fichier Excel source non modifié entre deux essais, sinon le garde-fou de réimport exact devient moins utile.
3. Créer d'abord les exercices comptables couvrant toutes les dates réellement présentes dans les fichiers à importer.
4. Préparer le plan comptable si vous voulez relire et contrôler correctement les écritures importées.
5. Préparer les règles comptables si vous voulez que l'import `Gestion` génère automatiquement les écritures correspondantes.

Important : l'import Excel ne crée pas automatiquement :

- les exercices comptables ;
- le plan comptable ;
- les règles comptables.

Pour les fichiers historiques actuellement rejoués dans le projet, il faut prévoir des exercices couvrant les dates de `2022` à `2026`, même si les fichiers portent les noms `2024` et `2025`.

## Ordre recommandé pour les tests historiques actuels

Pour le rejeu manuel des fichiers actuellement disponibles, l'ordre recommandé est le suivant.

1. Importer `Gestion 2024.xlsx`.
2. Importer `Gestion 2025.xlsx`.
3. Vérifier que le résultat est cohérent côté gestion et écritures générées.
4. Importer ensuite `Comptabilité 2024.xlsx` si vous voulez compléter la comptabilité avec le journal Excel.
5. Importer enfin `Comptabilité 2025.xlsx`.

Cet ordre est important, car certains rapprochements de paiements deviennent non ambigus seulement si le fichier `Gestion` précédent a déjà été repris.

## Raccourcis temporaires de test

En développement local, la page `Import Excel` peut afficher quatre boutons temporaires pour rejouer directement les fichiers historiques sans passer par la prévisualisation ni la confirmation des avertissements.

Ces boutons sont volontairement réservés aux tests locaux. Ils utilisent des chemins de fichiers configurés côté serveur et restent désactivés tant que les classeurs attendus ne sont pas trouvés.

Quand ils sont activés, l'ordre recommandé reste le même :

1. `Gestion 2024`
2. `Gestion 2025`
3. `Comptabilité 2024`
4. `Comptabilité 2025`

Le résultat détaillé de chaque import reste affiché dans la page après exécution, ce qui permet de contrôler immédiatement les créations, lignes ignorées et blocages sans masquer un éventuel problème dans une opération globale.

## Comment utiliser la prévisualisation

La prévisualisation est l'étape obligatoire avant un import.

Elle permet de voir :

- si le fichier est importable dans l'état actuel de la base ;
- combien d'objets ou d'écritures seront probablement créés ;
- quelles feuilles sont reconnues ;
- quelles lignes seront ignorées ;
- quelles lignes bloquent l'import.

Procédure recommandée :

1. Choisir le bon type de fichier : `Gestion` ou `Comptabilité`.
2. Sélectionner le fichier Excel.
3. Lancer la prévisualisation.
4. Vérifier que l'état général permet l'import.
5. Relire les avertissements feuille par feuille.
6. Contrôler les compteurs de lignes ignorées et bloquantes.

Si la prévisualisation est bloquée, il ne faut pas lancer l'import. Il faut d'abord corriger la donnée source ou la stratégie de reprise.

## Comment interpréter les diagnostics

Tous les messages n'ont pas la même gravité.

### Avertissements

Un avertissement indique qu'une ligne ou une feuille a été ignorée, ou qu'une adaptation automatique a été appliquée sans bloquer l'import.

Exemples fréquents :

- feuille auxiliaire ignorée ;
- ligne `Total` ignorée dans `Factures` ;
- ligne de solde initial ignorée dans `Caisse` ;
- ligne descriptive de solde ignorée dans `Banque` ;
- ligne `Journal` à débit et crédit nuls ignorée ;
- doublon exact déjà présent en comptabilité.

### Lignes bloquantes

Une ligne bloquante empêche l'import complet du fichier.

Exemples fréquents :

- colonnes requises absentes ;
- date ou montant invalide ;
- paiement impossible à rapprocher ;
- paiement ambigu ;
- contact ou facture impossible à déterminer sans ambiguïté.

### Réimport exact

Si un même fichier a déjà été importé avec succès, Solde refuse son réimport exact.

Ce comportement est volontaire. Il évite les doublons involontaires et protège la reprise historique.

## Ce que fait réellement l'import `Gestion`

L'import `Gestion` lit plusieurs feuilles du classeur historique.

En pratique, il peut :

- créer les contacts absents ;
- créer les factures absentes ;
- rapprocher les paiements avec les factures existantes ou importées dans le même flux ;
- créer les mouvements de caisse et de banque ;
- générer les écritures comptables correspondantes si les règles existent déjà dans Solde ;
- créer des factures fournisseurs historiques et leur règlement si une référence `FF-...` est détectée dans `Banque` ou `Caisse`.

L'import `Gestion` n'est donc pas limité aux seules factures clients. Sur les fichiers historiques, il peut enrichir sensiblement la reprise comptable.

## Ce que fait réellement l'import `Comptabilité`

L'import `Comptabilité` se concentre sur la feuille `Journal`.

Il :

- importe les écritures exploitables ;
- rattache chaque écriture à l'exercice couvrant sa date, si cet exercice existe ;
- ignore les lignes à débit et crédit nuls ;
- ignore les doublons exacts déjà présents ;
- laisse de côté les feuilles de reporting et `Journal (saisie)`.

Il ne remplace pas la préparation du plan comptable et ne crée pas les règles comptables.

## Contrôles manuels après import

Après chaque import, vérifier au minimum les points suivants.

1. Le résumé global de l'import.
2. Le détail feuille par feuille.
3. Les compteurs de créations, de lignes ignorées et de lignes bloquantes.
4. La présence des objets attendus dans l'interface.
5. Le rattachement des écritures au bon exercice.
6. L'absence d'erreur inattendue dans le résultat final.

Pour les tests historiques actuels, il est utile de comparer le résultat obtenu avec les ordres de grandeur déjà rejoués dans le projet :

- `Gestion 2024.xlsx` : `64` contacts, `303` factures, `308` paiements, `1222` écritures, `102` mouvements de caisse, `210` transactions bancaires ;
- `Gestion 2025.xlsx` : `18` contacts, `211` factures, `211` paiements, `844` écritures, `75` mouvements de caisse, `145` transactions bancaires ;
- `Comptabilité 2024.xlsx` : `1367` écritures importées ;
- `Comptabilité 2025.xlsx` : `928` écritures importées.

Ces chiffres correspondent au rejeu réel validé sur base isolée avec les fichiers historiques présents dans `data/`.

## Quand clôturer les exercices historiques

Pendant une reprise historique, il ne faut pas clôturer les exercices au fil de l'eau.

La bonne séquence est la suivante :

1. créer tous les exercices nécessaires ;
2. importer tous les fichiers historiques ;
3. vérifier le résultat métier et comptable ;
4. clôturer ensuite les anciens exercices avec la clôture administrative.

La clôture administrative sert uniquement à marquer un exercice comme clôturé sans créer de nouvelles écritures de clôture ou de report à nouveau. Elle est adaptée aux exercices déjà clôturés dans Excel avant reprise.

La clôture classique de Solde doit rester réservée aux exercices gérés directement dans l'application.

## Réinitialisation des données

La réinitialisation des données est une action d'administration destinée surtout aux démonstrations et aux tests de reprise.

Elle supprime toutes les données applicatives, y compris :

- les paramètres ;
- le plan comptable ;
- les règles comptables ;
- les exercices comptables ;
- les contacts ;
- les factures ;
- les paiements ;
- les écritures comptables ;
- les données de banque et de caisse ;
- l'historique d'import.

Seuls les utilisateurs sont conservés.

Conséquence importante : après une réinitialisation, il faut reconfigurer l'environnement avant de relancer un import, en particulier :

1. recréer les exercices comptables nécessaires ;
2. recharger ou recréer le plan comptable ;
3. recharger ou recréer les règles comptables si l'on veut régénérer les écritures depuis la gestion.

Cette action est irréversible. Elle ne doit pas être utilisée sur une base que vous souhaitez conserver en l'état.

## En cas de doute

Si un import donne un résultat inattendu :

1. ne pas relancer immédiatement sans comprendre ce qui s'est passé ;
2. relire la prévisualisation ;
3. vérifier les lignes ignorées et bloquantes ;
4. vérifier que les exercices nécessaires existent bien ;
5. repartir d'une base restaurée si vous devez refaire une reprise complète propre.

En phase de transition, si vous tenez encore la comptabilité en parallèle dans Excel et dans Solde, l'import doit aussi servir de contrôle régulier pour vérifier qu'aucune écriture ne manque et qu'aucune divergence n'a été introduite.
||||||| parent of 8704648 (feat(import): improve replay and accounting workflows)
=======
# Guide utilisateur — import Excel et réinitialisation

## But

Ce document explique comment utiliser l'import Excel dans Solde pour :

- initialiser l'application à partir des fichiers historiques existants ;
- contrôler le résultat d'un import avant validation ;
- comprendre les messages affichés par la prévisualisation et par l'import ;
- savoir exactement ce que fait la réinitialisation des données.

Ce guide est orienté usage métier et tests manuels. Il complète la documentation technique, mais n'a pas besoin d'être lu comme une spécification.

## Les deux types d'import

### Import `Gestion`

L'import `Gestion` sert à reprendre les données de gestion courante contenues dans un classeur historique.

Il peut créer :

- des contacts ;
- des factures ;
- des paiements ;
- des mouvements de caisse ;
- des mouvements bancaires ;
- des écritures comptables générées à partir des règles comptables configurées dans Solde.

Sur les fichiers historiques actuellement utilisés, l'import `Gestion` peut aussi reconstituer des factures fournisseurs et leur règlement quand il détecte des références de type `FF-...` dans les feuilles `Banque` ou `Caisse`.

### Import `Comptabilité`

L'import `Comptabilité` sert à importer les écritures du `Journal` Excel comme écritures comptables supplémentaires.

Il ne crée pas de contacts, de factures ni de paiements. Il ajoute uniquement des écritures comptables manuelles.

Si des écritures ont déjà été générées dans Solde depuis la gestion, l'import `Comptabilité` reste autorisé :

- les doublons exacts sont ignorés ;
- seules les écritures nouvelles sont ajoutées.

## Avant de commencer

Avant toute reprise ou tout test manuel, vérifier les points suivants.

1. Travailler sur une base sauvegardée ou restaurable facilement.
2. Utiliser un fichier Excel source non modifié entre deux essais, sinon le garde-fou de réimport exact devient moins utile.
3. Créer d'abord les exercices comptables couvrant toutes les dates réellement présentes dans les fichiers à importer.
4. Préparer le plan comptable si vous voulez relire et contrôler correctement les écritures importées.
5. Préparer les règles comptables si vous voulez que l'import `Gestion` génère automatiquement les écritures correspondantes.

Important : l'import Excel ne crée pas automatiquement :

- les exercices comptables ;
- le plan comptable ;
- les règles comptables.

Pour les fichiers historiques actuellement rejoués dans le projet, il faut prévoir des exercices couvrant les dates de `2022` à `2026`, même si les fichiers portent les noms `2024` et `2025`.

## Ordre recommandé pour les tests historiques actuels

Pour le rejeu manuel des fichiers actuellement disponibles, l'ordre recommandé est le suivant.

1. Importer `Gestion 2024.xlsx`.
2. Importer `Gestion 2025.xlsx`.
3. Vérifier que le résultat est cohérent côté gestion et écritures générées.
4. Importer ensuite `Comptabilité 2024.xlsx` si vous voulez compléter la comptabilité avec le journal Excel.
5. Importer enfin `Comptabilité 2025.xlsx`.

Cet ordre est important, car certains rapprochements de paiements deviennent non ambigus seulement si le fichier `Gestion` précédent a déjà été repris.

## Raccourcis temporaires de test

En développement local, la page `Import Excel` peut afficher quatre boutons temporaires pour rejouer directement les fichiers historiques sans passer par la prévisualisation ni la confirmation des avertissements.

Ces boutons sont volontairement réservés aux tests locaux. Ils utilisent des chemins de fichiers configurés côté serveur et restent désactivés tant que les classeurs attendus ne sont pas trouvés.

Quand ils sont activés, l'ordre recommandé reste le même :

1. `Gestion 2024`
2. `Gestion 2025`
3. `Comptabilité 2024`
4. `Comptabilité 2025`

Le résultat détaillé de chaque import reste affiché dans la page après exécution, ce qui permet de contrôler immédiatement les créations, lignes ignorées et blocages sans masquer un éventuel problème dans une opération globale.

## Comment utiliser la prévisualisation

La prévisualisation est l'étape obligatoire avant un import.

Elle permet de voir :

- si le fichier est importable dans l'état actuel de la base ;
- combien d'objets ou d'écritures seront probablement créés ;
- quelles feuilles sont reconnues ;
- quelles lignes seront ignorées ;
- quelles lignes bloquent l'import.

Procédure recommandée :

1. Choisir le bon type de fichier : `Gestion` ou `Comptabilité`.
2. Sélectionner le fichier Excel.
3. Lancer la prévisualisation.
4. Vérifier que l'état général permet l'import.
5. Relire les avertissements feuille par feuille.
6. Contrôler les compteurs de lignes ignorées et bloquantes.

Si la prévisualisation est bloquée, il ne faut pas lancer l'import. Il faut d'abord corriger la donnée source ou la stratégie de reprise.

## Comment interpréter les diagnostics

Tous les messages n'ont pas la même gravité.

### Avertissements

Un avertissement indique qu'une ligne ou une feuille a été ignorée, ou qu'une adaptation automatique a été appliquée sans bloquer l'import.

Exemples fréquents :

- feuille auxiliaire ignorée ;
- ligne `Total` ignorée dans `Factures` ;
- ligne de solde initial ignorée dans `Caisse` ;
- ligne descriptive de solde ignorée dans `Banque` ;
- ligne `Journal` à débit et crédit nuls ignorée ;
- doublon exact déjà présent en comptabilité.

### Lignes bloquantes

Une ligne bloquante empêche l'import complet du fichier.

Exemples fréquents :

- colonnes requises absentes ;
- date ou montant invalide ;
- paiement impossible à rapprocher ;
- paiement ambigu ;
- contact ou facture impossible à déterminer sans ambiguïté.

### Réimport exact

Si un même fichier a déjà été importé avec succès, Solde refuse son réimport exact.

Ce comportement est volontaire. Il évite les doublons involontaires et protège la reprise historique.

## Ce que fait réellement l'import `Gestion`

L'import `Gestion` lit plusieurs feuilles du classeur historique.

En pratique, il peut :

- créer les contacts absents ;
- créer les factures absentes ;
- rapprocher les paiements avec les factures existantes ou importées dans le même flux ;
- créer les mouvements de caisse et de banque ;
- générer les écritures comptables correspondantes si les règles existent déjà dans Solde ;
- créer des factures fournisseurs historiques et leur règlement si une référence `FF-...` est détectée dans `Banque` ou `Caisse`.

L'import `Gestion` n'est donc pas limité aux seules factures clients. Sur les fichiers historiques, il peut enrichir sensiblement la reprise comptable.

## Ce que fait réellement l'import `Comptabilité`

L'import `Comptabilité` se concentre sur la feuille `Journal`.

Il :

- importe les écritures exploitables ;
- rattache chaque écriture à l'exercice couvrant sa date, si cet exercice existe ;
- ignore les lignes à débit et crédit nuls ;
- ignore les doublons exacts déjà présents ;
- laisse de côté les feuilles de reporting et `Journal (saisie)`.

Il ne remplace pas la préparation du plan comptable et ne crée pas les règles comptables.

## Contrôles manuels après import

Après chaque import, vérifier au minimum les points suivants.

1. Le résumé global de l'import.
2. Le détail feuille par feuille.
3. Les compteurs de créations, de lignes ignorées et de lignes bloquantes.
4. La présence des objets attendus dans l'interface.
5. Le rattachement des écritures au bon exercice.
6. L'absence d'erreur inattendue dans le résultat final.

Pour les tests historiques actuels, il est utile de comparer le résultat obtenu avec les ordres de grandeur déjà rejoués dans le projet :

- `Gestion 2024.xlsx` : `64` contacts, `303` factures, `308` paiements, `1222` écritures, `102` mouvements de caisse, `210` transactions bancaires ;
- `Gestion 2025.xlsx` : `18` contacts, `211` factures, `211` paiements, `844` écritures, `75` mouvements de caisse, `145` transactions bancaires ;
- `Comptabilité 2024.xlsx` : `1367` écritures importées ;
- `Comptabilité 2025.xlsx` : `928` écritures importées.

Ces chiffres correspondent au rejeu réel validé sur base isolée avec les fichiers historiques présents dans `data/`.

## Quand clôturer les exercices historiques

Pendant une reprise historique, il ne faut pas clôturer les exercices au fil de l'eau.

La bonne séquence est la suivante :

1. créer tous les exercices nécessaires ;
2. importer tous les fichiers historiques ;
3. vérifier le résultat métier et comptable ;
4. clôturer ensuite les anciens exercices avec la clôture administrative.

La clôture administrative sert uniquement à marquer un exercice comme clôturé sans créer de nouvelles écritures de clôture ou de report à nouveau. Elle est adaptée aux exercices déjà clôturés dans Excel avant reprise.

La clôture classique de Solde doit rester réservée aux exercices gérés directement dans l'application.

## Réinitialisation des données

La réinitialisation des données est une action d'administration destinée surtout aux démonstrations et aux tests de reprise.

Elle supprime toutes les données applicatives, y compris :

- les paramètres ;
- le plan comptable ;
- les règles comptables ;
- les exercices comptables ;
- les contacts ;
- les factures ;
- les paiements ;
- les écritures comptables ;
- les données de banque et de caisse ;
- l'historique d'import.

Seuls les utilisateurs sont conservés.

Conséquence importante : après une réinitialisation, il faut reconfigurer l'environnement avant de relancer un import, en particulier :

1. recréer les exercices comptables nécessaires ;
2. recharger ou recréer le plan comptable ;
3. recharger ou recréer les règles comptables si l'on veut régénérer les écritures depuis la gestion.

Cette action est irréversible. Elle ne doit pas être utilisée sur une base que vous souhaitez conserver en l'état.

## En cas de doute

Si un import donne un résultat inattendu :

1. ne pas relancer immédiatement sans comprendre ce qui s'est passé ;
2. relire la prévisualisation ;
3. vérifier les lignes ignorées et bloquantes ;
4. vérifier que les exercices nécessaires existent bien ;
5. repartir d'une base restaurée si vous devez refaire une reprise complète propre.

En phase de transition, si vous tenez encore la comptabilité en parallèle dans Excel et dans Solde, l'import doit aussi servir de contrôle régulier pour vérifier qu'aucune écriture ne manque et qu'aucune divergence n'a été introduite.
>>>>>>> 8704648 (feat(import): improve replay and accounting workflows)
