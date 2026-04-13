# Gestion des utilisateurs et des permissions

## Objectif

BL-022 lots 1 et 2 clarifient la cible produit des rôles sans renommer immédiatement les valeurs techniques déjà utilisées dans l'API et les autorisations backend.

L'objectif est double :

1. rendre les rôles compréhensibles pour l'administrateur fonctionnel ;
2. ajouter une administration des comptes cohérente avec les permissions déjà en place.

## Principe retenu

Les valeurs techniques existantes restent inchangées dans ce lot :

- `readonly`
- `secretaire`
- `tresorier`
- `admin`

En revanche, elles sont interprétées côté produit avec des libellés métier plus lisibles.

## Correspondance rôles techniques / rôles métier

| Valeur technique | Libellé métier | Usage principal |
|---|---|---|
| `readonly` | Consultation | Lire les données sans modifier l'application |
| `secretaire` | Gestionnaire | Gérer les contacts, factures et paiements |
| `tresorier` | Comptable | Gérer la trésorerie, la comptabilité, les imports et les salaires |
| `admin` | Administrateur | Gérer les comptes, les paramètres et l'ensemble de l'application |

## Matrice simplifiée des permissions

| Zone / action | Consultation | Gestionnaire | Comptable | Administrateur |
|---|---|---|---|---|
| Se connecter et consulter les écrans | Oui | Oui | Oui | Oui |
| Modifier contacts, factures et paiements | Non | Oui | Oui | Oui |
| Modifier caisse, banque, imports, salaires et comptabilité | Non | Non | Oui | Oui |
| Gérer les paramètres de l'application | Non | Non | Non | Oui |
| Gérer les comptes utilisateurs | Non | Non | Non | Oui |

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
- une refonte complète du modèle de rôles côté backend.

## Garde-fous retenus

Pour éviter une perte d'accès administrative dans ce lot :

- un administrateur ne peut pas se désactiver lui-même ;
- un administrateur ne peut pas se retirer lui-même son rôle d'administration ;
- le dernier administrateur actif ne peut pas être désactivé ni rétrogradé.