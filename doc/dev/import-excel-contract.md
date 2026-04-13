# Contrat d'import Excel historique

## But

Décrire explicitement ce que l'import Excel considère aujourd'hui comme :

- accepté ;
- ignoré ;
- bloquant ;
- ambigu.

Ce document sert de référence de travail tant que les règles ne sont pas encore entièrement extraites dans une couche métier dédiée.

## Gestion

### Contacts

Accepté :
- feuille reconnue avec colonne `Nom` ;
- colonne `Prénom` facultative ;
- colonne `Email` facultative.

Ignoré :
- doublon intra-fichier sur le même contact ;
- contact déjà présent en base.

Bloquant :
- ligne reconnue avec `Nom` manquant.

Ambigu :
- aucun cas explicite actuellement.

### Factures

Accepté :
- feuille reconnue avec date, client, montant ;
- numéro de facture facultatif, un identifiant technique est généré si absent ;
- réutilisation d'un contact existant seulement en cas de match exact normalisé unique sur le nom client.

Ignoré :
- doublon intra-fichier sur un même numéro de facture ;
- facture déjà présente en base.

Bloquant :
- client manquant ;
- montant manquant, nul ou invalide ;
- colonnes requises absentes.

Ambigu :
- plusieurs contacts existants correspondent exactement au même nom client normalisé ; le fichier est alors bloqué explicitement.

### Paiements

Accepté :
- paiement avec référence de facture résolue sans ambiguïté ;
- ou paiement sans référence mais rapprochable de façon unique via le contact.

Ignoré :
- aucun cas explicite actuellement.

Bloquant :
- montant manquant, nul ou invalide ;
- absence simultanée de référence facture et de contact ;
- paiement impossible à rapprocher à une facture importée ou déjà présente en base.

Ambigu :
- plusieurs factures candidates par référence partielle ;
- plusieurs factures candidates via le contact.

### Caisse

Accepté :
- feuille reconnue avec date et mouvement monétaire interprétable.

Ignoré :
- aucun cas explicite actuellement.

Bloquant :
- date invalide ou absente ;
- mouvement ou montant non interprétable.

Ambigu :
- aucun cas explicite actuellement.

### Banque

Accepté :
- feuille reconnue avec date et montant interprétable.

Ignoré :
- aucun cas explicite actuellement.

Bloquant :
- date invalide ou absente ;
- montant absent, nul ou invalide.

Ambigu :
- aucun cas explicite actuellement.

## Comptabilite

### Journal

Accepté :
- feuille `Journal` reconnue avec compte et débit/crédit exploitables ;
- coexistence autorisée avec des écritures déjà générées depuis la gestion ;
- rattachement automatique à l'exercice couvrant la date de l'écriture quand cet exercice existe.

Ignoré :
- feuilles de reporting (`Grand Livre`, `Balance`, etc.) ;
- `Journal (saisie)` ;
- ligne `Journal` dont le débit et le crédit sont tous deux nuls ;
- doublon exact d'une écriture déjà présente en base sur la signature `(date, compte, libellé normalisé, débit, crédit)`.

Bloquant :
- compte manquant ;
- montants non interprétables ;
- réimport exact d'un fichier déjà importé avec succès.

Ambigu :
- aucun cas explicite actuellement.

## Règles transverses

Accepté :
- seules les feuilles reconnues et valides alimentent les compteurs d'import.
- la traçabilité retenue passe par le journal d'import (`import_logs`) et la liste sérialisée des `created_objects`, sans relation SQL dédiée par objet à ce stade.

Ignoré :
- feuilles auxiliaires, TODO, reporting, aide à la saisie.

Bloquant :
- toute erreur détectée sur une feuille reconnue empêche l'import complet ;
- tout réimport exact d'un fichier déjà importé avec succès est refusé ;
- les exercices comptables, le plan comptable et les règles comptables ne sont jamais créés automatiquement par l'import ;
- la coexistence avec des écritures déjà présentes reste autorisée : en comptabilité, seuls les doublons exacts sont ignorés ligne à ligne.

Ambigu :
- tout rapprochement métier donnant plusieurs candidats doit être bloqué, jamais résolu arbitrairement.

## Limites connues

- Une partie de l'orchestration preview/import reste dans `excel_import.py`, mais les décisions métier stables et les diagnostics normalisés sont désormais centralisés.
- Les cas de lignes ignorables sûres restent plus avancés sur `Contacts` et `Factures` que sur les autres feuilles.
