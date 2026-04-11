# Plan de fiabilisation de l'import Excel historique

> Document de travail en cours, volontairement non commité à ce stade.
>
> Dernière mise à jour : 2026-04-11
>
> Branche active : `feat-enhance-excel-import`

## Objectif

Rendre l'import des fichiers Excel historiques (`Gestion 2025.xlsx` et `Comptabilite 2025.xlsx`) :

- strict : pas d'import silencieux ou ambigu ;
- diagnosable : la preview doit expliquer exactement ce qui sera importé, ignoré ou bloqué ;
- cohérent : preview et import doivent partager les mêmes règles ;
- sûr : l'import final doit pouvoir être bloqué ou annulé proprement en cas d'incohérence.

## Règle de tenue à jour

Ce fichier doit être mis à jour après chaque tranche significative de travail, avec au minimum :

- le statut des tickets ci-dessous ;
- les validations réellement passées ;
- la prochaine action recommandée ;
- les questions ouvertes encore bloquantes.

## État courant

### Vue macro

- [x] IMP-00 — Profilage des fichiers Excel réels
- [x] IMP-01 — Contrat d'import strict
- [x] IMP-02 — Preview fidèle et diagnostique
- [x] IMP-03 — Couche de normalisation partagée
- [x] IMP-04 — Validation métier globale avant persistance
- [x] IMP-05 — Transaction d'import sûre
- [x] IMP-06 — Coexistence gestion / comptabilité clarifiée
- [x] IMP-07 — Idempotence et traçabilité d'import
- [x] IMP-08 — Rapport de résultat et observabilité renforcés
- [x] IMP-09 — Couverture de tests renforcée
- [x] IMP-10 — UX de confirmation durcie
- [x] IMP-11 — Répétition sur fichiers réels et procédure opératoire

### Résumé d'avancement

- [x] Profilage des vrais classeurs source terminé.
- [x] Preview durcie avec classification explicite des feuilles, diagnostic détaillé, exclusion des feuilles auxiliaires/reporting et blocage visuel si rien n'est importable.
- [x] Frontend aligné sur ce diagnostic détaillé, avec affichage des feuilles reconnues, ignorées, non prises en charge, des colonnes détectées/manquantes et des avertissements/erreurs.
- [x] Couche de normalisation partagée en place pour les feuilles `Factures`, `Paiements`, `Caisse` et `Banque` de gestion.
- [x] Ordre d'import gestion rendu métier et indépendant de l'ordre des onglets du classeur.
- [x] Feuille `Contacts` passée dans la même couche normalisée.
- [x] Premier garde-fou de validation globale en place : un fichier avec une feuille reconnue mais invalide est désormais refusé avant toute écriture partielle.
- [x] Garde-fou transactionnel supplémentaire en place : une erreur tardive pendant l'import annule aussi les écritures déjà flushées.
- [x] Les lignes invalides des feuilles gestion normalisées ne sont plus ignorées silencieusement : elles remontent désormais en erreurs bloquantes de preview/import.
- [x] Les paiements non rapprochables à une facture importée ou déjà présente en base sont désormais bloqués avant persistance.
- [x] La preview gestion réutilise désormais la même validation métier de rapprochement des paiements que l'import.
- [x] Les rapprochements ambigus de paiements ne dépendent plus du premier match SQL : ils sont désormais détectés et bloqués explicitement.
- [x] Les écritures comptables passent désormais elles aussi par une normalisation partagée preview/import, avec erreurs de ligne explicites.
- [x] Les doublons intra-fichier identifiés sur `Contacts` / `Factures` remontent désormais comme lignes ignorées avec avertissements, et non comme skips silencieux.
- [x] Les `Contacts` et `Factures` déjà présents en base sont désormais annoncés dès la preview comme lignes ignorées, avec compteurs alignés sur l'import réel.
- [x] Le rapport preview/import distingue désormais `ignored_rows`, `blocked_rows`, les avertissements globaux et un détail par feuille.
- [x] L'import comptable est désormais bloqué si des écritures auto-générées issues de la gestion existent déjà en base.
- [x] Un premier garde-fou d'idempotence par hash est en place pour bloquer le réimport exact d'un fichier déjà importé avec succès, avec journalisation en base.
- [x] Le journal d'import conserve désormais aussi une trace des objets créés pendant l'import, au-delà des seuls compteurs.
- [x] L'UI de preview distingue maintenant un état "aucune nouveauté importable" d'un état réellement bloquant par erreur.
- [x] Les lignes de total `Factures`, les lignes descriptives d'ouverture `Banque`, les lignes de solde initial `Caisse` et les lignes `Journal` à débit/crédit nuls sont désormais traitées comme lignes ignorées sûres.
- [x] Les exports réels ont été rejoués en preview sur la base locale migrée : `Comptabilite 2024.xlsx` et `Comptabilite 2025.xlsx` sont importables en preview, et les faux positifs réels identifiés sur `Gestion` sont désormais traités comme lignes ignorées sûres.
- [x] La chaîne réelle `Gestion 2024.xlsx -> Gestion 2025.xlsx` a été exécutée avec succès sur la base locale : l'import 2024 crée les factures historiques manquantes, le preview 2025 redevient vert, puis l'import 2025 réussit et le réimport exact est bien rebloqué par hash.
- [x] Un premier noyau de règles métier partagées a été extrait dans `backend/services/excel_import_policy.py` pour centraliser les messages stables et les décisions d'ignorance/dédoublonnage déjà validées.
- [x] Les conteneurs `ImportResult` et `PreviewResult` ont été extraits dans `backend/services/excel_import_results.py`, avec validation unitaire dédiée.
- [x] Les helpers purs de parsing/normalisation et la classification des feuilles ont été extraits respectivement dans `backend/services/excel_import_parsing.py` et `backend/services/excel_import_classification.py`, sans régression fonctionnelle observée.
- [x] Les helpers de structure de feuille (détection d'en-tête, lecture sécurisée, recherche de colonnes, composition de descriptions) ont été extraits dans `backend/services/excel_import_sheet_helpers.py`, toujours sans régression fonctionnelle observée.
- [x] Les helpers de preview/diagnostic (construction des feuilles de preview, agrégation d'avertissements/erreurs, comptage des contacts candidats) ont été extraits dans `backend/services/excel_import_preview_helpers.py`, toujours sans régression fonctionnelle observée.
- [x] Le matching des paiements a été extrait dans `backend/services/excel_import_payment_matching.py` (candidats, déduplication, résolution par référence/contact, chargement des candidats DB), toujours sans régression fonctionnelle observée.
- [x] Les helpers d'état DB et de traçabilité (hash fichier, recherche de réimport, chargement des clés déjà présentes, garde-fou de coexistence comptable, journal d'import) ont été extraits dans `backend/services/excel_import_state.py`, toujours sans régression fonctionnelle observée.
- [x] Les diagnostics backend sont désormais structurés en sortie d'API (`error_details` / `warning_details`, globaux et par feuille) tout en conservant les messages texte existants pour compatibilité UI.
- [x] Les parseurs de feuilles et leurs types normalisés ont été extraits dans `backend/services/excel_import_parsers.py` et `backend/services/excel_import_types.py`, avec une couverture unitaire dédiée par type de feuille.
- [x] La couche `excel_import_policy` centralise désormais aussi les motifs stables de lignes `Contacts` / `Factures` déjà présentes en base, le dédoublonnage métier par type de ligne et les avertissements de preview pour feuilles ignorées/non reconnues.
- [x] La couche `excel_import_policy` centralise désormais aussi les messages stables de validation de ligne et le contrat minimal de colonnes requises par type de feuille, réutilisés par les parseurs partagés.
- [x] La couche `excel_import_policy` centralise désormais aussi le formatage stable des issues de ligne / colonnes manquantes / blocages paiement, réutilisé par la preview et l'import, avec une première catégorisation stable exposée dans `error_details` / `warning_details`.
- [x] La première catégorisation stable des diagnostics structurés couvre désormais aussi les feuilles reconnues mais incomplètes (`*-missing-columns`) et les erreurs de validation de ligne génériques par type (`*-validation-error`) quand aucun code plus précis n'est disponible.
- [x] La réconciliation preview/base pour les `Contacts` / `Factures` déjà présents en base est désormais aussi portée par des helpers dédiés dans `excel_import_policy.py`, au lieu d'être réassemblée localement dans `excel_import.py`.
- [x] La décision métier de blocage/acceptation d'un paiement selon le résultat de matching est désormais partagée via `excel_import_policy.py`, avec distinction explicite entre preview (match workbook acceptable) et import (cible persistable requise).
- [x] Les constructions répétées de feuilles preview ignorées ou à structure non reconnue passent désormais aussi par des helpers dédiés dans `excel_import_preview_helpers.py`, au lieu d'être réassemblées localement dans `excel_import.py`.
- [x] La finalisation preview d'une feuille reconnue/incomplète passe désormais aussi par `append_finalized_sheet_preview(...)`, au lieu d'assembler localement `status`, `blocked_rows` et l'erreur `missing-columns` dans `excel_import.py`.
- [x] Le contrat stable de détection rapide des en-têtes preview par type de feuille gestion est désormais centralisé via `detect_gestion_preview_header(...)`, au lieu d'être codé en branches locales dans `excel_import.py`.
- [x] La finalisation globale de `preview.can_import` après validations DB est désormais mutualisée via `finalize_preview_can_import(...)`, au lieu d'être répétée dans les previews gestion et comptabilité.
- [x] Le message stable d'échec d'ouverture du classeur Excel est désormais mutualisé via `append_preview_open_error(...)`, au lieu d'être réassemblé localement dans les previews gestion et comptabilité.
- [x] Les messages stables d'échec d'ouverture et d'erreur d'import backend sont désormais mutualisés via `ImportResult`, au lieu d'être réassemblés localement dans `excel_import.py`.
- [x] Le branchement preview `kind is None` est désormais mutualisé via `append_reasoned_ignored_sheet_preview(...)`, au lieu de recalculer localement `status` et le warning optionnel dans les previews gestion et comptabilité.
- [x] La résolution `facture -> contact` est désormais strictement partagée entre preview et import : match exact normalisé unique accepté, aucun match = création, plusieurs matches = blocage explicite.
- [x] Les derniers diagnostics globaux structurés disposent maintenant aussi de catégories stables (`already-imported`, `comptabilite-coexistence-blocked`, `import-error`).
- [x] L'UX frontend impose désormais une preview valide avant tout import, réinitialise cette confirmation quand le type de fichier change, conserve la preview affichée pendant l'import et exige une confirmation explicite des avertissements avant exécution.
- [x] Validation globale avant persistance terminée pour les cas métier explicitement couverts par le contrat actuel.

### Dernière tranche terminée

- [x] Extraction de parseurs normalisés partagés pour `Factures` et `Paiements`.
- [x] Alignement preview/import sur le cas des paiements retrouvés via le contact quand la référence de facture est absente.
- [x] Régression sur l'ordre des feuilles corrigée : `Paiements` avant `Factures` ne casse plus l'import.
- [x] Extension de la même approche aux feuilles `Caisse` et `Banque`.
- [x] Détection d'en-têtes rendue accent-insensible pour éviter les écarts `Entrée` / `Entree`, `Débit` / `Debit`, etc.
- [x] Normalisation partagée ajoutée pour `Contacts`, y compris quand la colonne `Prénom` est absente.
- [x] Blocage de l'import avant persistance si la preview détecte des erreurs sur une feuille reconnue.
- [x] Rollback global validé si une feuille plus tardive échoue après des flush intermédiaires.
- [x] Remontée explicite des erreurs de ligne sur `Factures`, `Paiements`, `Contacts`, `Caisse` et `Banque` au lieu d'un skip silencieux.
- [x] Validation métier partagée preview/import pour bloquer les paiements sans facture rapprochable.
- [x] Preview gestion branchée sur la base pour refléter aussi les rapprochements possibles via des factures déjà existantes.
- [x] Résolution des paiements refactorée pour distinguer les cas `unique`, `ambigu` et `introuvable`.
- [x] Blocage des rapprochements ambigus par référence de facture partielle ou par contact multi-factures.
- [x] Parseur normalisé partagé ajouté pour les écritures du `Journal` comptable.
- [x] Les lignes comptables invalides ne sont plus ignorées silencieusement en preview/import.
- [x] Distinction explicite entre lignes importées, ignorées et bloquées dans le résultat backend et l'UI.
- [x] Réconciliation preview/base ajoutée pour marquer aussi les `Contacts` / `Factures` déjà existants comme lignes ignorées avant import.
- [x] Garde-fou de coexistence ajouté : preview/import comptabilité refusés si des écritures de gestion auto-générées existent déjà.
- [x] Journal d'import minimal ajouté avec hash fichier, statut, nom de fichier et résumé sérialisé.
- [x] Blocage du réimport exact sur gestion et comptabilité quand un hash a déjà été importé avec succès.
- [x] Le résumé sérialisé du journal d'import inclut maintenant la liste des objets créés pendant l'import.
- [x] Ajout de garde-fous sur les motifs réels observés dans les exports historiques : lignes de total/synthèse ignorées, montants signés en `Caisse` acceptés, écritures `Journal` à zéro ignorées.
- [x] Dry-run réel rejoué après migration locale `0011` : la prévision de remise d'espèces sans date est désormais ignorée, et les derniers paiements ambigus de `Gestion 2025.xlsx` sont levés en important d'abord l'exercice précédent `Gestion 2024.xlsx`.
- [x] Import réel de `Gestion 2024.xlsx` validé sur base locale (`46` contacts, `263` factures, `268` paiements, `102` mouvements de caisse, `210` transactions bancaires créés ; `2` lignes ignorées, `0` blocage).
- [x] Preview DB-aware de `Gestion 2025.xlsx` rejoué après import 2024 : vert (`14` contacts, `183` factures, `183` paiements estimés ; `0` erreur bloquante).
- [x] Import réel de `Gestion 2025.xlsx` validé sur base locale (`14` contacts, `183` factures, `183` paiements, `75` mouvements de caisse, `145` transactions bancaires créés ; `12` lignes ignorées, `0` blocage), puis réimport exact correctement refusé par le garde-fou de hash.
- [x] Extraction d'une couche `excel_import_policy` pour mutualiser les règles d'ignorance (`Total`, `solde initial`, prévision de remise d'espèces, solde descriptif banque, écriture journal nulle), les messages de rapprochement paiement et le dédoublonnage.
- [x] Régression couverte par une nouvelle suite unitaire `tests/unit/test_excel_import_policy.py` (`8` tests verts) plus la suite d'intégration d'import inchangée (`35` tests verts).
- [x] Extraction d'un module `excel_import_results` pour isoler les structures de retour preview/import et sécurisation par une suite unitaire `tests/unit/test_excel_import_results.py` (`2` tests verts).
- [x] Extraction d'un module `excel_import_parsing` pour isoler les conversions et normalisations pures, sécurisée par `tests/unit/test_excel_import_parsing.py` (`8` tests verts).
- [x] Extraction d'un module `excel_import_classification` pour isoler la reconnaissance des feuilles et la détection de contenu, sécurisée par `tests/unit/test_excel_import_classification.py` (`6` tests verts).
- [x] Extraction d'un module `excel_import_sheet_helpers` pour isoler la structure des feuilles et la lecture de lignes/colonnes, sécurisée par `tests/unit/test_excel_import_sheet_helpers.py` (`6` tests verts).
- [x] Extraction d'un module `excel_import_preview_helpers` pour isoler les helpers de preview/diagnostic, sécurisée par `tests/unit/test_excel_import_preview_helpers.py` (`5` tests verts).
- [x] Extraction d'un module `excel_import_payment_matching` pour isoler les types et helpers de rapprochement paiement, sécurisée par `tests/unit/test_excel_import_payment_matching.py` (`8` tests verts).
- [x] Extraction d'un module `excel_import_state` pour isoler l'état DB, l'idempotence et la journalisation d'import, sécurisée par `tests/unit/test_excel_import_state.py` (`6` tests verts).
- [x] Structuration des diagnostics preview/import dans `excel_import_results`, avec exposition API couverte par `tests/unit/test_excel_import_results.py` (`3` tests verts) et la suite d'intégration d'import (`35` tests verts).
- [x] Extraction d'un module `excel_import_parsers` et d'un module `excel_import_types` pour isoler les parseurs métier par feuille et les lignes normalisées, sécurisée par `tests/unit/test_excel_import_parsers.py` (`6` tests verts).
- [x] Durcissement du flux frontend d'import : bouton principal désactivé tant qu'aucune preview valide n'existe, accusé de réception requis en présence d'avertissements et invalidation automatique de la preview si le type de fichier change.
- [x] IMP-01 a progressé avec l'extraction dans `excel_import_policy` des motifs stables `deja existant`, des avertissements de preview sur feuilles ignorées/non reconnues et des helpers de dédoublonnage `Contacts` / `Factures`, réutilisés en preview et en import.
- [x] IMP-01 a progressé avec l'extraction dans `excel_import_policy` des messages stables de validation de ligne (`montant manquant`, `date invalide`, `compte manquant`, etc.) et du contrat minimal de colonnes requises par type de feuille, désormais consommés par `excel_import_parsers`.
- [x] IMP-01 a progressé avec l'extraction dans `excel_import_policy` du formatage stable des row issues / ignored issues / blocked issues encore assemblés dans `excel_import.py`, plus une première `category` stable dans les diagnostics structurés de `excel_import_results`.
- [x] IMP-01 a progressé avec l'extension de cette `category` stable aux feuilles reconnues mais incomplètes et aux erreurs de validation de ligne non mappées précisément, désormais ramenées à des catégories métier par type de feuille.
- [x] IMP-01 a progressé avec l'extraction dans `excel_import_policy` des règles de repérage preview DB-aware des `Contacts` / `Factures` déjà présents, réutilisées par `excel_import.py` avant marquage en lignes ignorées.
- [x] IMP-01 a progressé avec l'extraction dans `excel_import_policy` de la décision de blocage/acceptation des paiements après matching, réutilisée à la fois dans la preview DB-aware et dans l'import réel.
- [x] IMP-01 a progressé avec l'extraction dans `excel_import_preview_helpers` des constructions répétées de feuilles preview ignorées / structure non reconnue, réutilisées dans les previews gestion et comptabilité.
- [x] IMP-01 a progressé avec l'extraction dans `excel_import_preview_helpers` de la finalisation commune des feuilles preview reconnues / incomplètes (`append_finalized_sheet_preview`), réutilisée dans les previews gestion et comptabilité.
- [x] IMP-01 a progressé avec la centralisation dans `excel_import_policy` des signatures stables de détection rapide des en-têtes preview par type de feuille gestion, réutilisées par `excel_import.py`.
- [x] IMP-01 a progressé avec l'extraction dans `excel_import_preview_helpers` de la finalisation globale `preview.can_import = preview.can_import and not preview.errors`, réutilisée dans les previews gestion et comptabilité.
- [x] IMP-01 a progressé avec l'extraction dans `excel_import_preview_helpers` du message stable d'échec d'ouverture Excel, réutilisé dans les previews gestion et comptabilité.
- [x] IMP-01 a progressé avec la centralisation dans `excel_import_results` des messages stables `Impossible d'ouvrir le fichier` et `Erreur import ...`, réutilisés par les imports gestion, comptabilité et par les imports de feuilles.
- [x] IMP-01 a progressé avec l'extraction dans `excel_import_preview_helpers` du branchement partagé `kind is None`, désormais mutualisé pour les previews gestion et comptabilité avec calcul commun de `status` et du warning optionnel.
- [x] IMP-06 est désormais fermé : la coexistence avec des écritures comptables `MANUAL` est explicitement autorisée, tandis que seules les écritures auto-générées issues de la gestion bloquent preview/import comptabilité.
- [x] IMP-07 est désormais fermé : la cible de traçabilité est explicitement figée au niveau `import_logs` + `created_objects` sérialisés, sans relation SQL dédiée par objet à ce stade.
- [x] IMP-05 est désormais fermé : les erreurs de flush attrapées localement dans les imports de feuilles provoquent aussi l'abandon de l'import global, le reset des compteurs et un log `failed`.
- [x] IMP-04 est désormais fermé : les ambiguïtés restantes connues sont maintenant bloquées explicitement avant persistance, y compris la résolution `facture -> contact` quand plusieurs contacts existants correspondent exactement.
- [x] IMP-01 est désormais fermé : les décisions métier stables et leurs diagnostics structurés sont maintenant centralisés, y compris la résolution stricte `facture -> contact` et les catégories globales résiduelles.

### Validations vertes connues

- [x] `pytest tests/integration/test_import_api.py` : 35 tests verts.
- [x] `pytest tests/unit/test_excel_import_policy.py tests/unit/test_excel_import_results.py tests/unit/test_excel_import_parsing.py tests/unit/test_excel_import_parsers.py tests/unit/test_excel_import_classification.py tests/unit/test_excel_import_sheet_helpers.py tests/unit/test_excel_import_preview_helpers.py tests/unit/test_excel_import_payment_matching.py tests/unit/test_excel_import_state.py tests/integration/test_import_api.py` : 91 tests verts.
- [x] `pytest tests/unit/test_excel_import_policy.py` : 16 tests verts.
- [x] `pytest tests/unit/test_excel_import_policy.py tests/unit/test_excel_import_results.py` : 23 tests verts.
- [x] `pytest tests/unit/test_excel_import_policy.py tests/unit/test_excel_import_results.py` : 25 tests verts.
- [x] `pytest tests/unit/test_excel_import_policy.py tests/unit/test_excel_import_parsers.py` : 22 tests verts.
- [x] `pytest tests/unit/test_excel_import_policy.py` : 23 tests verts.
- [x] `pytest tests/unit/test_excel_import_policy.py` : 26 tests verts.
- [x] `pytest tests/unit/test_excel_import_policy.py` : 28 tests verts.
- [x] `pytest tests/unit/test_excel_import_preview_helpers.py` : 7 tests verts.
- [x] `pytest tests/unit/test_excel_import_preview_helpers.py` : 9 tests verts.
- [x] `pytest tests/unit/test_excel_import_preview_helpers.py` : 11 tests verts.
- [x] `pytest tests/unit/test_excel_import_preview_helpers.py` : 12 tests verts.
- [x] `pytest tests/unit/test_excel_import_preview_helpers.py` : 14 tests verts.
- [x] `pytest tests/unit/test_excel_import_results.py` : 6 tests verts.
- [x] `pytest tests/unit/test_excel_import_policy.py tests/unit/test_excel_import_results.py tests/unit/test_excel_import_preview_helpers.py` : 54 tests verts.
- [x] `pytest tests/integration/test_import_api.py -k "existing_contact or existing_invoice or auxiliary_sheets"` : 4 tests verts.
- [x] `pytest tests/integration/test_import_api.py -k "missing_required_invoice_data or block_payment_without_match or block_row_with_missing_account or block_row_with_invalid_amounts"` : 4 tests verts.
- [x] `pytest tests/integration/test_import_api.py -k "missing_required_invoice_data or block_payment_without_match or existing_contact or existing_invoice"` : 5 tests verts.
- [x] `pytest tests/integration/test_import_api.py -k "missing_required_invoice_data or block_payment_without_match or existing_contact or existing_invoice or recognized_sheet_is_invalid"` : 6 tests verts.
- [x] `pytest tests/integration/test_import_api.py -k "existing_contact or existing_invoice"` : 3 tests verts.
- [x] `pytest tests/integration/test_import_api.py -k "block_payment_without_match or ambiguous_invoice_reference or ambiguous_contact_match or matched_against_existing_invoice"` : 4 tests verts.
- [x] `pytest tests/integration/test_import_api.py -k "auxiliary_sheets or recognized_sheet_is_invalid"` : 2 tests verts.
- [x] `pytest tests/integration/test_import_api.py -k "auxiliary_sheets or recognized_sheet_is_invalid or estimates_contacts_from_invoices_and_payments or accept_contacts_sheet_without_prenom"` : 4 tests verts.
- [x] `pytest tests/integration/test_import_api.py -k "auxiliary_sheets or estimates_contacts_from_invoices_and_payments or recognized_sheet_is_invalid"` : 3 tests verts.
- [x] `pytest tests/integration/test_import_api.py -k "import_gestion_empty_sheet or import_comptabilite_empty_sheet or preview_and_import_gestion_accept_contacts_sheet_without_prenom or preview_and_import_comptabilite_ignore_zero_amount_rows"` : 4 tests verts.
- [x] `pytest tests/integration/test_import_api.py -k "auxiliary_sheets or recognized_sheet_is_invalid or estimates_contacts_from_invoices_and_payments"` : 3 tests verts.
- [x] `pytest tests/integration/test_import_api.py -k "generated_gestion_entries_exist or existing_manual_entries"` : 2 tests verts.
- [x] `pytest tests/integration/test_import_api.py -k "late_sheet_crashes or flush_error_is_caught_locally or generated_gestion_entries_exist or existing_manual_entries"` : 4 tests verts.
- [x] `pytest tests/integration/test_import_api.py -k "ambiguous_existing_contact or generated_gestion_entries_exist or blocks_reimport_of_same_file"` : 4 tests verts.
- [x] `pytest tests/integration/test_import_api.py -k "ambiguous_existing_contact or missing_required_invoice_data"` : 2 tests verts.
- [x] `npm --prefix frontend run type-check`.
- [x] `npm --prefix frontend run test:unit -- --run src/tests/views/ImportExcelView.spec.ts`.
- [x] Feuilles auxiliaires ignorées.
- [x] `Journal (saisie)` ignoré.
- [x] Estimation des contacts dans la preview.
- [x] Paiements retrouvés via le contact.
- [x] Indépendance vis-à-vis de l'ordre des onglets.
- [x] Cohérence preview/import sur `Caisse` avec colonnes `Entrée` / `Sortie`.
- [x] Cohérence preview/import sur `Banque` avec colonnes `Débit` / `Crédit`.
- [x] Cohérence preview/import sur `Contacts` avec colonne `Nom` sans colonne `Prénom`.
- [x] Blocage des imports partiels lorsqu'une feuille reconnue est invalide.
- [x] Rollback des créations déjà flushées lorsqu'une erreur tardive survient pendant l'import.
- [x] Blocage des lignes de facture invalides avec diagnostic par numéro de ligne.
- [x] Blocage des paiements non rapprochables avec diagnostic partagé preview/import.
- [x] Paiement-only accepté quand une facture existante en base permet le rapprochement.
- [x] Blocage des références de facture ambiguës.
- [x] Blocage des rapprochements ambigus via un contact portant plusieurs factures candidates.
- [x] Blocage des lignes comptables avec compte manquant.
- [x] Blocage des lignes comptables avec montants invalides.
- [x] Lignes de total `Factures` remontées comme ignorées.
- [x] Montants signés acceptés sur `Caisse` en format `Montant` seul, avec maintien du blocage si la date manque.
- [x] Lignes descriptives d'ouverture `Banque` remontées comme ignorées.
- [x] Lignes `Journal` à débit/crédit nuls remontées comme ignorées.
- [x] Prévisions de remise d'espèces `Caisse` sans date remontées comme ignorées quand elles correspondent à un dépôt bancaire futur.
- [x] Doublons de factures intra-fichier remontés comme lignes ignorées avec rapport détaillé.
- [x] Contacts déjà existants en base remontés dès la preview comme lignes ignorées.
- [x] Factures déjà existantes en base remontées dès la preview comme lignes ignorées.
- [x] Blocage des réimports exacts de fichiers gestion déjà importés, avec journalisation des tentatives.
- [x] Blocage des réimports exacts de fichiers comptables déjà importés.
- [x] Blocage de l'import comptable quand des écritures auto-générées de gestion existent déjà.
- [x] Traçabilité des objets créés vérifiée dans le journal d'import.
- [x] Preview réelle de `Gestion 2024.xlsx` verte (`46` contacts estimés, `263` factures, `268` paiements, `0` erreur).
- [x] Preview réelle de `Comptabilite 2025.xlsx` verte (`930` écritures estimées, `10` lignes ignorées, `0` erreur).
- [x] Preview réelle de `Comptabilite 2024.xlsx` verte (`1385` écritures estimées, `20` lignes ignorées, `0` erreur).
- [x] Preview réelle de `Gestion 2025.xlsx` verte après import préalable de `Gestion 2024.xlsx` (`14` contacts estimés, `183` factures, `183` paiements, `0` erreur).
- [x] Import réel de `Gestion 2024.xlsx` réussi sur base locale.
- [x] Import réel de `Gestion 2025.xlsx` réussi sur base locale.
- [x] Réimport exact de `Gestion 2025.xlsx` rebloqué par hash après succès du premier import.

## Backlog de travail

### IMP-00 — Profiler les fichiers Excel réels

- [x] Ticket terminé
- But : comprendre les vrais onglets, en-têtes, variantes de colonnes et feuilles parasites.
- [x] Profiling de `Gestion 2025.xlsx` effectué.
- [x] Profiling de `Comptabilite 2025.xlsx` effectué.
- [x] Feuilles métier et feuilles auxiliaires/reporting identifiées.

### IMP-01 — Définir le contrat d'import strict

- [x] Ticket terminé
- But : formaliser ce qui est accepté, ignoré, bloquant, déductible ou ambigu.
- [x] Formaliser une première version du contrat dans `doc/dev/import-excel-contract.md`.
- [x] Centraliser les règles d'acceptation, d'ignorance et de blocage dans une couche métier dédiée.
- [x] Extraire un premier noyau de règles partagées dans `backend/services/excel_import_policy.py`.
- [x] Sortir les règles métier stables et leurs diagnostics des fonctions d'import dispersées, en ne laissant dans `excel_import.py` que l'orchestration résiduelle.
- [x] Centraliser les motifs stables `Contacts` / `Factures` déjà présents en base et les avertissements de preview de feuilles ignorées/non reconnues.
- [x] Centraliser le dédoublonnage métier `Contacts` / `Factures` dans la couche de politique.
- [x] Centraliser les messages stables de validation de ligne et le contrat minimal de colonnes requises par type de feuille.
- [x] Centraliser le formatage stable des diagnostics de ligne (`ignored` / `blocked` / colonnes manquantes / blocages paiement) et amorcer une `category` structurée compatible avec l'API actuelle.
- [x] Étendre cette `category` structurée aux erreurs de validation encore trop génériques et aux cas `missing-columns` par type de feuille.
- [x] Sortir de `excel_import.py` la logique preview DB-aware de repérage des `Contacts` / `Factures` déjà existants.
- [x] Sortir de `excel_import.py` la décision métier partagée qui transforme un résultat de matching paiement en blocage de preview ou d'import.
- [x] Sortir de `excel_import.py` la construction répétée des previews de feuilles ignorées / structure non reconnue.
- [x] Définir explicitement les cas ambigus actuellement connus et leur stratégie de traitement.

### IMP-02 — Rendre la preview fidèle et diagnostique

- [x] Ticket terminé
- But : faire de la preview un reflet fiable de l'import réel.
- [x] Classification explicite des feuilles gestion/comptabilité.
- [x] Exclusion des feuilles d'aide, TODO, reporting et `Journal (saisie)`.
- [x] Diagnostic par feuille (`status`, `kind`, colonnes détectées/manquantes, avertissements, erreurs).
- [x] Calcul de `can_import` côté backend.
- [x] Affichage frontend exploitable en clair.

### IMP-03 — Introduire une couche de normalisation partagée

- [x] Ticket terminé
- But : parser les feuilles en structures normalisées, réutilisées à la fois par la preview et l'import.
- [x] `Factures` : normalisation partagée en lignes de facture.
- [x] `Paiements` : normalisation partagée en lignes de paiement.
- [x] `Caisse` : normalisation partagée en mouvements de caisse.
- [x] `Banque` : normalisation partagée en transactions bancaires.
- [x] `Contacts` : normalisation partagée en lignes de contact.
- [x] Import gestion dans l'ordre métier `contacts -> invoices -> payments -> cash -> bank`.
- [x] `Journal` comptable : normalisation partagée en lignes d'écriture.

### IMP-04 — Ajouter une validation métier globale avant persistance

- [x] Ticket terminé
- But : distinguer clairement :
- [x] Bloquer l'import complet si la preview détecte déjà une feuille reconnue invalide.
- [x] Les lignes valides.
- [x] Les lignes ignorables.
- [x] Les erreurs bloquantes.
- [x] Les ambiguïtés nécessitant arbitrage.
- [x] Remonter les erreurs de ligne bloquantes pour les feuilles gestion normalisées.
- [x] Bloquer les paiements sans facture rapprochable avant toute persistance.
- [x] Bloquer les rapprochements ambigus au lieu de choisir arbitrairement un candidat.
- [x] Étendre le même principe aux lignes d'écritures comptables invalides.
- [x] Distinguer un premier lot de lignes ignorables sûres (`Contacts` / `Factures` en doublon intra-fichier) des erreurs bloquantes.
- [x] Étendre ce lot aux `Contacts` / `Factures` déjà présents en base avec alignement preview/import.
- [x] Étendre ce lot aux lignes de total/synthèse sûres réellement observées (`Factures`, `Banque`, `Caisse`, `Journal`).
- [x] Étendre ce lot aux prévisions de remise d'espèces `Caisse` sans date quand elles représentent un futur dépôt bancaire explicite.
- [x] Commencer à sortir ces règles et leurs messages stables dans une couche dédiée `excel_import_policy`.
- Cible : produire un rapport exploitable avant tout flush significatif en base.

### IMP-05 — Garantir une transaction d'import sûre

- [x] Ticket terminé
- But : éviter les imports partiels incohérents.
- [x] Bloquer l'import proprement en cas d'erreur bloquante détectée en preview/validation partagée.
- [x] Garantir l'absence de données partielles persistées sur échec tardif d'une feuille ultérieure.
- [x] Propager aussi les erreurs de flush attrapées localement dans les imports de feuilles pour que l'orchestrateur global stoppe, remette les compteurs à zéro et logue l'import en `failed`.

### IMP-06 — Clarifier la coexistence entre gestion et comptabilité

- [x] Ticket terminé
- But : éviter les doublons ou incohérences entre :
- [x] Définir une première source de vérité pratique : si des écritures auto-générées issues de la gestion existent déjà, elles priment sur un import comptable global.
- [x] Définir un premier cas d'autorisation : l'import comptable n'est autorisé que s'il n'existe pas encore d'écritures auto-générées issues de la gestion.
- [x] Définir un premier garde-fou anti-doublon sur les écritures : blocage explicite preview/import comptabilité en présence d'écritures générées.
- [x] Clarifier la stratégie cible si des écritures manuelles coexistent déjà avec un futur import comptable.

### IMP-07 — Gérer l'idempotence et la traçabilité d'import

- [x] Ticket terminé
- But : pouvoir répondre à deux questions :
- [x] Savoir si un fichier a déjà été importé.
- [x] Savoir quelles données ont été créées par quel import.
- [x] Ajouter un journal d'import, un hash ou une signature de fichier.
- [x] Ajouter des garde-fous anti-réinjection.
- [x] Journaliser dans le résumé d'import les objets créés pendant l'exécution.
- [x] Décider que la traçabilité cible actuelle reste le journal d'import + `created_objects` sérialisés, sans relation SQL dédiée par objet à ce stade.

### IMP-08 — Améliorer le rapport de résultat et l'observabilité

- [x] Ticket terminé
- But : fournir un compte rendu final plus utile qu'un simple compteur.
- [x] Structurer les erreurs.
- [x] Structurer les avertissements par feuille.
- [x] Ajouter un résumé par type d'objet créé ou ignoré.
- [x] Exposer côté UI un détail par feuille avec lignes importées, ignorées, bloquées et avertissements.
- [x] Exposer côté API des diagnostics structurés globaux et par feuille, en conservant les messages texte existants pour compatibilité.

### IMP-09 — Renforcer la couverture de tests

- [x] Ticket terminé
- [x] Suite d'intégration d'import couvrant plusieurs régressions importantes.
- [x] 35 tests verts sur `tests/integration/test_import_api.py`.
- [x] 6 tests verts sur `tests/unit/test_excel_import_classification.py`.
- [x] 8 tests verts sur `tests/unit/test_excel_import_parsing.py`.
- [x] 6 tests verts sur `tests/unit/test_excel_import_parsers.py`.
- [x] 8 tests verts sur `tests/unit/test_excel_import_payment_matching.py`.
- [x] 6 tests verts sur `tests/unit/test_excel_import_state.py`.
- [x] 16 tests verts sur `tests/unit/test_excel_import_policy.py`.
- [x] 3 tests verts sur `tests/unit/test_excel_import_results.py`.
- [x] 6 tests verts sur `tests/unit/test_excel_import_sheet_helpers.py`.
- [x] 5 tests verts sur `tests/unit/test_excel_import_preview_helpers.py`.
- [x] Ajouter des tests sur `Contacts`.
- [x] Ajouter des tests de validation bloquante.
- [x] Ajouter des tests de rollback.
- [x] Ajouter des tests de non-réimport / idempotence.
- [x] Ajouter des tests de lignes ignorées déjà présentes en base.
- [x] Ajouter des tests sur les motifs réels observés dans les exports historiques (`Total`, `solde initial`, montants signés, `Journal` à zéro).

### IMP-10 — Durcir l'UX de confirmation d'import

- [x] Ticket terminé
- [x] Blocage du bouton de confirmation si `can_import` est faux.
- [x] Preview beaucoup plus lisible.
- [x] Distinguer en preview un état sans nouveauté importable d'un état réellement bloquant.
- [x] Exiger une preview valide avant tout import depuis l'action principale.
- [x] Invalider la preview confirmée si le type de fichier change.
- [x] Conserver la preview affichée pendant l'import pour confirmer en contexte.
- [x] Exiger une confirmation explicite des avertissements avant l'import.

### IMP-11 — Répétition sur fichiers réels et procédure opératoire

- [x] Ticket terminé
- But : tester la chaîne complète sur les vrais exports historiques et documenter une procédure de reprise fiable.
- [x] Tester la chaîne complète sur les vrais exports historiques selon le chemin opératoire retenu (`Gestion` comme source primaire).
- [x] Rejouer la preview réelle sur `Gestion 2025.xlsx` et `Comptabilite 2025.xlsx`.
- [x] Réduire les blocages réels aux seuls cas de donnée encore ambigus ou incomplets.
- [x] Vérifier que l'import de l'exercice précédent lève bien les ambiguïtés métier de l'exercice courant.
- [x] Exécuter avec succès la chaîne réelle `Gestion 2024.xlsx -> Gestion 2025.xlsx`.
- [x] Vérifier le blocage de réimport exact après import réel réussi.
- [x] Documenter une check-list d'import.
- [x] Documenter l'ordre recommandé.
- [x] Documenter les points de contrôle post-import.
- [x] Documenter la stratégie de secours.
- [x] Centraliser cette première procédure dans `doc/dev/import-excel-procedure.md`.

## Fichiers actuellement concernés

- `backend/services/excel_import.py`
- `backend/services/excel_import_classification.py`
- `backend/services/excel_import_parsing.py`
- `backend/services/excel_import_policy.py`
- `backend/services/excel_import_preview_helpers.py`
- `backend/services/excel_import_results.py`
- `backend/services/excel_import_sheet_helpers.py`
- `backend/routers/excel_import.py`
- `backend/models/import_log.py`
- `backend/alembic/versions/0011_add_import_logs.py`
- `doc/dev/import-excel-contract.md`
- `doc/dev/import-excel-procedure.md`
- `frontend/src/api/accounting.ts`
- `frontend/src/tests/views/ImportExcelView.spec.ts`
- `frontend/src/views/ImportExcelView.vue`
- `frontend/src/i18n/fr.ts`
- `tests/unit/test_excel_import_classification.py`
- `tests/unit/test_excel_import_parsing.py`
- `tests/unit/test_excel_import_policy.py`
- `tests/unit/test_excel_import_preview_helpers.py`
- `tests/unit/test_excel_import_results.py`
- `tests/unit/test_excel_import_sheet_helpers.py`
- `tests/integration/test_import_api.py`

## Point de reprise recommandé

La prochaine tranche utile ne porte plus sur l'UX de confirmation, désormais verrouillée côté frontend, mais sur les chantiers structurels encore ouverts du moteur d'import.

Ordre recommandé :

1. [ ] formaliser les règles globales de validation par type de feuille dans une couche métier dédiée ;
2. [ ] étendre encore la catégorisation stable au-delà du lot déjà couvert (`existing`, `duplicate`, `missing-columns`, erreurs de paiement, avertissements de feuille, `*-validation-error`) vers les derniers messages libres encore présents ;
3. [ ] clarifier la stratégie de coexistence cible avec d'éventuelles écritures manuelles avant d'ouvrir la voie d'import `Comptabilite` en réel ;
4. [ ] décider si la traçabilité actuelle via résumé de log suffit, ou si une relation dédiée par objet créé devient nécessaire.

## Questions ouvertes

- Quelle politique exacte veut-on pour l'import comptable si des écritures auto-générées existent déjà côté gestion ?
- Souhaite-t-on conserver un mode d'import partiel avec avertissements, ou viser un mode strictement bloquant dès qu'une feuille reconnue est incohérente ?
- Faut-il rester sur une traçabilité journalisée dans le résumé d'import, ou faut-il lier explicitement chaque objet créé à un import source par une relation dédiée ?

## Journal synthétique

### 2026-04-11

- IMP-03 a progressé avec la normalisation partagée `Factures` / `Paiements`.
- L'ordre des feuilles n'est plus un facteur de comportement pour l'import gestion.
- IMP-03 a été étendu à `Caisse` et `Banque`, avec alignement preview/import sur des colonnes séparées `Entrée` / `Sortie` et `Débit` / `Crédit`.
- La détection d'en-têtes est désormais accent-insensible.
- IMP-03 a été complété pour `Contacts`, y compris sur une feuille sans colonne `Prénom`.
- IMP-04 a commencé avec un premier garde-fou : un fichier contenant une feuille reconnue mais invalide est désormais refusé avant tout import partiel.
- IMP-05 a commencé avec un rollback global validé sur erreur tardive pendant l'import.
- IMP-04 a progressé avec des erreurs de ligne désormais explicites et bloquantes sur les feuilles gestion normalisées.
- IMP-04 / IMP-05 ont progressé avec une validation partagée preview/import des paiements non rapprochables, y compris contre les factures déjà présentes en base.
- IMP-04 / IMP-05 ont progressé avec le blocage explicite des rapprochements ambigus de paiements par référence ou par contact.
- IMP-03 / IMP-04 ont progressé avec une normalisation partagée des écritures comptables et le blocage explicite des lignes journal invalides.
- IMP-04 / IMP-08 ont progressé avec une distinction explicite entre lignes importées, ignorées et bloquées, plus des avertissements détaillés par feuille côté backend et frontend.
- IMP-07 a commencé avec un journal d'import minimal et un blocage par hash des réimports exacts déjà importés avec succès.
- IMP-06 a commencé avec un blocage explicite de l'import comptable si des écritures auto-générées issues de la gestion existent déjà en base.
- IMP-07 a progressé avec une traçabilité des objets créés directement stockée dans le résumé du journal d'import.
- IMP-01 a commencé avec un contrat d'import explicité dans `doc/dev/import-excel-contract.md`.
- IMP-11 a commencé avec une première procédure opératoire documentée dans `doc/dev/import-excel-procedure.md`.
- IMP-10 a progressé avec une distinction UI entre preview bloquée et preview sans nouveauté importable.
- IMP-04 / IMP-11 ont progressé avec la prise en compte explicite de motifs réels d'exports : lignes `Total` ignorées, lignes descriptives d'ouverture `Banque` ignorées, lignes de solde initial `Caisse` ignorées et montants signés `Caisse` acceptés.
- IMP-04 / IMP-11 ont progressé avec l'ignorance explicite des prévisions de remise d'espèces sans date quand elles correspondent à un dépôt bancaire futur.
- IMP-04 / IMP-11 ont progressé avec l'ignorance explicite des lignes `Journal` à débit/crédit nuls.
- La base locale de répétition a été migrée au schéma courant (`0011`) pour permettre les previews DB-aware avec `import_logs`.
- La suite `tests/integration/test_import_api.py` est verte avec 35 tests.
- Une nouvelle couche `backend/services/excel_import_policy.py` centralise un premier socle de règles et messages métier, couverte par `tests/unit/test_excel_import_policy.py` (8 tests verts).
- `backend/services/excel_import_policy.py` centralise désormais aussi les motifs stables `deja existant`, les avertissements de preview pour feuilles ignorées/non reconnues et le dédoublonnage métier `Contacts` / `Factures`, couverts par `tests/unit/test_excel_import_policy.py` (16 tests verts).
- `backend/services/excel_import_policy.py` centralise désormais aussi les messages stables de validation de ligne et le contrat minimal de colonnes requises, réutilisés dans `backend/services/excel_import_parsers.py` et validés par `tests/unit/test_excel_import_policy.py` + `tests/unit/test_excel_import_parsers.py` (22 tests verts).
- `backend/services/excel_import_policy.py` centralise désormais aussi le formatage stable des diagnostics de ligne et des colonnes manquantes, réutilisé dans `backend/services/excel_import.py` et `backend/services/excel_import_preview_helpers.py`, tandis que `backend/services/excel_import_results.py` expose une première `category` stable dans les détails structurés, validés par `tests/unit/test_excel_import_policy.py` + `tests/unit/test_excel_import_results.py` (23 tests verts) et un sous-ensemble d'intégration d'import (5 tests verts).
- `backend/services/excel_import_policy.py` catégorise désormais aussi les feuilles reconnues mais incomplètes (`*-missing-columns`) et les erreurs de validation résiduelles via un fallback `*-validation-error` par type de feuille ; cette extension est validée par `tests/unit/test_excel_import_policy.py` + `tests/unit/test_excel_import_results.py` (25 tests verts) et un sous-ensemble d'intégration d'import (6 tests verts).
- `backend/services/excel_import_policy.py` encapsule désormais aussi le repérage preview DB-aware des lignes `Contacts` / `Factures` déjà présentes en base, réutilisé par `backend/services/excel_import.py` et validé par `tests/unit/test_excel_import_policy.py` (23 tests verts) plus le sous-ensemble d'intégration `existing_contact or existing_invoice` (3 tests verts).
- `backend/services/excel_import_policy.py` encapsule désormais aussi la décision partagée issue d'un `PaymentMatchResolution`, avec tolérance des candidats workbook en preview mais exigence d'une cible persistable à l'import ; cette extraction est validée par `tests/unit/test_excel_import_policy.py` (26 tests verts) et le sous-ensemble d'intégration paiement (`4` tests verts).
- `backend/services/excel_import_preview_helpers.py` encapsule désormais aussi la construction des feuilles preview ignorées et des structures non reconnues, réutilisée par `backend/services/excel_import.py` et validée par `tests/unit/test_excel_import_preview_helpers.py` (7 tests verts) plus le sous-ensemble d'intégration `auxiliary_sheets or recognized_sheet_is_invalid` (2 tests verts).
- Les conteneurs `ImportResult` et `PreviewResult` vivent désormais dans `backend/services/excel_import_results.py`, couverts par `tests/unit/test_excel_import_results.py` (2 tests verts).
- Les helpers purs de parsing vivent désormais dans `backend/services/excel_import_parsing.py` et la reconnaissance des feuilles dans `backend/services/excel_import_classification.py`, couvertes respectivement par `8` et `6` tests unitaires verts.
- Les helpers de structure de feuille vivent désormais dans `backend/services/excel_import_sheet_helpers.py`, couverts par `6` tests unitaires verts.
- Les helpers de preview/diagnostic vivent désormais dans `backend/services/excel_import_preview_helpers.py`, couverts par `5` tests unitaires verts.
- Les previews réelles de `Comptabilite 2024.xlsx` et `Comptabilite 2025.xlsx` sont vertes.
- L'import réel de `Gestion 2024.xlsx` a réintroduit les factures historiques `2025-0131` et `2025-0134`, ce qui a levé les ambiguïtés de `Gestion 2025.xlsx`.
- La chaîne réelle `Gestion 2024.xlsx -> Gestion 2025.xlsx` a été exécutée avec succès sur la base locale, et le réimport exact de `Gestion 2025.xlsx` est bien rebloqué par hash.
- IMP-10 a été fermé côté frontend : l'import direct sans preview n'est plus possible, la confirmation est invalidée au changement de type et les avertissements exigent un accusé de réception explicite.
- Un test Vue ciblé couvre désormais ce verrouillage (`3` tests verts).
- Prochain objectif concret : ouvrir un nouveau chantier si nécessaire ; le plan IMP actuel est désormais entièrement traité.
