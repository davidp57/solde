# Manuel utilisateur - lot 1

## Objectif du guide

Ce premier lot du manuel utilisateur aide à prendre en main Solde pour les parcours les plus courants : se connecter, se repérer dans l'application, gérer les contacts, créer une facture client et suivre les paiements déjà enregistrés.

Ce document décrit les écrans actuellement disponibles. Les captures d'écran seront ajoutées dans une phase ultérieure, quand l'interface sera stabilisée.

## Périmètre de cette version

Ce lot couvre :

1. la connexion ;
2. les repères de navigation ;
3. la gestion des contacts ;
4. la création et le suivi des factures clients ;
5. la consultation et le suivi des paiements clients.

Ce lot ne couvre pas encore :

- les achats fournisseurs ;
- la caisse ;
- la banque et les remises ;
- l'import Excel ;
- les écrans comptables avancés.

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
- Si un message indique que le serveur est inaccessible, il s'agit plutôt d'un problème technique ou réseau.

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

### Résultat attendu

La facture apparaît dans le portefeuille client avec son statut et son total. Si des paiements y sont rattachés, l'historique montre ce qui a déjà été encaissé et ce qu'il reste à percevoir.

### Points d'attention

- Une facture sans ligne utile n'est pas exploitable : prenez le temps de vérifier la description et les montants.
- Si vous voulez envoyer la facture par e-mail, assurez-vous que le contact dispose d'une adresse e-mail exploitable.
- Le statut évolue selon les paiements associés à la facture.

## 5. Consulter et suivre les paiements clients

### Objectif

Vérifier les paiements déjà enregistrés, suivre les règlements par facture ou par contact, et contrôler ce qui reste à remettre en banque.

### Ce que permet l'application aujourd'hui

Dans l'interface actuellement disponible, l'écran `Paiements` sert surtout à consulter, filtrer et supprimer un paiement existant. Il n'expose pas encore un formulaire dédié pour créer ou modifier un paiement depuis cet écran principal.

Autrement dit, le suivi des paiements est bien visible, mais la saisie manuelle directe d'un paiement dans l'interface principale n'est pas encore documentée ici car elle n'est pas exposée comme parcours utilisateur standard.

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
- Pour la création ou l'édition directe d'un paiement via l'interface, il faudra documenter un lot ultérieur quand ce parcours sera exposé de façon standard.

## Suite du manuel

Les prochains lots compléteront ce guide avec les achats fournisseurs, la caisse, la banque, l'import Excel, les écrans comptables, puis les captures d'écran harmonisées.