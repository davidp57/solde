# BL-005 — Politique de coexistence entre imports et écritures existantes

## Objectif

Rendre explicite la règle de coexistence actuelle entre :

- les imports `Gestion` ;
- les imports `Comptabilite` ;
- les objets métier déjà présents dans Solde ;
- les écritures comptables déjà générées automatiquement ;
- les écritures comptables saisies manuellement.

Ce document formalise la politique actuellement retenue dans le code pour éviter les décisions implicites ou contradictoires pendant les reprises historiques et la convergence Excel/Solde.

## Principes directeurs

1. La sûreté métier prime sur l'automatisation.
2. Un import ne doit jamais réécrire silencieusement un objet ou une écriture existante sans règle explicite et sûre.
3. En comptabilité, seul le doublon exact est dédupliqué automatiquement.
4. Une ambiguïté de rapprochement métier doit être bloquée ou laissée à revue manuelle, jamais résolue arbitrairement.
5. La coexistence avec des écritures `MANUAL` est autorisée tant qu'il n'existe pas de doublon exact.

## Politique retenue

### Vue synthétique

| Cas | Preview | Import réel | Décision retenue |
|---|---|---|---|
| Fichier déjà importé à hash identique | bloqué | bloqué | refuser le réimport exact |
| Doublon exact d'objet `Gestion` déjà présent | ignoré | ignoré | ne pas recréer le même objet métier |
| Doublon exact de ligne comptable déjà présente | ignoré | ignoré | ne pas recréer la même ligne comptable |
| Groupe comptable déjà couvert par des écritures auto-générées Solde | avertissement global + lignes ignorées | lignes ignorées | conserver Solde comme source déjà suffisante pour ce groupe |
| Écritures `MANUAL` déjà présentes sur la période sans doublon exact | autorisé | autorisé | importer les nouvelles lignes en plus |
| Rapprochement métier ambigu | bloqué | bloqué | exiger une résolution humaine |
| Clarification sûre d'une facture client existante depuis `Comptabilite` | ignoré comme nouvelle écriture + clarification métier | clarification appliquée | enrichir l'objet existant sans dupliquer les écritures |
| Doublon proche non exact | signal implicite seulement via delta ou comportement normal | importé comme nouvelle écriture | ne pas fusionner automatiquement un cas ambigu |

## Règles détaillées par famille de cas

### 1. Idempotence par fichier

- Un fichier déjà importé avec succès, identifié par le même hash, est refusé.
- Cette règle vaut pour `Gestion` comme pour `Comptabilite`.
- Le diagnostic visible est `already-imported`.

### 2. Imports `Gestion`

#### Contacts, factures, salaires déjà présents

- Si l'objet existe déjà selon la signature métier actuellement retenue, la ligne est ignorée.
- L'import ne tente pas de fusionner, compléter ou écraser l'objet existant.

#### Paiements, banque, caisse déjà présents

- Si la signature de comparaison métier existe déjà dans Solde, la ligne est ignorée.
- Le but est d'éviter le doublon fonctionnel, pas seulement le doublon technique de ligne.

#### Cas ambigus côté `Gestion`

- Si un contact client est ambigu, la facture est bloquée.
- Si un paiement ne peut pas être rapproché de façon sûre, il est bloqué.
- Si plusieurs candidats existent pour un même rapprochement, il est bloqué.

### 3. Imports `Comptabilite`

#### Doublon exact de ligne comptable

- Une ligne `Journal` déjà présente avec la même signature `(date, compte, libellé normalisé, débit, crédit)` est ignorée.
- Cette déduplication est volontairement stricte.

#### Groupe déjà couvert par Solde

- Si un groupe d'écritures correspond déjà à un groupe auto-généré par Solde (`invoice`, `payment`, `deposit`, `salary`, `gestion`, `cloture`), il est ignoré ligne par ligne.
- La preview ajoute un avertissement global de coexistence pour signaler qu'une partie du journal Excel recouvre des écritures déjà produites dans Solde.
- Cet avertissement n'est pas bloquant.

#### Écritures `MANUAL` déjà existantes

- La simple présence d'écritures `MANUAL` n'empêche pas l'import `Comptabilite`.
- Si une nouvelle ligne comptable ne correspond pas à un doublon exact, elle est importée comme nouvelle écriture `MANUAL`.
- La règle retenue est de ne pas surbloquer un import historique à cause d'une comptabilité manuelle existante, tout en conservant la déduplication stricte.
- Quand une ligne importée partage la même date, le même compte et les mêmes montants qu'une écriture `MANUAL` sans être un doublon exact sur le libellé, Solde émet un avertissement non bloquant de proximité pour inviter à revue manuelle.

#### Clarification d'une facture client existante

- Si des écritures `Comptabilite` correspondent à une facture client déjà présente dans Solde, Solde ne crée pas de nouvelle écriture comptable manuelle pour la dupliquer.
- Si la facture existante peut être clarifiée de façon sûre à partir des écritures, cette clarification est appliquée.
- Sinon, les lignes sont ignorées comme déjà couvertes par l'existant.

### 4. Doublons proches et écarts ambigus

- Un doublon proche mais non exact n'est pas automatiquement fusionné.
- Exemple typique : même date, même compte et même montant, mais libellé différent sans preuve suffisante qu'il s'agit de la même écriture.
- Dans ce cas, la règle retenue reste conservatrice : on préfère conserver deux écritures plutôt que supprimer ou fusionner à tort.

## Traduction opérationnelle actuelle dans les diagnostics

Les catégories stables actuellement visibles ou dérivables sont notamment :

- `already-imported` pour le réimport exact d'un fichier ;
- `entry-existing` pour une écriture comptable déjà présente ;
- `entry-covered-by-solde` pour une ligne comptable déjà couverte par un groupe métier ou une opération existante dans Solde ;
- `entry-near-manual` pour une ligne comptable proche d'une écriture `MANUAL` existante mais non strictement identique ;
- `existing-row-in-solde` pour une ligne de gestion déjà représentée dans Solde ;
- `comptabilite-coexistence` pour l'avertissement global de coexistence avec des écritures auto-générées ;
- les catégories d'ambiguïté ou d'échec de rapprochement (`invoice-ambiguous-contact`, `payment-unmatched`, etc.) pour les cas à bloquer.

## Ce que BL-005 acte maintenant

BL-005 acte la politique suivante comme cible produit actuelle :

- coexistence autorisée avec l'existant quand le cas est sûr et non destructif ;
- déduplication automatique uniquement sur les doublons exacts ou les groupes explicitement reconnus comme déjà couverts par Solde ;
- aucun blocage de principe sur la seule présence d'écritures `MANUAL` ;
- signal non bloquant quand une ligne importée est proche d'une écriture `MANUAL` existante sans être strictement identique ;
- aucun écrasement silencieux d'une donnée existante ;
- blocage dès qu'un rapprochement métier devient ambigu.

## Suites éventuelles hors de ce cadrage initial

- décider si certains autres doublons proches doivent un jour être signalés explicitement pour revue manuelle au-delà du cas `MANUAL` déjà couvert.