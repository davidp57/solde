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
- Observations préalables : `test centré sur l'exercice 2024 uniquement ; les exercices 2023, 2024 et 2025 affichent tous des chiffres dans l'écran Balance ; pour les écrans de gestion, le relevé se fait avec l'exercice 2024 sélectionné ; relevé visuel Banque/Caisse reconfirmé le 2026-04-16 après configuration de l'ouverture du système au 2024-08-01 (banque 8 155,62 € ; caisse 226,79 €)`

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
- `Caisse` : solde courant `54.98 €`, variation de période `+54.98 €`, nombre d'écritures `103`, comptages visibles `0` ; relevé visuel confirmé sur l'écran `Caisse` avec l'exercice `2024` sélectionné
- `Banque` : solde courant `2674.77 €`, variation de période `+2674.77 €`, nombre de transactions `204`, bordereaux visibles `0` ; relevé visuel confirmé sur l'écran `Banque` avec l'exercice `2024` sélectionné
- `Salaires` : total visible `22`, brut `20 509,94 €`, net `15 964,81 €`, coût total `25 221,81 €` ; relevé visuel confirmé sur l'écran `Salaires` avec l'exercice `2024` sélectionné
- `Journal` : nombre d'écritures `670`, total débit `184 989,16 €`, total crédit `184 989,16 €`, sources distinctes `5` ; relevé visuel confirmé sur l'écran `Journal comptable` avec l'exercice `2024` sélectionné
- `Balance` : lignes de balance visibles confirmées sur l'écran `Balance générale` avec l'exercice `2024` sélectionné ; l'écran ne montre toujours pas de total général visible, donc les totaux `débit 184 989,16 €` et `crédit 184 989,16 €` restent issus du calcul en base locale
- `Bilan` : total actif `54 196,45 €`, total passif `-60 018,54 €`, résultat `-5 822,09 €` ; relevé visuel confirmé sur l'écran `Bilan simplifié` avec l'exercice `2024` sélectionné ; l'UI affiche explicitement `Total passif : -60 018,54 €` et `Résultat de l'exercice : -5 822,09 €`
- `Résultat` : total charges `31 052,56 €`, total produits `25 230,47 €`, résultat net `-5 822,09 €` ; relevé visuel confirmé sur l'écran `Compte de résultat` avec l'exercice `2024` sélectionné ; l'UI affiche `Déficit : -5 822,09`

## Exercice 2024

- Bornes de l'exercice dans Solde : `2024-08-01 -> 2025-07-31` (statut `Ouvert`)
- Fichier(s) Excel de référence : `Gestion 2024.xlsx` et `Comptabilite 2024.xlsx`

| Domaine | Chiffres Excel | Chiffres Solde | Statut | Commentaire |
|---|---|---|---|---|
| Factures clients | `245 factures ; total 22 357,00 € ; payé 22 253,00 € ; en retard 104,00 € (calculé)` | `245 factures ; total 22 357,00 € ; payé 22 253,00 € ; en retard 0,00 €` | `à clarifier` | `nombre, total et payé conformes ; les 104,00 € restants correspondent aux factures 2024-0277 (78,00 €) et 2025-0010 (26,00 €), encore au statut sent sans due_date, donc non comptées comme overdue par l'UI` |
| Factures fournisseurs | `36 références FF-* reconstituées depuis Banque/Caisse ; Banque = 20 lignes / 3 811,00 € ; Caisse = 16 lignes / 592,81 € ; total 4 403,81 €` | `36 factures ; total 4 403,81 € ; payé 4 403,81 €` | `conforme` | `la reconstruction par références FF-* sur la plage 2024-08-01 -> 2025-07-31 retombe exactement sur les factures fournisseurs créées dans Solde` |
| Paiements | `266 paiements ; total 23 028,00 € ; 2 non remis` | `266 paiements ; total 23 028,00 € ; 2 non remis` | `conforme` | `nombre, total et non remis conformes` |
| Caisse | `102 mouvements importés ; flux net -171,81 € ; ouverture du système hors fichier = +226,79 €` | `solde 54,98 € ; variation +54,98 € ; 103 écritures ; 0 comptages visibles` | `écart justifié` | `relevé visuel reconfirmé le 2026-04-16 ; BL-027 appliqué : Solde affiche le cumul des flux importés et d'une ouverture du système explicite au 2024-08-01` |
| Banque | `203 mouvements importés ; flux net -5 480,85 € ; ouverture du système hors fichier = +8 155,62 €` | `solde 2 674,77 € ; variation +2 674,77 € ; 204 transactions ; 0 bordereaux visibles` | `écart justifié` | `relevé visuel reconfirmé le 2026-04-16 ; BL-027 appliqué : le solde visible intègre l'ouverture du système au 2024-08-01 en plus des transactions importées` |
| Salaires | `25 lignes candidates dans l'onglet Aide Salaires ; 22 salaires distincts après déduplication mois + employé ; brut 20 509,94 € ; net 15 964,81 € ; coût total 25 221,81 €` | `22 salaires sur l'exercice 2024 ; brut 20 509,94 € ; net 15 964,81 € ; coût total 25 221,81 €` | `à clarifier` | `relevé visuel écran confirmé le 2026-04-16 ; les chiffres Solde concordent avec la logique d'import actuelle ; réserve méthodologique : la colonne Excel reste dérivée du parseur d'import et non d'un relevé indépendant du classeur` |
| Journal | `1 390 lignes de journal ; 1 385 lignes importables (5 écritures nulles ignorées) ; 660 opérations (colonne N° de 0 à 659) ; débit 181 885,84 € ; crédit 181 885,84 €` | `670 opérations ; débit 184 989,16 € ; crédit 184 989,16 € ; 5 sources distinctes` | `à clarifier` | `l'écart ne vient pas d'un sur-découpage ChangeNum : l'onglet Journal retombe aussi sur 660 groupes ; Solde affiche 670 groupes car 107 groupes base-only et 97 groupes Excel-only ne partagent pas la même signature date + comptes + montants, soit un delta net de +10 groupes et +3 103,32 €` |
| Balance | `débit 181 885,84 € ; crédit 181 885,84 € ; solde débiteur 87 045,59 € ; solde créditeur 87 045,59 €` | `balance affichée confirmée visuellement sur l'exercice 2024 ; totaux Solde débit/crédit = 184 989,16 € / 184 989,16 €` | `à clarifier` | `le delta de 3 103,32 € suit le même motif que le Journal : des écritures de gestion auto-générées, surtout fournisseurs via 401000 et certains groupes de salaires, ne retombent pas sur une signature identique à celle du journal Excel` |
| Bilan |  | `actif 54 196,45 € ; passif -60 018,54 € ; résultat -5 822,09 €` | `à clarifier` | `relevé visuel écran confirmé le 2026-04-16 ; l'UI affiche explicitement un total passif négatif, reste à décider si cette convention d'affichage est celle attendue pour la recette` |
| Résultat |  | `charges 31 052,56 € ; produits 25 230,47 € ; résultat -5 822,09 €` | `relevé visuel` | `écran confirmé le 2026-04-16 ; l'UI qualifie explicitement le résultat de déficit` |

### Vérifications ciblées 2024

- Comptes ou écritures sensibles vérifiés : `531000 Caisse`, `512100 Compte courant`, `512102 Compte d'épargne`, `110000 Report à nouveau`, `431100 URSSAF`
- Lignes explicitement ignorées connues : `Gestion 2024 : 5 ignorées, 0 bloquante ; Comptabilité 2024 : 1367 ignorées, 0 bloquante`
- Rapprochement technique du Journal 2024 : `le seul onglet Journal contient 1 385 lignes comptables importables, 660 opérations (colonne N° = 0..659) et 181 885,84 € au débit comme au crédit ; l'algorithme d'import reconstruit aussi 660 groupes sur cet onglet, donc le différentiel Solde n'est pas causé par ChangeNum ; les groupes non rapprochés côté base sont uniquement des sources auto-générées invoice/payment/salary, jamais des groupes manual importés depuis Comptabilité`
- Écarts restant à instruire : `rapprochement Excel -> Solde encore à finaliser domaine par domaine ; pour le Journal et la Balance, arrêter explicitement la convention de comparaison retenue entre état final Solde et journal Excel, au lieu de viser une identité brute ligne à ligne quand la modélisation diffère ; trancher la convention métier du montant en retard client quand une facture reste impayée sans due_date ni statut overdue ; vérifier si le signe du total passif affiché dans le Bilan correspond bien à la convention d'affichage attendue ; préciser dans la synthèse finale la convention retenue pour comparer la trésorerie importée et l'ouverture du système hors fichier ; confirmer si les salaires doivent être rapprochés seulement sur les montants métier ou aussi sur une convention stricte de date et de regroupement`

## Exercice 2025

- Bornes de l'exercice dans Solde : `...`
- Fichier(s) Excel de référence : `...`
- Décision de clôture `BL-026` : `l'exercice 2025 n'est pas poursuivi dans ce ticket ; la suite de la validation stricte est reportée après cadrage de BL-008 et traitement des correctifs identifiés comme BL-029`

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

- Niveau de confiance sur la reprise `Gestion` : `élevé sur l'exercice 2024 pour les chiffres métier visibles : factures fournisseurs, paiements, banque et caisse sont conformes ou justifiés ; la validation 2025 reste à faire et certains points de convention métier demeurent ouverts côté factures clients et salaires`
- Niveau de confiance sur la reprise `Comptabilité` : `moyen à bon sur l'exercice 2024 : les états principaux sont cohérents et les écarts résiduels identifiés relèvent en partie de différences de modélisation entre Excel et Solde ; la validation 2025 n'est pas poursuivie dans BL-026 et la règle de comparaison comptable cible doit encore être figée`
- Écarts bloquants : `aucun écart bloquant démontré à ce stade sur la reprise 2024 ; en revanche, il n'existe pas encore de convention de rapprochement assez explicite pour conclure à une convergence comptable brute Excel = Solde sur le journal final, ce qui motive la bascule vers BL-008 et BL-029`
- Écarts non bloquants : `montant en retard client dépendant de la convention UI (`due_date` / `overdue`) ; trésorerie 2024 nécessitant l'intégration de l'ouverture du système hors fichier ; comparaison comptable 2024 sensible à des différences de granularité (facture fournisseur + règlement dans Solde vs paiement direct dans Excel, ventilation produit côté clients, regroupements salariaux)`
- Sujets à transformer en correctifs distincts : `BL-029 pour la saisie et la ventilation des factures clients pilotées par les lignes, y compris le cas des factures mixtes ; BL-008 pour un mode de validation itérative distinguant convergence globale et validation du moteur Gestion ; éventuellement un sujet dédié si la convention d'affichage du passif au Bilan doit être revue ; la validation future de 2025 devra être reprise dans ce nouveau cadre plutôt que prolongée telle quelle dans BL-026`