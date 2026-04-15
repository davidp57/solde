# BL-026 — Cadrage de la validation chiffrée des imports Excel

## Objectif

Valider, sur la reprise réelle `2024` et `2025`, que les chiffres visibles dans Solde concordent avec les fichiers Excel sources :

- côté `Gestion` ;
- côté `Comptabilité` ;
- exercice par exercice ;
- avec une méthode de rapprochement explicite et réutilisable.

Ce document cadre la méthode de recette. Il ne définit pas encore un moteur générique de réconciliation automatisée.

## Faits vérifiés dans le code

### Imports et ordre de rejeu

- L'application expose bien quatre raccourcis de test pour `Gestion 2024`, `Gestion 2025`, `Comptabilité 2024` et `Comptabilité 2025`.
- La documentation existante recommande déjà l'ordre de rejeu suivant :
  1. `Gestion 2024`
  2. `Gestion 2025`
  3. `Comptabilité 2024`
  4. `Comptabilité 2025`
- Cet ordre reste la base de la validation `BL-026`, car certains rapprochements de paiements ne deviennent stables qu'après import de l'exercice précédent.

### Sources Solde exploitables

#### Sources primaires comptables

Les écrans et endpoints suivants sont directement exploitables comme sources primaires pour une validation par exercice, car ils acceptent un `fiscal_year_id` explicite :

- `Journal`
- `Balance`
- `Bilan`
- `Résultat`
- `Grand livre`

#### Sources primaires gestion

Les écrans et endpoints suivants sont exploitables comme sources primaires de gestion, mais par filtre de date ou d'année civile, pas par `fiscal_year_id` :

- `Factures clients`
- `Factures fournisseurs`
- `Paiements`
- `Banque`
- `Caisse`
- `Salaires`

Conséquence : pour la partie `Gestion`, la validation doit se faire sur le périmètre de dates exact des exercices, et non sur le seul nom de fichier `2024` ou `2025`.

#### Sources secondaires seulement

Les éléments suivants sont utiles comme contrôle rapide ou sanity check, mais ne doivent pas servir de preuve principale pour `BL-026` :

- `Dashboard`, car ses KPI ne sont pas filtrés par exercice ;
- les bandeaux de résultat d'import, car ils reflètent l'opération d'import, pas l'état final consolidé de l'application ;
- la preview d'import, car elle décrit un fichier avant écriture, pas le résultat persistant final.

## Principe de validation retenu

Le ticket vise une validation chiffrée lisible et défendable. Le principe retenu est donc :

1. comparer d'abord les données source Excel et l'état final de Solde, pas seulement les compteurs d'import ;
2. raisonner par exercice réel et par domaine métier ;
3. utiliser les états comptables comme preuve principale côté comptabilité ;
4. utiliser les listes et totaux filtrés par date comme preuve principale côté gestion ;
5. consigner explicitement tout écart avec une hypothèse de cause.

## Périmètre de comparaison

### 1. Gestion

Pour chaque exercice, comparer au minimum :

- le nombre et le total des `factures clients` ;
- le nombre et le total des `factures fournisseurs` si le fichier en génère ;
- le nombre et le total des `paiements` ;
- le nombre et le total des mouvements de `caisse` ;
- le nombre et le total des mouvements de `banque` ;
- les `salaires` si l'exercice contient une feuille correspondante ;
- quelques cas ciblés de rapprochement métier sensibles : paiements déposés ou non, factures fournisseurs reconstruites via références `FF-*`, mouvements de solde initial ignorés.

### 2. Comptabilité

Pour chaque exercice, comparer au minimum :

- le nombre d'écritures du `Journal` ;
- le total `débit` et le total `crédit` du `Journal` ;
- la `Balance` par compte avec contrôle des totaux `débit`, `crédit` et `solde` ;
- le `Bilan` (`total actif`, `total passif`, `résultat`) ;
- le `Résultat` (`charges`, `produits`, résultat net) ;
- un jeu réduit de `grands livres` sur comptes sensibles pour vérification détaillée si un écart apparaît.

## Matrice de preuves à produire

| Domaine | Source Excel | Source Solde | Portée | Type de preuve |
|---|---|---|---|---|
| Factures clients | feuille `Factures` gestion | écran `Factures clients` + API `GET /invoices` | exercice par dates | nombre, total, échantillons |
| Factures fournisseurs | feuilles `Banque` / `Caisse` si reconstruction `FF-*` | écran `Factures fournisseurs` + API `GET /invoices` | exercice par dates | nombre, total, références sensibles |
| Paiements | feuille `Paiements` gestion | écran `Paiements` + API `GET /payments` | exercice par dates | nombre, total, déposés/non déposés |
| Caisse | feuille `Caisse` gestion | écran `Caisse` + API `GET /cash/entries` | exercice par dates | nombre, total net, cas ignorés |
| Banque | feuille `Banque` gestion | écran `Banque` + API `GET /bank/transactions` | exercice par dates | nombre, total net, cas ignorés |
| Salaires | feuille salaires si présente | écran `Salaires` | exercice par dates/mois | nombre, totaux |
| Journal | feuille `Journal` comptabilité | écran/API `journal-grouped` | exercice par `fiscal_year_id` | nombre, débit, crédit |
| Balance | feuille `Journal` agrégée par compte | écran/API `balance` | exercice par `fiscal_year_id` | par compte + totaux |
| Bilan | feuille `Journal` retraitée | écran/API `bilan` | exercice par `fiscal_year_id` | actif, passif, résultat |
| Résultat | feuille `Journal` retraitée | écran/API `resultat` | exercice par `fiscal_year_id` | charges, produits, résultat |
| Grand livre | feuille `Journal` détaillée | écran/API `ledger/{account}` | exercice par `fiscal_year_id` | contrôle ciblé en cas d'écart |

## Séquence de validation recommandée

### Étape 1 — figer le périmètre des exercices

Avant toute comparaison, relever les bornes réelles des exercices présents dans Solde.

Règle : toujours comparer sur les dates réelles de l'exercice, pas sur une hypothèse d'année civile fondée sur le nom du fichier.

### Étape 2 — valider la gestion sur l'état final importé

Pour chaque exercice :

1. filtrer les écrans ou APIs de gestion sur la plage de dates exacte de l'exercice ;
2. relever les compteurs et totaux visibles ;
3. reconstruire les mêmes chiffres côté Excel ;
4. noter les écarts éventuels ;
5. qualifier chaque écart :
   - comportement attendu d'import ;
   - divergence de données ;
   - bug probable ;
   - ambiguïté métier ou source.

### Étape 3 — valider la comptabilité par exercice

Pour chaque exercice :

1. relever les chiffres du `Journal` ;
2. vérifier l'égalité `total débit = total crédit` ;
3. relever la `Balance` complète ;
4. relever le `Bilan` et le `Résultat` ;
5. si un écart persiste, ouvrir un ou plusieurs `Grands livres` ciblés pour isoler le compte responsable.

### Étape 4 — produire un constat de validation

Pour chaque exercice, produire un constat unique avec :

- ce qui a été comparé ;
- les chiffres Excel ;
- les chiffres Solde ;
- le statut (`conforme`, `écart justifié`, `écart à corriger`, `à clarifier`) ;
- les remarques utiles pour la suite du ticket.

## Format attendu du constat

Le format cible pour la recette est le suivant.

### Exercice `...`

| Domaine | Excel | Solde | Statut | Commentaire |
|---|---|---|---|---|
| Factures clients | ... | ... | ... | ... |
| Factures fournisseurs | ... | ... | ... | ... |
| Paiements | ... | ... | ... | ... |
| Caisse | ... | ... | ... | ... |
| Banque | ... | ... | ... | ... |
| Journal | ... | ... | ... | ... |
| Balance | ... | ... | ... | ... |
| Bilan | ... | ... | ... | ... |
| Résultat | ... | ... | ... | ... |

## Points d'attention

- Ne pas utiliser le `Dashboard` comme preuve principale par exercice.
- Ne pas comparer uniquement les compteurs retournés par l'import : la cible est l'état persistant final de Solde.
- Pour la gestion, préférer les filtres de date exacts aux comparaisons globales de listes non bornées.
- Les écritures auto-générées issues de la gestion et les écritures importées de comptabilité doivent être lues ensemble dans les états comptables finaux si l'objectif est de comparer Solde à la réalité Excel complète.
- Les lignes explicitement ignorées par politique d'import (`Total`, `solde initial`, écriture nulle, etc.) doivent être connues avant de qualifier un écart comme bug.

## Prochaine étape recommandée

Préparer un premier relevé de validation sur l'exercice que l'utilisateur est en train de rejouer, avec un gabarit de constat rempli partiellement dès que les imports sont terminés.