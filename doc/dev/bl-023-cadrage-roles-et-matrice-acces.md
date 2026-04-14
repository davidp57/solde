# BL-023 — Cadrage des rôles et de la matrice d'accès

## Objectif

Avant de modifier les permissions, il faut clarifier la cible produit des rôles et distinguer trois choses qui sont aujourd'hui mélangées :

- la matrice documentée dans `BL-022` ;
- la matrice réellement appliquée par le backend ;
- la visibilité réellement exposée par le frontend.

Ce document sert de base de discussion pour décider la cible, puis encadrer une implémentation ultérieure sans corriger "au feeling" un symptôme à la fois.

## Décisions produit validées le 2026-04-14

Les arbitrages suivants sont désormais actés :

- `admin` voit tout, édite tout et gère l'application, y compris `utilisateurs`, `paramètres` et les autres fonctions transverses ;
- `tresorier` garde sa valeur technique actuelle mais doit être présenté comme `Comptable` dans le produit ;
- `Comptable` voit et édite toute la partie `Gestion` et toute la partie `Comptabilité` ;
- `secretaire` garde sa valeur technique actuelle mais doit être présenté comme `Gestionnaire` dans le produit ;
- `Gestionnaire` voit et édite toute la partie `Gestion` ;
- `readonly` n'a pas de vraie utilité produit à ce stade ; il peut rester comme valeur technique legacy ou transitoire, mais il n'entre plus dans la cible fonctionnelle active à mettre en avant dans l'interface et la matrice principale ;
- l'interface doit séparer visiblement les zones `Gestion` et `Comptabilité`.

## Structure UI validée

La navigation cible doit être organisée au minimum en deux sections visuellement distinctes.

### Partie Gestion

- `Tableau de bord`
- `Contacts`
- `Factures clients`
- `Factures fournisseurs`
- `Paiements`
- `Banque`
- `Caisse`

### Partie Comptabilité

- `Exercices`
- `Plan comptable`
- `Règles comptables`
- `Bilan`
- `Résultat`
- `Journal`
- `Balance`
- `Grand livre`

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

## Cible produit validée

### Principe directeur retenu

Le modèle cible s'appuie sur trois rôles produit actifs :

- `Gestionnaire`
- `Comptable`
- `Administrateur`

Le rôle technique `readonly` n'est pas retenu comme rôle produit utile dans la cible actuelle. Il peut être conservé techniquement tant que nécessaire pour éviter une migration brutale, mais il ne doit plus structurer la conception fonctionnelle principale.

### Matrice cible validée

| Zone / action | Gestionnaire | Comptable | Administrateur |
|---|---|---|---|
| Tableau de bord | Lecture + écriture métier associée | Lecture + écriture métier associée | Lecture + écriture métier associée |
| Contacts | Lecture + écriture | Lecture + écriture | Lecture + écriture |
| Factures client / fournisseur | Lecture + écriture | Lecture + écriture | Lecture + écriture |
| Paiements | Lecture + écriture | Lecture + écriture | Lecture + écriture |
| Banque | Lecture + écriture | Lecture + écriture | Lecture + écriture |
| Caisse | Lecture + écriture | Lecture + écriture | Lecture + écriture |
| Exercices | Non | Lecture + écriture | Lecture + écriture |
| Plan comptable | Non | Lecture + écriture | Lecture + écriture |
| Règles comptables | Non | Lecture + écriture | Lecture + écriture |
| Bilan | Non | Lecture | Lecture |
| Résultat | Non | Lecture | Lecture |
| Journal | Non | Lecture | Lecture |
| Balance | Non | Lecture | Lecture |
| Grand livre | Non | Lecture | Lecture |
| Imports Excel | Non | Lecture + écriture | Lecture + écriture |
| Salaires | Non | Lecture + écriture | Lecture + écriture |
| Utilisateurs | Non | Non | Lecture + écriture |
| Paramètres | Non | Non | Lecture + écriture |

### Conséquences explicites de cette décision

- `Gestionnaire` couvre toute la partie `Gestion`, y compris `banque` et `caisse` ;
- `Comptable` est un sur-ensemble fonctionnel du `Gestionnaire`, avec accès complet à la partie `Comptabilité` ;
- `Administrateur` est un sur-ensemble du `Comptable` et porte en plus la gestion de l'application ;
- la séparation UI `Gestion` / `Comptabilité` devient une exigence produit, pas seulement une préférence ergonomique ;
- toute présence future de `readonly` devra être traitée comme un cas de compatibilité ou d'administration avancée, pas comme un rôle central de la cible métier.

## Questions restantes avant implémentation

Les arbitrages produit principaux étant maintenant faits, les points restants sont surtout d'implémentation :

1. faut-il masquer complètement `readonly` dans l'UI d'administration tant que son utilité produit n'est pas redéfinie ;
2. comment structurer visuellement la navigation pour matérialiser `Gestion` et `Comptabilité` sans alourdir l'usage quotidien ;
3. comment traiter exactement la zone utilisateur du shell et le sélecteur global d'exercice selon le rôle et la section courante.

## Principes d'implémentation à respecter ensuite

Quand la matrice sera validée, l'implémentation devra respecter ces règles :

1. le backend reste la source de vérité des permissions ;
2. le frontend masque les menus et routes non autorisés, mais ne remplace pas les contrôles backend ;
3. les helpers frontend doivent exposer une matrice explicite par capacité, pas seulement `isAdmin` et `isTresorier` ;
4. les tests backend doivent couvrir les refus `403` par rôle pour les zones sensibles ;
5. les tests frontend doivent couvrir la visibilité du menu, des routes gardées, du sélecteur d'exercice et de la zone utilisateur du shell.

## Découpage recommandé pour la suite

### Étape 1 — backend

Aligner les dépendances `require_role(...)` et compléter les tests d'autorisation par domaine.

### Étape 2 — frontend

Aligner le menu, les guards, les helpers d'autorisation, la visibilité du sélecteur d'exercice et le rendu stable de la zone utilisateur.

### Étape 3 — documentation

Mettre à jour `doc/dev/gestion-utilisateurs-et-permissions.md` pour refléter la matrice finale effectivement implémentée.