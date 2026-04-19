# Manuel utilisateur - version texte lots 1 à 3

## Objectif du guide

Cette version texte du manuel utilisateur couvre désormais les lots 1 à 3 prévus pour BL-021. Elle aide à prendre en main Solde pour les parcours du quotidien, de la connexion jusqu'à la consultation des écrans comptables, en passant par les factures fournisseurs, la caisse, la banque et l'import Excel.

Ce document décrit les écrans actuellement disponibles. Les captures d'écran seront ajoutées dans une phase ultérieure, quand l'interface sera stabilisée.

## Périmètre de cette version

Cette version couvre :

1. la connexion ;
2. les repères de navigation ;
3. la gestion des contacts ;
4. la création et le suivi des factures clients ;
5. la consultation et le suivi des paiements clients ;
6. les factures fournisseurs ;
7. la caisse ;
8. la banque et les remises ;
9. l'import Excel ;
10. les écrans comptables principaux ;
11. une FAQ courte ;
12. un glossaire métier simple.

Ce document ne couvre pas encore les captures d'écran annotées ni la version finale mise en page pour impression.

## Avant de commencer

### Ce qu'il vous faut

- un compte utilisateur actif ;
- votre identifiant et votre mot de passe ;
- au moins un exercice comptable déjà créé par l'administration ;
- si vous voulez créer une facture, le contact client doit déjà exister dans Solde.

### Ce que vous voyez selon votre rôle

Les écrans principaux de gestion sont visibles depuis le menu latéral ou le menu mobile. Certains écrans d'administration, comme `Paramètres`, ne sont visibles que pour un compte administrateur.

## 1. Se connecter

### Objectif

Accéder à l'application avec votre compte utilisateur.

### Étapes

1. Ouvrez la page de connexion de Solde.
2. Saisissez votre identifiant dans le champ `Identifiant`.
3. Saisissez votre mot de passe dans le champ `Mot de passe`.
4. Cliquez sur `Se connecter`.

### Résultat attendu

Si les informations sont correctes, Solde ouvre le tableau de bord.

### En cas de problème

- Si un message indique que l'identifiant ou le mot de passe est incorrect, vérifiez la saisie puis recommencez.
- Si un message indique que le serveur est inaccessible, il s'agit plutôt d'un problème technique ou de réseau.

## 2. Se repérer dans l'application

### Objectif

Comprendre où trouver les principaux écrans du quotidien.

### Repères utiles

- Le menu principal donne accès au `Tableau de bord`, aux `Contacts`, aux `Factures clients`, aux `Paiements`, à la `Banque`, à la `Caisse` et aux écrans comptables.
- En version mobile, ce menu s'ouvre avec le bouton en haut de l'écran.
- Votre nom d'utilisateur et votre rôle sont visibles dans la zone latérale ou la barre du haut selon la taille de l'écran.
- Le bouton de déconnexion permet de quitter proprement la session.

### Tableau de bord

Le tableau de bord donne les repères les plus utiles au démarrage :

- solde banque ;
- solde caisse ;
- nombre et montant des factures impayées ;
- nombre de factures en retard ;
- nombre de paiements non remis en banque ;
- exercice en cours ;
- résultat de l'exercice.

Commencez souvent par cet écran si vous voulez vérifier la situation générale avant de saisir ou contrôler des données.

## 3. Gérer les contacts

### Objectif

Créer, retrouver et mettre à jour les personnes ou structures liées à l'association.

### Quand utiliser cet écran

Utilisez l'écran `Contacts` pour :

- créer un nouveau client ;
- enregistrer un fournisseur ;
- mettre à jour un e-mail, un téléphone ou une adresse ;
- consulter l'historique d'un contact.

### Créer un contact

1. Ouvrez `Contacts` dans le menu principal.
2. Cliquez sur `Nouveau contact`.
3. Choisissez le type de contact : `Client`, `Fournisseur` ou `Client & Fournisseur`.
4. Renseignez au minimum le `Nom`.
5. Complétez si besoin le `Prénom`, l'`E-mail`, le `Téléphone`, l'`Adresse` et les `Notes`.
6. Cliquez sur `Enregistrer`.

### Modifier un contact

1. Dans la liste, retrouvez le contact voulu.
2. Utilisez si besoin la recherche ou le filtre par type.
3. Cliquez sur le bouton de modification de la ligne.
4. Ajustez les informations utiles.
5. Cliquez sur `Enregistrer`.

### Consulter l'historique d'un contact

1. Depuis la liste des contacts, cliquez sur le bouton d'historique de la ligne.
2. Solde affiche une fiche avec :
   - les coordonnées du contact ;
   - le total facturé ;
   - le total payé ;
   - le restant dû ;
   - la liste des factures ;
   - la liste des paiements associés.

Cet écran est utile pour répondre à une question simple : où en est ce contact dans son suivi de facturation et d'encaissement ?

### Résultat attendu

Le contact est disponible dans les listes de recherche, notamment lors de la création d'une facture.

### Points d'attention

- Si le contact doit recevoir une facture, vérifiez qu'il est bien créé avec un type compatible `Client` ou `Client & Fournisseur`.
- Le champ `Notes` est utile pour garder un contexte pratique, mais il ne remplace pas une information obligatoire de facturation.

## 4. Créer et suivre une facture client

### Objectif

Établir une facture client, vérifier son statut puis utiliser les actions de suivi disponibles.

### Prérequis

- le contact client existe déjà dans Solde ;
- vous connaissez la date de facture et, si besoin, la date d'échéance ;
- vous avez le détail des lignes à facturer.

### Créer une facture client

1. Ouvrez `Factures clients` dans le menu principal.
2. Cliquez sur `Nouvelle facture`.
3. Sélectionnez le `Contact` concerné.
4. Renseignez la `Date` de facture.
5. Renseignez si besoin l'`Échéance`.
6. Choisissez éventuellement un `Type` de facture si cela vous aide à classer les factures.
7. Ajoutez une `Description` générale si nécessaire.
8. Dans la zone `Lignes`, ajoutez une ou plusieurs lignes de facture.
9. Pour chaque ligne, renseignez :
   - la description ;
   - la quantité ;
   - le prix unitaire.
10. Vérifiez le total calculé automatiquement.
11. Cliquez sur `Enregistrer`.

### Retrouver une facture

L'écran `Factures clients` permet ensuite de filtrer la liste par :

- statut ;
- année ;
- recherche libre.

La liste affiche notamment le numéro, la date, le contact, le type, le total et le statut.

### Actions disponibles sur une facture

Depuis la ligne d'une facture, vous pouvez :

- ouvrir l'historique de la facture ;
- enregistrer un règlement ;
- modifier la facture ;
- générer un PDF ;
- envoyer la facture par e-mail ;
- dupliquer la facture ;
- supprimer la facture.

### Lire l'historique d'une facture

L'historique de facture permet de visualiser rapidement :

- le total facturé ;
- le montant déjà réglé ;
- le restant dû ;
- la liste des paiements rattachés à cette facture.

Depuis cette fenêtre, vous pouvez aussi enregistrer un nouveau règlement tant qu'il reste un solde à percevoir.

### Résultat attendu

La facture apparaît dans le portefeuille client avec son statut et son total. Si des paiements y sont rattachés, l'historique montre ce qui a déjà été encaissé et ce qu'il reste à percevoir.

### Points d'attention

- Une facture sans ligne utile n'est pas exploitable : prenez le temps de vérifier la description et les montants.
- Si vous voulez envoyer la facture par e-mail, assurez-vous que le contact dispose d'une adresse e-mail exploitable.
- Le statut évolue selon les paiements associés à la facture.

## 5. Consulter et suivre les paiements clients

### Objectif

Vérifier les paiements déjà enregistrés, suivre les règlements par facture ou par contact, et contrôler ce qui reste à remettre en banque.

### Saisir un paiement client

Le parcours standard consiste à enregistrer depuis la facture client les règlements en `Espèces` et en `Chèque`.

1. Ouvrez `Factures clients`.
2. Repérez la facture à régler.
3. Cliquez sur `Enregistrer un règlement` depuis la ligne ou depuis l'historique de la facture.
4. Vérifiez la date proposée et ajustez-la si nécessaire.
5. Renseignez le montant encaissé.
6. Choisissez le mode de règlement : `Espèces` ou `Chèque`.
7. Si vous saisissez un chèque, renseignez le numéro de chèque.
8. Ajoutez si besoin une référence ou une note.
9. Cliquez sur `Enregistrer`.

Les `Virements` suivent un autre point d'entrée : ils doivent être constatés depuis le relevé bancaire, puis rapprochés du bon paiement.

### Effet selon le mode de règlement

- `Espèces` : le paiement est enregistré et apparaît immédiatement dans le journal `Caisse`.
- `Chèque` : le paiement est enregistré, mais reste en attente d'une remise manuelle en banque.

Ce comportement permet de distinguer clairement l'encaissement réel du dépôt bancaire, surtout pour les chèques et les dépôts d'espèces.

### Consulter les paiements d'une facture

1. Ouvrez `Factures clients`.
2. Sur la facture voulue, cliquez sur le bouton d'historique.
3. Vérifiez la liste des paiements associés, avec leur date, leur montant, leur mode de règlement et, le cas échéant, leur numéro de chèque.

### Consulter les paiements d'un contact

1. Ouvrez `Contacts`.
2. Ouvrez l'historique du contact.
3. Consultez la section `Paiements` pour voir les règlements rattachés à ce contact.

### Consulter l'ensemble des paiements

1. Ouvrez `Paiements` dans le menu principal.
2. Utilisez si besoin le filtre `À remettre en banque` pour vous concentrer sur les paiements non encore remis.
3. Utilisez la recherche pour retrouver rapidement une ligne.
4. Lisez les principales colonnes :
   - date ;
   - montant ;
   - mode de règlement ;
   - numéro de chèque ;
   - statut de remise en banque.

### Résultat attendu

Vous pouvez répondre à trois questions simples :

1. quel paiement est rattaché à quelle facture ;
2. quel contact a déjà réglé et combien ;
3. quels paiements ne sont pas encore remis en banque.

### Points d'attention

- Un paiement supprimé peut modifier automatiquement le statut de la facture associée.
- Les chèques non remis en banque sont à surveiller de près, notamment avant une remise.
- Une remise d'espèces en banque crée un mouvement de sortie dans la caisse au moment du dépôt, en plus du mouvement d'entrée enregistré lors de l'encaissement.

## 6. Saisir et suivre une facture fournisseur

### Objectif

Enregistrer une facture fournisseur, retrouver rapidement sa référence et joindre son justificatif.

### Quand utiliser cet écran

Utilisez `Factures fournisseurs` pour :

- saisir une facture reçue ;
- suivre les échéances et les statuts ;
- rattacher un justificatif à la facture ;
- retrouver une référence fournisseur.

### Créer une facture fournisseur

1. Ouvrez `Factures fournisseurs` dans le menu principal.
2. Cliquez sur `Nouvelle facture`.
3. Sélectionnez le fournisseur concerné dans le champ `Contact`.
4. Renseignez la `Date` et, si besoin, l'`Échéance`.
5. Saisissez la `Référence fournisseur`.
6. Saisissez le `Total`.
7. Ajoutez une `Description` si elle est utile.
8. Cliquez sur `Enregistrer`.

### Retrouver et filtrer une facture fournisseur

L'écran permet de filtrer par :

- statut ;
- année ;
- recherche libre.

La liste affiche le numéro, la date, le contact, la référence, le total, le statut et la présence éventuelle d'un fichier joint.

### Joindre un justificatif

1. Repérez la facture dans la liste.
2. Cliquez sur le bouton de téléversement.
3. Choisissez un fichier compatible, par exemple `PDF`, `JPG`, `PNG` ou `WEBP`.
4. Cliquez sur `Enregistrer` dans la boîte de dialogue.

### Résultat attendu

La facture fournisseur apparaît dans le portefeuille fournisseur avec sa référence, son montant et, si vous l'avez ajouté, un indicateur de pièce jointe.

### Points d'attention

- Contrairement aux factures clients, la saisie fournisseur repose sur un montant global, pas sur des lignes détaillées.
- Vérifiez la référence fournisseur dès la saisie : c'est souvent le repère le plus utile pour retrouver un document.

## 7. Gérer la caisse

### Objectif

Suivre les mouvements d'espèces et enregistrer les comptages physiques de caisse.

### Ce que contient l'écran `Caisse`

L'écran est organisé en deux onglets :

- `Journal` pour les mouvements de caisse ;
- `Comptages` pour les vérifications physiques de caisse.

En haut de l'écran, Solde affiche notamment :

- le solde de caisse ;
- le nombre de mouvements visibles ;
- le nombre de comptages visibles.

### Ajouter un mouvement de caisse

1. Ouvrez `Caisse`.
2. Cliquez sur `Nouvelle écriture`.
3. Saisissez la `Date`.
4. Choisissez le type de mouvement : entrée ou sortie.
5. Saisissez le `Montant`.
6. Renseignez la `Description`.
7. Cliquez sur `Enregistrer`.

### Lire le journal de caisse

Le journal de caisse vous permet de contrôler :

- la date du mouvement ;
- son sens ;
- son montant ;
- sa description ;
- le solde après mouvement.

### Enregistrer un comptage de caisse

1. Cliquez sur `Nouveau comptage`.
2. Saisissez la date du comptage.
3. Renseignez le nombre de billets et pièces pour chaque valeur proposée.
4. Ajoutez une note si vous devez garder un commentaire.
5. Cliquez sur `Enregistrer`.

### Résultat attendu

Vous pouvez comparer le total compté avec le solde attendu et repérer immédiatement un écart positif, nul ou négatif.

### Points d'attention

- Le comptage est un contrôle, pas seulement une saisie : servez-vous-en pour expliquer un écart éventuel dans les notes.
- Le filtre de recherche unique s'applique aux listes visibles et facilite la revue rapide d'un mouvement ou d'un comptage.

## 8. Gérer la banque et les remises

### Objectif

Suivre les transactions bancaires, importer un relevé simple, enregistrer des remises et contrôler les paiements encore en attente de dépôt.

### Ce que contient l'écran `Banque`

L'écran comporte deux onglets :

- `Relevé de compte` pour les mouvements bancaires ;
- `Bordereaux de remise` pour les dépôts de chèques ou d'espèces.

Les actions principales disponibles en haut de page sont :

- `Importer CSV` ;
- `Nouveau bordereau` ;
- `Nouvelle opération`.

### Ajouter une transaction bancaire manuelle

1. Ouvrez `Banque`.
2. Cliquez sur `Nouvelle opération`.
3. Saisissez la date, le montant, la description, la référence et le solde après opération.
4. Cliquez sur `Enregistrer`.

### Importer un relevé CSV simple

1. Cliquez sur `Importer CSV`.
2. Collez le contenu attendu dans la zone prévue.
3. Lancez l'import.
4. Vérifiez ensuite la liste des transactions importées.

### Lettrer une transaction bancaire

Dans l'onglet `Relevé de compte`, utilisez l'action `Lettrer` sur la ligne pour marquer une opération non lettrée comme lettrée.

### Créer une remise

1. Cliquez sur `Nouveau bordereau`.
2. Renseignez la date de remise.
3. Choisissez le type de remise : chèques ou espèces.
4. Renseignez si besoin la référence bancaire.
5. Sélectionnez un ou plusieurs paiements en attente.
6. Cliquez sur `Enregistrer`.

### Résultat attendu

Vous pouvez suivre les transactions de banque, savoir quelles opérations sont rapprochées, et grouper des paiements en remises traçables.

### Points d'attention

- Une remise ne peut être créée que s'il existe des paiements non encore remis en banque.
- Le compteur de paiements en attente de remise est un bon repère pour la préparation des dépôts.

## 9. Utiliser l'import Excel

### Objectif

Prévisualiser puis lancer un import `Gestion` ou `Comptabilité` en comprenant les messages de contrôle avant validation.

### Ce que permet l'écran `Import Excel`

L'écran d'import permet de :

- choisir un type d'import ;
- sélectionner un fichier Excel ;
- lancer une prévisualisation ;
- vérifier les compteurs estimés ;
- lire les avertissements et blocages ;
- confirmer l'import si le résultat est jugé satisfaisant.

### Procédure recommandée

1. Ouvrez `Import Excel`.
2. Choisissez le type `Gestion` ou `Comptabilité`.
3. Sélectionnez le fichier Excel.
4. Cliquez sur `Prévisualiser`.
5. Lisez l'état général : prêt, sans effet utile, ou bloqué.
6. Contrôlez les compteurs estimés, les feuilles reconnues, les avertissements et les erreurs.
7. Si des avertissements existent mais que l'import reste autorisé, cochez la case de confirmation demandée.
8. Cliquez sur le bouton d'import pour lancer le traitement.

### Comment lire la prévisualisation

La prévisualisation affiche notamment :

- les volumes estimés de contacts, factures, paiements et écritures ;
- la liste des feuilles reconnues ;
- les colonnes détectées ou manquantes ;
- les lignes ignorées ;
- les lignes bloquantes.

### Résultat attendu

Vous savez avant import si le fichier est acceptable, ce qui sera probablement créé, et quelles anomalies doivent être traitées d'abord.

### Pour aller plus loin

Pour le détail complet sur les types d'import, la réinitialisation, l'ordre conseillé de reprise historique et les messages fréquents, consultez aussi le guide complémentaire [Import Excel et réinitialisation](./import-excel-et-reinitialisation.md).

### Points d'attention

- La prévisualisation doit rester votre étape de contrôle principale avant tout import réel.
- Si l'état est bloqué, il faut corriger le problème avant de relancer l'import.

## 10. Consulter les écrans comptables

### Objectif

Savoir à quoi servent les principaux écrans comptables et où aller selon la question que vous vous posez.

### Journal comptable

Utilisez `Journal` pour consulter les écritures comptables avec filtres par période, compte, source et exercice.

Cet écran permet aussi :

- d'exporter en CSV ;
- de créer une écriture manuelle simple avec un compte au débit, un compte au crédit, un montant et un libellé.

### Balance

Utilisez `Balance` pour obtenir une vue synthétique des comptes avec :

- numéro de compte ;
- libellé ;
- type de compte ;
- total débit ;
- total crédit ;
- solde.

Elle est utile pour contrôler rapidement la situation d'un ensemble de comptes sur une période ou un exercice.

### Grand livre

Utilisez `Grand livre` quand vous voulez analyser un seul compte en détail.

Vous pouvez :

- choisir un compte ;
- filtrer par dates ;
- lancer la recherche ;
- lire le solde d'ouverture, le solde de clôture et le détail des lignes.

### Compte de résultat

Utilisez `Compte de résultat` pour consulter les charges, les produits et le résultat sur un exercice donné.

### Bilan

Utilisez `Bilan` pour consulter l'actif et le passif de l'exercice sélectionné, avec possibilité d'export CSV.

### Plan comptable

Utilisez `Plan comptable` pour :

- consulter les comptes existants ;
- filtrer par type ;
- créer un compte ;
- modifier un compte ;
- utiliser `Pré-remplir` pour charger les comptes par défaut.

### Exercices

Utilisez `Exercices` pour :

- lister les exercices comptables ;
- créer un exercice ;
- clôturer un exercice ouvert quand c'est nécessaire.

### Résultat attendu

Vous savez vers quel écran vous diriger selon que vous cherchez une écriture précise, une synthèse par compte, le détail d'un compte, le résultat d'un exercice ou la structure comptable de base.

### Points d'attention

- Les écrans comptables ne servent pas tous au même niveau de lecture : commencez par la `Balance` ou le `Journal`, puis descendez au `Grand livre` si vous avez besoin du détail d'un compte.
- La création d'écritures manuelles dans le `Journal` doit rester maîtrisée, car elle a un impact direct sur la comptabilité.

## 11. Questions fréquentes

### Pourquoi je ne vois pas certains écrans ?

Certains écrans ou certaines actions dépendent de votre rôle utilisateur. Les écrans d'administration ne sont pas visibles pour tous les profils.

### Où modifier mon e-mail ou mon mot de passe ?

Utilisez l'écran `Mon profil`, accessible depuis le menu principal. Vous pouvez y mettre à jour votre e-mail de contact et changer votre mot de passe en renseignant le mot de passe actuel.

### J'ai oublié mon mot de passe, que faire ?

Demandez à un administrateur de réinitialiser temporairement votre accès depuis l'écran `Utilisateurs`. Une fois reconnecté, changez immédiatement ce mot de passe temporaire depuis `Mon profil`.

### Pourquoi une facture n'apparaît pas comme payée ?

Le statut dépend des paiements réellement rattachés à cette facture. Vérifiez l'historique de la facture et la présence des paiements attendus.

### Pourquoi je ne peux pas créer de remise ?

Une remise nécessite au moins un paiement encore non remis en banque. Si la liste est vide, il n'y a rien à déposer dans l'état actuel de l'application.

### Pourquoi l'import Excel est-il bloqué ?

La prévisualisation signale les colonnes manquantes, lignes ambiguës ou erreurs bloquantes. Tant que ces points ne sont pas résolus, l'import doit rester bloqué.

### Où saisir un paiement manuellement ?

L'écran `Paiements` permet aujourd'hui surtout la consultation, le filtrage et la suppression. Le parcours standard de saisie manuelle d'un paiement n'est pas encore exposé comme formulaire dédié dans cet écran principal.

### Que se passe-t-il après un changement de mot de passe ?

Les anciennes sessions sont invalidées. Reconnectez-vous simplement avec votre nouveau mot de passe.

## 12. Glossaire simple

### Exercice comptable

Période de référence de la comptabilité, par exemple une année associative.

### Facture client

Document émis par l'association pour demander un règlement à un client.

### Facture fournisseur

Document reçu d'un fournisseur pour une dépense de l'association.

### Paiement

Règlement rattaché à une facture ou à un flux de gestion, par chèque, espèces ou virement.

### Remise

Dépôt en banque d'un ensemble de paiements, par exemple un lot de chèques ou d'espèces.

### Journal comptable

Liste détaillée des écritures comptables.

### Balance

Vue synthétique qui présente, pour chaque compte, les débits, crédits et soldes.

### Grand livre

Vue détaillée des mouvements d'un compte précis sur une période.

### Compte de résultat

État qui compare les charges et les produits pour mesurer le résultat d'un exercice.

### Bilan

État qui présente l'actif et le passif à une date ou sur un exercice.

### Plan comptable

Liste structurée des comptes utilisés par l'association.

## Suite du manuel

La prochaine étape consiste surtout à enrichir cette version texte avec des captures d'écran homogènes, des encadrés d'alerte plus visibles et une finition éditoriale globale.