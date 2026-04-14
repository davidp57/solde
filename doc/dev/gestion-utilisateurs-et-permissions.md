# Gestion des utilisateurs et des permissions

## Objectif

BL-022 lots 1 et 2 ont introduit l'administration des comptes. BL-023 clarifie désormais la cible produit des rôles et la séparation visible entre `Gestion` et `Comptabilité`, sans renommer immédiatement les valeurs techniques déjà utilisées dans l'API et les autorisations backend.

L'objectif est double :

1. rendre les rôles compréhensibles pour l'administrateur fonctionnel ;
2. ajouter une administration des comptes cohérente avec les permissions déjà en place.

## Principe retenu

Les valeurs techniques existantes restent inchangées dans ce lot :

- `readonly`
- `secretaire`
- `tresorier`
- `admin`

En revanche, elles sont interprétées côté produit avec des libellés métier plus lisibles. La cible produit active repose désormais surtout sur trois rôles métier : `Gestionnaire`, `Comptable`, `Administrateur`.

## Correspondance rôles techniques / rôles métier

| Valeur technique | Libellé métier | Usage principal |
|---|---|---|
| `readonly` | Consultation | Rôle legacy ou transitoire, sans utilité produit claire à ce stade |
| `secretaire` | Gestionnaire | Gérer toute la partie gestion |
| `tresorier` | Comptable | Gérer la partie comptable et toute la partie gestion |
| `admin` | Administrateur | Gérer les comptes, les paramètres et l'ensemble de l'application |

## Sections UI cibles

La navigation doit séparer visiblement au moins deux sections :

### Gestion

- Tableau de bord
- Contacts
- Factures clients
- Factures fournisseurs
- Paiements
- Banque
- Caisse

### Comptabilité

- Exercices
- Plan comptable
- Règles comptables
- Bilan
- Résultat
- Journal
- Balance
- Grand livre

## Matrice simplifiée des permissions

| Zone / action | Gestionnaire | Comptable | Administrateur |
|---|---|---|---|
| Partie gestion | Lecture + écriture | Lecture + écriture | Lecture + écriture |
| Partie comptable | Non | Lecture + écriture ou lecture seule selon l'écran | Lecture + écriture ou lecture seule selon l'écran |
| Utilisateurs | Non | Non | Lecture + écriture |
| Paramètres de l'application | Non | Non | Lecture + écriture |

En pratique :

- `Gestionnaire` voit et édite toute la partie `Gestion` ;
- `Comptable` voit et édite toute la partie `Gestion`, et voit ou édite la partie `Comptabilité` selon l'écran concerné ;
- `Administrateur` voit tout, édite tout et gère l'application ;
- `readonly` n'est plus un rôle cible à mettre en avant dans le produit.

Précisions d'implémentation utiles :

- le tableau de bord reste accessible via une section `Accueil` distincte de la section `Gestion`, y compris pour le rôle technique legacy `readonly` ;
- le sélecteur global d'exercice reste visible pour les rôles métier actifs `Gestionnaire`, `Comptable` et `Administrateur`, car plusieurs écrans de gestion sont filtrés par exercice même hors section `Comptabilité` ;
- l'écran de gestion des exercices reste réservé à `Comptable` et `Administrateur` ;
- la carte `Exercice en cours` du tableau de bord suit la même logique que le sélecteur global : exercice ouvert couvrant la date du jour, sinon exercice ouvert le plus récent.

## Portée du lot 2

Le lot 2 ajoute l'administration des comptes avec les capacités suivantes :

- lister les comptes existants ;
- créer un compte ;
- changer le rôle d'un compte ;
- activer ou désactiver un compte.

Le lot 2 ne couvre pas encore :

- l'espace `Mon profil` ;
- le changement de mot de passe par l'utilisateur lui-même ;
- le mot de passe oublié ou la récupération d'accès ;
- l'alignement complet backend/frontend avec la nouvelle matrice BL-023.

## Garde-fous retenus

Pour éviter une perte d'accès administrative dans ce lot :

- un administrateur ne peut pas se désactiver lui-même ;
- un administrateur ne peut pas se retirer lui-même son rôle d'administration ;
- le dernier administrateur actif ne peut pas être désactivé ni rétrogradé.