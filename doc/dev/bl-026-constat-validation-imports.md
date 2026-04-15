# BL-026 — Constat de validation des imports Excel

## Rappel

Ce document sert à consigner le résultat effectif de la validation chiffrée entre les fichiers Excel sources et les données visibles dans Solde.

Méthode de référence : `doc/dev/bl-026-cadrage-validation-imports-excel.md`.

## Préconditions du relevé

- Base utilisée : `base locale de dev après reset`
- Date du relevé : `2026-04-15`
- Import `Gestion 2024` : `succès avec avertissements`
- Import `Gestion 2025` : `non lancé`
- Import `Comptabilité 2024` : `succès avec avertissements`
- Import `Comptabilité 2025` : `non lancé`
- Exercices présents dans Solde : `2023`, `2024` et `2025` (créés via le bouton "créer le socle comptable")
- Observations préalables : `test centré sur l'exercice 2024 uniquement ; les exercices 2023, 2024 et 2025 affichent tous des chiffres dans l'écran Balance ; pour les écrans de gestion, le relevé se fait en vue tous les exercices puis avec filtre strict sur la colonne date`

## Capture rapide pendant le test 2024

### Résultat d'import à relever tout de suite

- Résultat `Gestion 2024` : `succès avec avertissements`
- Compteurs `Gestion 2024` : `contacts=66`, `factures=303`, `paiements=308`, `salaires=23`, `caisse=102`, `banque=210`, `écritures=1445`
- Lignes `Gestion 2024` ignorées / bloquées : `ignorées=5`, `bloquantes=0`
- Résultat `Comptabilité 2024` : `succès avec avertissements`
- Compteurs `Comptabilité 2024` : `écritures=23`, `ignorées=1367`, `bloquées=0`
- Messages d'avertissement ou d'erreur à conserver : `rien`

### Contrôles Solde à relever juste après import

- Bornes exactes de l'exercice `2024` dans Solde : `2024-08-01 -> 2025-07-31` (statut `Ouvert`)
- `Factures clients` : total visible `245`, montant total `22357.00 €`, montant payé `22253.00 €`, montant en retard `0.00 €`
- `Factures fournisseurs` : total visible `36`, montant total `4403.81 €`
- `Paiements` : total visible `266`, montant total `23028.00 €`, non remis en banque `2`
- `Caisse` : solde courant `-171.81 €`, variation de période `-171.81 €`, nombre d'écritures `102` ; cartes alignées sur le périmètre affiché (`Périmètre affiché`)
- `Banque` : solde courant `2674.77 €`, variation de période `+2674.77 €`, nombre de transactions `204` ; cartes alignées sur le périmètre affiché (`Périmètre affiché`)
- `Journal` : nombre d'écritures `670`, total débit `184 989,16 €`, total crédit `184 989,16 €`
- `Balance` : total débit `184 989,16 €`, total crédit `184 989,16 €` ; totaux calculés directement depuis la base locale car l'écran n'affiche pas de total général
- `Bilan` : total actif `54 196,45 €`, total passif `-60 018,54 €`, résultat `-5 822,09 €`
- `Résultat` : total charges `31 052,56 €`, total produits `25 230,47 €`, résultat net `-5 822,09 €`

## Exercice 2024

- Bornes de l'exercice dans Solde : `2024-08-01 -> 2025-07-31` (statut `Ouvert`)
- Fichier(s) Excel de référence : `Gestion 2024.xlsx` et `Comptabilite 2024.xlsx`

| Domaine | Chiffres Excel | Chiffres Solde | Statut | Commentaire |
|---|---|---|---|---|
| Factures clients | `245 factures ; total 22 357,00 € ; payé 22 253,00 € ; en retard 104,00 € (calculé)` | `245 factures ; total 22 357,00 € ; payé 22 253,00 € ; en retard 0,00 €` | `à clarifier` | `nombre, total et payé conformes ; écart de 104,00 € sur le montant en retard` |
| Factures fournisseurs | `à reconstruire depuis les onglets Banque et Caisse (références FF-*/vlookup)` | `36 factures ; total 4 403,81 €` | `à instruire` | `pas d'onglet dédié dans Gestion 2024.xlsx ; rapprochement Excel direct non encore fait` |
| Paiements | `266 paiements ; total 23 028,00 € ; 2 non remis` | `266 paiements ; total 23 028,00 € ; 2 non remis` | `conforme` | `nombre, total et non remis conformes` |
| Caisse |  | `solde -171,81 € ; variation -171,81 € ; 102 écritures` | `à clarifier` | `relevé provisoire ; dépend du futur traitement de l'ouverture du système sur le premier exercice importé` |
| Banque |  | `solde 2 674,77 € ; variation +2 674,77 € ; 204 transactions` | `à reprendre` | `cartes alignées sur le périmètre affiché après correction frontend du 2026-04-15 ; chiffres susceptibles d'évoluer après traitement de l'ouverture du système` |
| Salaires |  | `23 salaires créés à l'import ; contrôle écran détaillé non encore relevé` |  |  |
| Journal |  | `670 opérations ; débit 184 989,16 € ; crédit 184 989,16 €` |  |  |
| Balance |  | `débit 184 989,16 € ; crédit 184 989,16 €` |  | `totaux calculés directement depuis la base locale, car non affichés dans l'écran` |
| Bilan |  | `actif 54 196,45 € ; passif -60 018,54 € ; résultat -5 822,09 €` |  |  |
| Résultat |  | `charges 31 052,56 € ; produits 25 230,47 € ; résultat -5 822,09 €` |  |  |

### Vérifications ciblées 2024

- Comptes ou écritures sensibles vérifiés : `531000 Caisse`, `512100 Compte courant`, `512102 Compte d'épargne`, `110000 Report à nouveau`, `431100 URSSAF`
- Lignes explicitement ignorées connues : `Gestion 2024 : 5 ignorées, 0 bloquante ; Comptabilité 2024 : 1367 ignorées, 0 bloquante`
- Écarts restant à instruire : `rapprochement Excel -> Solde encore à finaliser domaine par domaine ; factures fournisseurs à reconstruire depuis Banque/Caisse (références FF-*) ; trésorerie 2024 à remesurer après traitement du sujet BL-027 sur l'ouverture du système Banque/Caisse du premier exercice importé ; contrôle détaillé écran Salaires non encore relevé ; vérifier si le signe du total passif affiché dans le Bilan correspond bien à la convention d'affichage attendue`

## Exercice 2025

- Bornes de l'exercice dans Solde : `...`
- Fichier(s) Excel de référence : `...`

| Domaine | Chiffres Excel | Chiffres Solde | Statut | Commentaire |
|---|---|---|---|---|
| Factures clients |  |  |  |  |
| Factures fournisseurs |  |  |  |  |
| Paiements |  |  |  |  |
| Caisse |  |  |  |  |
| Banque |  |  |  |  |
| Salaires |  |  |  |  |
| Journal |  |  |  |  |
| Balance |  |  |  |  |
| Bilan |  |  |  |  |
| Résultat |  |  |  |  |

### Vérifications ciblées 2025

- Comptes ou écritures sensibles vérifiés : `...`
- Lignes explicitement ignorées connues : `...`
- Écarts restant à instruire : `...`

## Synthèse globale

- Niveau de confiance sur la reprise `Gestion` : `...`
- Niveau de confiance sur la reprise `Comptabilité` : `...`
- Écarts bloquants : `...`
- Écarts non bloquants : `...`
- Sujets à transformer en correctifs distincts : `...`