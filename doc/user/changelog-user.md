# Nouveautés de Solde ⚖️

Ce document présente les changements visibles dans l'application, version par version.

---

## Version 1.4 *(à venir)*

### Tous les utilisateurs

#### Confort de navigation
- Les listes affichent désormais **50 lignes par défaut** (au lieu de 20) — moins de clics pour parcourir les données.
- Un message d'avertissement s'affiche quand une liste dépasse 1 000 résultats, pour signaler qu'il faut affiner les filtres.

### Secrétaire

#### Saisie des factures
- Dans les lignes d'une facture, la **virgule est acceptée** comme séparateur décimal (elle est automatiquement convertie en point).
- La **première lettre** d'un libellé de prestation est **mise en majuscule automatiquement** dès qu'on passe au champ suivant.

---

## Version 1.3.0 — 2 mai 2026

### Tous les utilisateurs

#### Tableau de bord
- Les **bordereaux de dépôt en attente** sont désormais visibles directement depuis le tableau de bord, sans avoir à ouvrir la vue Banque.

### Secrétaire

#### Contacts
- Possibilité d'enregistrer **jusqu'à 2 adresses e-mail supplémentaires** par contact, avec un libellé libre (ex. « autre parent »).
- La recherche de contacts porte maintenant sur les noms de l'enfant et de l'autre parent.
- Marquage **« client indésirable »** : badge rouge dans la liste, et blocage de la création de facture tant que le marquage est actif.

#### Assistant de création de facture rapide
- L'étape de confirmation affiche maintenant le **nom complet du contact** concerné.
- Un bouton **« Envoyer par e-mail »** est disponible directement dans la confirmation, avec un badge « E-mail envoyé » après envoi.
- Lors de l'envoi d'une facture, les **adresses e-mail secondaires** du contact apparaissent avec des cases à cocher pour choisir les destinataires.

### Trésorier

#### Paiements et remises en banque
- La colonne « Remis en banque » distingue maintenant **trois états** : ✓ remis / ⏱ en cours de dépôt (orange) / ✗ à remettre.
- Un bouton **« Tout sélectionner / Tout désélectionner »** facilite la création d'un bordereau de chèques.
- Nouveau panneau **« Dépôts en attente »** dans la vue Banque : liste les bordereaux préparés mais pas encore confirmés, avec un bouton « Confirmer » par bordereau.
- Le tableau des dépôts affiche une colonne **Statut** (en attente / confirmé) avec filtre.
- Le total d'un bordereau d'espèces ne compte plus les pièces (seuls les billets sont déposables).

#### Factures fournisseur
- Nouveau **dialogue de prévisualisation** : historique des règlements, aperçu du PDF ou de l'image jointe, navigation entre factures précédente/suivante. Accessible aussi depuis l'historique d'un contact.
- Bouton **« Enregistrer un règlement »** disponible dans la liste des factures fournisseur et dans la prévisualisation.
- Un règlement fournisseur en espèces génère automatiquement une **sortie de caisse** correspondante.
- Les factures fournisseur créées manuellement démarrent avec le statut **« Envoyée »** (au lieu de « Brouillon »).

#### Caisse
- Comptage de caisse : le total des pièces se saisit dans un **champ unique** « Pièces (ferraille) » au lieu de chaque coupure.
- Les paiements en espèces reçus entrent **immédiatement** dans la caisse. La sortie caisse (vers la banque) n'est générée qu'à la confirmation du bordereau.

#### Banque et relevés
- Une **icône crayon** sur chaque transaction du relevé permet de corriger la catégorie détectée automatiquement.
- Deux nouveaux boutons sur le relevé : **« Tout rapprocher »** et **« Rapprocher avant le… »** pour valider plusieurs transactions en une fois.
- Le rapprochement génère désormais automatiquement les **écritures comptables** correspondantes selon la catégorie (frais bancaires, charges sociales, subventions, virements internes).
- La colonne Référence du relevé affiche la référence comptable lisible (plus jamais un code technique interne).
- La source d'un import bancaire est maintenant précise : Excel, CSV, OFX ou QIF.
- Les transactions déjà importées sont silencieusement ignorées (pas de doublons).
- Un fichier OFX contenant plusieurs comptes bancaires est refusé avec un message d'erreur clair.

#### Salaires
- Les écritures comptables de salaires sont désormais datées au **dernier jour du mois** (correction d'une erreur de date).

### Administrateur

#### Sauvegardes
- Le libellé d'une sauvegarde peut contenir jusqu'à **100 caractères** (au lieu de 50).
- Un message de confirmation s'affiche dans l'interface après chaque sauvegarde réussie.

---

## Version 1.2.1 — 2 mai 2026

### Tous les utilisateurs

#### Aperçus PDF
- L'aperçu des factures PDF fonctionne maintenant correctement dans Chrome et Firefox.

---

## Version 1.1.0 — 28 avril 2026

### Secrétaire / Trésorier

#### Paramètres
- Les gestionnaires (trésorier) peuvent désormais **consulter les paramètres** de l'association en lecture seule (modification réservée aux administrateurs).

#### Contacts
- Nouvelles informations sur la fiche contact : **prénom/nom de l'enfant** et **prénom/nom de l'autre parent**.
- La recherche de contacts porte sur ces nouveaux champs.

#### Factures client
- La **date du jour est pré-remplie** à la création d'une nouvelle facture.
- L'édition d'une facture est **bloquée** si elle a déjà été envoyée avec un paiement partiel, ou si elle est entièrement payée.
- Le dialogue de paiement affiche le **nom du client, la description, le montant total et l'échéance** de la facture.

#### PDF des factures
- Les **instructions de règlement** (IBAN, BIC, numéro de chèque à l'ordre de) sont ajoutées en pied de facture.

#### Notes internes
- Tous les utilisateurs peuvent saisir des **notes internes** via la page Aide (bouton « Ajouter une note »).

### Trésorier

#### Paiements et remises en banque
- Nouveau statut intermédiaire pour les chèques : **« en bordereau »** (entre la création du bordereau et sa confirmation).
- Bouton **« Tout sélectionner / Tout désélectionner »** dans le dialogue de création de bordereau.
- La colonne « Remis en banque » distingue les trois états.
- Le compteur de paiements non remis sur le tableau de bord exclut les chèques déjà en bordereau.

#### Dépôts et caisse
- Nouveau bouton **« Confirmer »** pour valider un bordereau de dépôt.
- Panneau **« Dépôts en attente »** dans la vue Banque.

### Administrateur

#### Notes internes
- Les administrateurs voient **tous les commentaires** de tous les utilisateurs depuis la section Administration.
- Possibilité de **marquer une note comme résolue** ou de la supprimer.
