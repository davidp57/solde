# Procédure opératoire — import Excel historique

## Objectif

Dérouler un import historique `Gestion` ou `Comptabilite` avec un niveau de sûreté compatible avec les garde-fous actuellement en place dans l'application.

Cette procédure sert de check-list opératoire et de base pour les futures répétitions sur fichiers réels.

## Pré-requis

- Travailler sur une base sauvegardée ou facilement restaurable.
- Vérifier que la base locale est au schéma courant avant toute répétition réelle (`alembic upgrade head` si nécessaire).
- Vérifier que le fichier source correspond bien à l'année et au périmètre attendus.
- Disposer d'un export Excel source non modifié manuellement entre deux essais, pour que le garde-fou de hash reste pertinent.
- Pour un import `Comptabilite`, vérifier qu'aucune écriture auto-générée issue de la gestion n'existe déjà en base.

## Ordre recommandé

1. Importer d'abord les fichiers `Gestion` par ordre chronologique si cette filière sert de source métier principale.
2. N'importer `Comptabilite` que si la comptabilité doit être injectée comme source primaire et qu'aucune écriture de gestion auto-générée n'existe déjà.
3. Ne jamais importer deux fois le même fichier sans comprendre d'abord pourquoi le premier import n'est pas exploitable.
4. Si des paiements d'un exercice courant pointent vers des factures de l'exercice précédent, charger d'abord le fichier `Gestion` précédent pour rétablir des candidats de rapprochement uniques.

## Check-list avant import

1. Ouvrir la preview du fichier visé.
2. Vérifier que `can_import` est vrai.
3. Lire les avertissements feuille par feuille.
4. Vérifier les compteurs `ignored_rows` et `blocked_rows`.
5. Confirmer que les lignes ignorées correspondent bien à des cas attendus : doublons intra-fichier, données déjà présentes en base, feuilles auxiliaires.
6. Si la preview est bloquée, ne pas forcer l'import : corriger la donnée ou la stratégie d'import d'abord.

## Cas de blocage attendus

- Colonnes requises manquantes sur une feuille reconnue.
- Lignes invalides sur `Contacts`, `Factures`, `Paiements`, `Caisse`, `Banque` ou `Journal`.
- Paiements sans facture rapprochable.
- Paiements ambigus par référence ou par contact.
- Réimport exact d'un fichier déjà importé avec succès.
- Import `Comptabilite` alors que des écritures auto-générées issues de la gestion existent déjà.

## Lignes ignorées attendues

- Feuilles auxiliaires, TODO, reporting, `Journal (saisie)`.
- Doublons intra-fichier sur `Contacts` et `Factures`.
- `Contacts` déjà présents en base.
- `Factures` déjà présentes en base.
- Lignes `Total` ou synthèse sans donnée métier exploitable dans `Factures`.
- Lignes descriptives d'ouverture sans mouvement exploitable dans `Banque`.
- Lignes de solde initial sans mouvement exploitable dans `Caisse`.
- Prévisions de remise d'espèces sans date dans `Caisse` lorsqu'elles représentent explicitement un futur dépôt bancaire.
- Lignes `Journal` à débit et crédit tous deux nuls.

## Statut réel constaté au 2026-04-11

- `Comptabilite 2024.xlsx` : preview DB-aware verte, `1385` écritures estimées, `20` lignes ignorées, `0` erreur bloquante.
- `Comptabilite 2025.xlsx` : preview DB-aware verte, `930` écritures estimées, `10` lignes `Journal` à zéro correctement ignorées, `0` erreur bloquante.
- `Gestion 2024.xlsx` : import réel réussi sur base locale (`46` contacts, `263` factures, `268` paiements, `102` mouvements de caisse, `210` transactions bancaires créés ; `2` lignes ignorées, `0` blocage).
- `Gestion 2025.xlsx` : la prévision `Caisse` ligne `23` (`Remise espèces`, montant `-710`, date absente) est bien ignorée ; les ambiguïtés de `Paiements` lignes `2` et `3` disparaissent après import préalable de `Gestion 2024.xlsx`, puis l'import réel réussit (`14` contacts, `183` factures, `183` paiements, `75` mouvements de caisse, `145` transactions bancaires créés ; `12` lignes ignorées, `0` blocage).
- Le réimport exact de `Gestion 2025.xlsx` est ensuite correctement refusé par le garde-fou de hash.
- Les anciens faux positifs réels ont été éliminés : ligne `Total` en `Factures`, lignes descriptives d'ouverture en `Banque`, lignes de solde initial / montants signés en `Caisse`, prévisions de remise d'espèces sans date, lignes `Journal` à zéro.

## Contrôles après import

1. Vérifier le résumé global : objets créés, lignes ignorées, lignes bloquées, avertissements.
2. Relire le détail par feuille dans l'interface.
3. Vérifier que les objets créés attendus sont visibles dans l'application.
4. Pour un import `Gestion`, vérifier qu'aucune erreur d'écriture comptable n'a été remontée en avertissement.
5. Si un comportement inattendu apparaît, consulter le journal d'import en base pour récupérer le hash, le statut et le résumé sérialisé.

## Stratégie de secours

1. Si la preview est bloquée : ne rien importer et corriger la source ou la stratégie.
2. Si l'import échoue en cours : considérer l'import comme annulé ; le rollback global doit empêcher les persistances partielles.
3. Si l'import a réussi mais le résultat est métierment faux : restaurer la sauvegarde de base avant de recommencer avec une source corrigée.
4. Si un doute persiste sur la coexistence gestion/comptabilité : privilégier `Gestion` comme source de vérité tant qu'une politique plus fine n'a pas été définie.

## Limitations connues

- La traçabilité détaillée des objets créés est journalisée dans le résumé du log d'import, mais pas encore exposée par une relation dédiée en base.
- La stratégie de coexistence avec des écritures manuelles préexistantes n'est pas encore entièrement formalisée.
- La filière `Gestion` a été répétée jusqu'à l'import complet sur les vrais exports historiques (`2024` puis `2025`) ; la filière `Comptabilite` n'a été validée qu'en preview, conformément à l'ordre recommandé tant qu'elle n'est pas retenue comme source primaire.