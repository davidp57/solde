# Procédure opératoire — import Excel historique

## Objectif

Dérouler un import historique `Gestion` ou `Comptabilite` avec un niveau de sûreté compatible avec les garde-fous actuellement en place dans l'application.

Cette procédure sert de check-list opératoire et de base pour les futures répétitions sur fichiers réels.

## Pré-requis

- Travailler sur une base sauvegardée ou facilement restaurable.
- Vérifier que la base locale est au schéma courant avant toute répétition réelle (`alembic upgrade head` si nécessaire).
- Vérifier que le fichier source correspond bien à l'année et au périmètre attendus.
- Disposer d'un export Excel source non modifié manuellement entre deux essais, pour que le garde-fou de hash reste pertinent.
- Créer au préalable les exercices comptables couvrant les périodes importées si l'on veut un rattachement automatique correct des écritures. Sur les exports historiques actuellement rejoués, cela couvre des dates allant de `2022` à `2026`.
- Préparer séparément le plan comptable et, pour la gestion courante, les règles comptables ; l'import Excel ne les crée jamais.

## Ordre recommandé

1. Importer d'abord les fichiers `Gestion` par ordre chronologique si cette filière sert de source métier principale.
2. Importer `Comptabilite` après `Gestion` si le journal doit compléter les écritures déjà générées ; les doublons exacts sont alors ignorés et seules les écritures nouvelles sont ajoutées.
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
- Doublons exacts du `Journal` déjà présents en base lors d'un import `Comptabilite` complémentaire.

## Statut réel constaté au 2026-04-12

- `Gestion 2024.xlsx` : import réel réussi sur base isolée préchargée (plan comptable, règles et exercices `2022` à `2026`) avec `64` contacts, `303` factures, `308` paiements, `1222` écritures, `102` mouvements de caisse et `210` transactions bancaires créés ; `2` lignes ignorées, `0` blocage.
- `Gestion 2024.xlsx` : ces compteurs incluent désormais les factures fournisseurs historiques et leurs règlements reconstruits depuis les références `FF-...` détectées dans `Banque` et `Caisse`.
- `Gestion 2025.xlsx` : la prévision `Caisse` ligne `23` (`Remise espèces`, montant `-710`, date absente) est bien ignorée ; les ambiguïtés de `Paiements` lignes `2` et `3` disparaissent après import préalable de `Gestion 2024.xlsx`, puis l'import réel réussit avec `18` contacts, `211` factures, `211` paiements, `844` écritures, `75` mouvements de caisse et `145` transactions bancaires créés ; `12` lignes ignorées, `0` blocage.
- Le réimport exact de `Gestion 2025.xlsx` est ensuite correctement refusé par le garde-fou de hash.
- `Comptabilite 2024.xlsx` : preview DB-aware verte à `1385` écritures estimées, puis import réel complémentaire validé avec `1367` écritures créées, `23` lignes ignorées et `0` blocage.
- `Comptabilite 2025.xlsx` : preview DB-aware verte à `930` écritures estimées, puis import réel complémentaire validé avec `928` écritures créées, `12` lignes ignorées et `0` blocage.
- Avec les exercices `2022` à `2026` préchargés, le rejeu complet ne laisse aucune écriture importée ou générée sans rattachement à un exercice comptable.
- Les anciens faux positifs réels ont été éliminés : ligne `Total` en `Factures`, lignes descriptives d'ouverture en `Banque`, lignes de solde initial / montants signés en `Caisse`, prévisions de remise d'espèces sans date, lignes `Journal` à zéro.

## Contrôles après import

1. Vérifier le résumé global : objets créés, lignes ignorées, lignes bloquées, avertissements.
2. Relire le détail par feuille dans l'interface.
3. Vérifier que les objets créés attendus sont visibles dans l'application.
4. Vérifier que les écritures importées ou générées sont rattachées au bon exercice quand celui-ci existe déjà.
5. Pour un import `Gestion`, vérifier qu'aucune erreur d'écriture comptable n'a été remontée en avertissement.
6. Si un comportement inattendu apparaît, consulter le journal d'import en base pour récupérer le hash, le statut et le résumé sérialisé.

## Clôture des exercices historiques importés

Après une reprise historique complète, la règle opératoire est la suivante.

1. Ne pas clôturer les exercices historiques pendant les imports.
2. Importer d'abord l'ensemble des fichiers historiques et vérifier les compteurs, les rapprochements et le rattachement aux exercices.
3. Une fois la reprise validée, fermer les anciens exercices via une clôture administrative, c'est-à-dire sans générer de nouvelle écriture de clôture ni de report à nouveau.
4. Réserver la clôture comptable classique de Solde aux exercices réellement tenus dans Solde, pour lesquels l'application doit produire elle-même l'écriture de résultat et le report à nouveau.

Cette distinction évite de dupliquer dans Solde des écritures de clôture déjà présentes dans les journaux Excel importés.

## Stratégie de secours

1. Si la preview est bloquée : ne rien importer et corriger la source ou la stratégie.
2. Si l'import échoue en cours : considérer l'import comme annulé ; le rollback global doit empêcher les persistances partielles.
3. Si l'import a réussi mais le résultat est métierment faux : restaurer la sauvegarde de base avant de recommencer avec une source corrigée.
4. Si un doute persiste sur la coexistence gestion/comptabilité : repartir d'une base restaurée, rejouer `Gestion`, puis importer `Comptabilite` pour mesurer précisément les lignes nouvelles et les doublons exacts ignorés.

## Limitations connues

- La traçabilité détaillée des objets créés est journalisée dans le résumé du log d'import, mais pas encore exposée par une relation dédiée en base.
- La coexistence repose sur une déduplication exacte de lignes comptables ; elle ne couvre pas encore les doublons "métier" proches mais non identiques.
- Les exports historiques actuellement utilisés pour le rejeu couvrent un périmètre de dates plus large que leur seul nom de fichier ; il faut donc préparer tous les exercices réellement couverts avant de juger le rattachement comptable.
