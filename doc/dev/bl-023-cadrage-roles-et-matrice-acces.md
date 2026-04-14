# BL-023 — Cadrage des rôles et de la matrice d'accès

## Objectif

Avant de modifier les permissions, il faut clarifier la cible produit des rôles et distinguer trois choses qui sont aujourd'hui mélangées :

- la matrice documentée dans `BL-022` ;
- la matrice réellement appliquée par le backend ;
- la visibilité réellement exposée par le frontend.

Ce document sert de base de discussion pour décider la cible, puis encadrer une implémentation ultérieure sans corriger "au feeling" un symptôme à la fois.

## État actuel vérifié

### Rôles techniques existants

Les rôles techniques actuellement utilisés dans le code sont :

- `readonly`
- `secretaire`
- `tresorier`
- `admin`

Le document existant `doc/dev/gestion-utilisateurs-et-permissions.md` les présente déjà côté produit comme :

- `readonly` -> `Consultation`
- `secretaire` -> `Gestionnaire`
- `tresorier` -> `Comptable`
- `admin` -> `Administrateur`

### Matrice effectivement appliquée par le backend

Le backend applique aujourd'hui une règle simple par domaine :

| Zone backend | Lecture | Écriture |
|---|---|---|
| Contacts | tout utilisateur authentifié | `secretaire`, `tresorier`, `admin` |
| Factures | tout utilisateur authentifié | `secretaire`, `tresorier`, `admin` |
| Paiements | tout utilisateur authentifié | `secretaire`, `tresorier`, `admin` |
| Banque | tout utilisateur authentifié | `tresorier`, `admin` |
| Caisse | tout utilisateur authentifié | `tresorier`, `admin` |
| Comptabilité (journal, balance, grand livre, comptes, règles, exercices) | tout utilisateur authentifié | `tresorier`, `admin` |
| Imports Excel | pas de lecture dédiée aujourd'hui | `tresorier`, `admin` |
| Salaires | tout utilisateur authentifié | `tresorier`, `admin` |
| Paramètres | `admin` | `admin` |
| Utilisateurs | `admin` | `admin` |

Conséquence directe : côté API, un utilisateur `readonly` peut déjà lire les écrans comptables, la banque, la caisse et les salaires si le frontend lui donne accès aux vues correspondantes.

### Visibilité effectivement appliquée par le frontend

Le frontend est aujourd'hui plus permissif que la matrice produit documentée :

- tous les utilisateurs authentifiés voient la quasi-totalité des entrées du menu principal ;
- seuls `Utilisateurs` et `Paramètres` sont masqués aux non-admins ;
- seules les routes `settings` et `users` sont explicitement gardées côté routeur via `requiresAdmin` ;
- les autres vues sont donc accessibles par navigation directe tant que le backend autorise la lecture ;
- la zone utilisateur du shell repose sur `auth.user` et fait apparaître un symptôme intermittent de disparition du nom d'utilisateur et du bouton de déconnexion.

Conséquence directe : la matrice perçue par l'utilisateur dépend aujourd'hui plus du menu et des lectures backend implicites que d'une matrice de permissions explicitement décidée.

## Écart principal à traiter

Le document `BL-022` décrit une séparation produit intuitive :

- `Consultation` lit sans modifier ;
- `Gestionnaire` gère les flux métier `contacts`, `factures`, `paiements` ;
- `Comptable` gère trésorerie, comptabilité, imports et salaires ;
- `Administrateur` gère comptes et paramètres.

Mais l'application actuelle ne traduit pas encore proprement cette cible :

- `readonly` lit aujourd'hui beaucoup plus que ce que laisse entendre le nom `Consultation` ;
- `secretaire` voit actuellement de nombreuses entrées comptables dans le shell ;
- la frontière exacte entre lecture comptable autorisée, lecture trésorerie autorisée et écriture métier n'est pas explicitement décidée ;
- le shell global expose des éléments transverses `menu`, `sélecteur d'exercice`, `zone utilisateur` sans matrice de visibilité clairement définie.

## Proposition de cible produit

### Principe directeur recommandé

La recommandation est de conserver les quatre rôles techniques existants dans un premier temps, mais d'expliciter une matrice produit stable par zone métier. Cela évite de cumuler deux chantiers en même temps :

- refonte des permissions ;
- renommage ou changement structurel du modèle de rôles.

### Matrice cible proposée pour discussion

| Zone / action | Consultation | Gestionnaire | Comptable | Administrateur |
|---|---|---|---|---|
| Tableau de bord | Lecture | Lecture | Lecture | Lecture |
| Contacts | Lecture | Lecture + écriture | Lecture + écriture | Lecture + écriture |
| Factures client / fournisseur | Lecture | Lecture + écriture | Lecture + écriture | Lecture + écriture |
| Paiements | Lecture | Lecture + écriture | Lecture + écriture | Lecture + écriture |
| Banque | Non | Lecture simple | Lecture + écriture | Lecture + écriture |
| Caisse | Non | Lecture simple | Lecture + écriture | Lecture + écriture |
| Journal / balance / grand livre / bilan / résultat | Non | Non | Lecture | Lecture |
| Plan comptable / règles comptables / exercices | Non | Non | Lecture + écriture | Lecture + écriture |
| Imports Excel | Non | Non | Lecture + écriture | Lecture + écriture |
| Salaires | Non | Non | Lecture + écriture | Lecture + écriture |
| Utilisateurs | Non | Non | Non | Lecture + écriture |
| Paramètres | Non | Non | Non | Lecture + écriture |

### Pourquoi cette proposition

- elle aligne `Gestionnaire` sur les flux métier quotidiens sans lui ouvrir toute la comptabilité ;
- elle laisse à `Comptable` la responsabilité de la comptabilité, de la trésorerie, des imports et des salaires ;
- elle conserve à `Administrateur` la capacité d'administration globale sans lui attribuer un rôle métier différent du `Comptable` sur les écrans fonctionnels ;
- elle rend enfin explicite un cas aujourd'hui flou : la lecture simple de `banque` et `caisse` pour `Gestionnaire`, qui peut être utile si l'on veut permettre une visibilité opérationnelle sans écriture.

## Points de décision à valider avec David

Les décisions produit qui restent ouvertes avant implémentation sont les suivantes :

1. `Consultation` doit-il voir uniquement les flux métier, ou aussi certains écrans comptables de synthèse comme la balance ou le résultat ?
2. `Gestionnaire` peut-il consulter `banque` et `caisse` en lecture simple, ou doit-il rester strictement limité à `contacts`, `factures`, `paiements` ?
3. `Administrateur` doit-il être un sur-ensemble complet du `Comptable`, ou seulement un rôle d'administration technique avec accès ponctuel aux écrans métier ?
4. Le sélecteur global d'exercice doit-il être visible seulement sur les écrans qui l'utilisent réellement, ou globalement pour tous les rôles qui ont accès à au moins un écran comptable ?

## Principes d'implémentation à respecter ensuite

Quand la matrice sera validée, l'implémentation devra respecter ces règles :

1. le backend reste la source de vérité des permissions ;
2. le frontend masque les menus et routes non autorisés, mais ne remplace pas les contrôles backend ;
3. les helpers frontend doivent exposer une matrice explicite par capacité, pas seulement `isAdmin` et `isTresorier` ;
4. les tests backend doivent couvrir les refus `403` par rôle pour les zones sensibles ;
5. les tests frontend doivent couvrir la visibilité du menu, des routes gardées, du sélecteur d'exercice et de la zone utilisateur du shell.

## Découpage recommandé pour la suite

### Étape 1 — arbitrage produit

Valider la matrice cible par zone et trancher les quatre questions ouvertes ci-dessus.

### Étape 2 — backend

Aligner les dépendances `require_role(...)` et compléter les tests d'autorisation par domaine.

### Étape 3 — frontend

Aligner le menu, les guards, les helpers d'autorisation, la visibilité du sélecteur d'exercice et le rendu stable de la zone utilisateur.

### Étape 4 — documentation

Mettre à jour `doc/dev/gestion-utilisateurs-et-permissions.md` pour refléter la matrice finale effectivement implémentée.