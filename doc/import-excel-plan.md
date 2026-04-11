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
- [ ] IMP-01 — Contrat d'import strict
- [x] IMP-02 — Preview fidèle et diagnostique
- [ ] IMP-03 — Couche de normalisation partagée
- [ ] IMP-04 — Validation métier globale avant persistance
- [ ] IMP-05 — Transaction d'import sûre
- [ ] IMP-06 — Coexistence gestion / comptabilité clarifiée
- [ ] IMP-07 — Idempotence et traçabilité d'import
- [ ] IMP-08 — Rapport de résultat et observabilité renforcés
- [ ] IMP-09 — Couverture de tests renforcée
- [ ] IMP-10 — UX de confirmation durcie
- [ ] IMP-11 — Répétition sur fichiers réels et procédure opératoire

### Résumé d'avancement

- [x] Profilage des vrais classeurs source terminé.
- [x] Preview durcie avec classification explicite des feuilles, diagnostic détaillé, exclusion des feuilles auxiliaires/reporting et blocage visuel si rien n'est importable.
- [x] Frontend aligné sur ce diagnostic détaillé, avec affichage des feuilles reconnues, ignorées, non prises en charge, des colonnes détectées/manquantes et des avertissements/erreurs.
- [x] Couche de normalisation partagée en place pour les feuilles `Factures`, `Paiements`, `Caisse` et `Banque` de gestion.
- [x] Ordre d'import gestion rendu métier et indépendant de l'ordre des onglets du classeur.
- [x] Feuille `Contacts` passée dans la même couche normalisée.
- [x] Premier garde-fou de validation globale en place : un fichier avec une feuille reconnue mais invalide est désormais refusé avant toute écriture partielle.
- [x] Garde-fou transactionnel supplémentaire en place : une erreur tardive pendant l'import annule aussi les écritures déjà flushées.
- [ ] Validation globale avant persistance encore incomplète.

### Dernière tranche terminée

- [x] Extraction de parseurs normalisés partagés pour `Factures` et `Paiements`.
- [x] Alignement preview/import sur le cas des paiements retrouvés via le contact quand la référence de facture est absente.
- [x] Régression sur l'ordre des feuilles corrigée : `Paiements` avant `Factures` ne casse plus l'import.
- [x] Extension de la même approche aux feuilles `Caisse` et `Banque`.
- [x] Détection d'en-têtes rendue accent-insensible pour éviter les écarts `Entrée` / `Entree`, `Débit` / `Debit`, etc.
- [x] Normalisation partagée ajoutée pour `Contacts`, y compris quand la colonne `Prénom` est absente.
- [x] Blocage de l'import avant persistance si la preview détecte des erreurs sur une feuille reconnue.
- [x] Rollback global validé si une feuille plus tardive échoue après des flush intermédiaires.

### Validations vertes connues

- [x] `pytest tests/integration/test_import_api.py` : 16 tests verts.
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

## Backlog de travail

### IMP-00 — Profiler les fichiers Excel réels

- [x] Ticket terminé
- But : comprendre les vrais onglets, en-têtes, variantes de colonnes et feuilles parasites.
- [x] Profiling de `Gestion 2025.xlsx` effectué.
- [x] Profiling de `Comptabilite 2025.xlsx` effectué.
- [x] Feuilles métier et feuilles auxiliaires/reporting identifiées.

### IMP-01 — Définir le contrat d'import strict

- [ ] Ticket encore ouvert
- But : formaliser ce qui est accepté, ignoré, bloquant, déductible ou ambigu.
- [ ] Centraliser les règles d'acceptation, d'ignorance et de blocage.
- [ ] Sortir ces règles des fonctions d'import dispersées.
- [ ] Définir explicitement les cas ambigus et leur stratégie de traitement.

### IMP-02 — Rendre la preview fidèle et diagnostique

- [x] Ticket terminé
- But : faire de la preview un reflet fiable de l'import réel.
- [x] Classification explicite des feuilles gestion/comptabilité.
- [x] Exclusion des feuilles d'aide, TODO, reporting et `Journal (saisie)`.
- [x] Diagnostic par feuille (`status`, `kind`, colonnes détectées/manquantes, avertissements, erreurs).
- [x] Calcul de `can_import` côté backend.
- [x] Affichage frontend exploitable en clair.

### IMP-03 — Introduire une couche de normalisation partagée

- [ ] Ticket encore ouvert
- But : parser les feuilles en structures normalisées, réutilisées à la fois par la preview et l'import.
- [x] `Factures` : normalisation partagée en lignes de facture.
- [x] `Paiements` : normalisation partagée en lignes de paiement.
- [x] `Caisse` : normalisation partagée en mouvements de caisse.
- [x] `Banque` : normalisation partagée en transactions bancaires.
- [x] `Contacts` : normalisation partagée en lignes de contact.
- [x] Import gestion dans l'ordre métier `contacts -> invoices -> payments -> cash -> bank`.
- [ ] Décider si les écritures comptables doivent aussi passer par une structure normalisée dédiée.

### IMP-04 — Ajouter une validation métier globale avant persistance

- [ ] Ticket démarré mais non terminé
- But : distinguer clairement :
- [x] Bloquer l'import complet si la preview détecte déjà une feuille reconnue invalide.
- [ ] Les lignes valides.
- [ ] Les lignes ignorables.
- [ ] Les erreurs bloquantes.
- [ ] Les ambiguïtés nécessitant arbitrage.
- Cible : produire un rapport exploitable avant tout flush significatif en base.

### IMP-05 — Garantir une transaction d'import sûre

- [ ] Ticket démarré mais non terminé
- But : éviter les imports partiels incohérents.
- [ ] Bloquer l'import proprement en cas d'erreur bloquante.
- [x] Garantir l'absence de données partielles persistées sur échec tardif d'une feuille ultérieure.
- [ ] Formaliser la stratégie pour tous les types d'erreurs bloquantes métier, pas seulement les exceptions techniques.

### IMP-06 — Clarifier la coexistence entre gestion et comptabilité

- [ ] Décision encore ouverte
- But : éviter les doublons ou incohérences entre :
- [ ] Définir la source de vérité entre gestion et comptabilité.
- [ ] Définir dans quels cas l'import comptable est autorisé.
- [ ] Définir la stratégie anti-doublon sur les écritures.

### IMP-07 — Gérer l'idempotence et la traçabilité d'import

- [ ] Ticket non démarré
- But : pouvoir répondre à deux questions :
- [ ] Savoir si un fichier a déjà été importé.
- [ ] Savoir quelles données ont été créées par quel import.
- [ ] Ajouter un journal d'import, un hash ou une signature de fichier.
- [ ] Ajouter des garde-fous anti-réinjection.

### IMP-08 — Améliorer le rapport de résultat et l'observabilité

- [ ] Ticket non démarré
- But : fournir un compte rendu final plus utile qu'un simple compteur.
- [ ] Structurer les erreurs.
- [ ] Structurer les avertissements par feuille.
- [ ] Ajouter un résumé par type d'objet créé ou ignoré.

### IMP-09 — Renforcer la couverture de tests

- [ ] Ticket encore ouvert
- [x] Suite d'intégration d'import couvrant plusieurs régressions importantes.
- [x] 16 tests verts sur `tests/integration/test_import_api.py`.
- [x] Ajouter des tests sur `Contacts`.
- [ ] Ajouter des tests de validation bloquante.
- [x] Ajouter des tests de rollback.
- [ ] Ajouter des tests de non-réimport / idempotence.

### IMP-10 — Durcir l'UX de confirmation d'import

- [ ] Ticket encore ouvert
- [x] Blocage du bouton de confirmation si `can_import` est faux.
- [x] Preview beaucoup plus lisible.
- [ ] Adapter l'UX au futur niveau de validation globale.
- [ ] Décider de l'UX pour les imports partiellement exploitables si ce mode est conservé.

### IMP-11 — Répétition sur fichiers réels et procédure opératoire

- [ ] Ticket non démarré
- But : tester la chaîne complète sur les vrais exports historiques et documenter une procédure de reprise fiable.
- [ ] Tester la chaîne complète sur les vrais exports historiques.
- [ ] Documenter une check-list d'import.
- [ ] Documenter l'ordre recommandé.
- [ ] Documenter les points de contrôle post-import.
- [ ] Documenter la stratégie de secours.

## Fichiers actuellement concernés

- `backend/services/excel_import.py`
- `backend/routers/excel_import.py`
- `frontend/src/api/accounting.ts`
- `frontend/src/views/ImportExcelView.vue`
- `frontend/src/i18n/fr.ts`
- `tests/integration/test_import_api.py`

## Point de reprise recommandé

La prochaine tranche utile est de prolonger IMP-04 pour formaliser davantage les erreurs bloquantes et les lignes ignorables, puis de compléter IMP-05 sur la politique de rollback pour les erreurs métier non techniques.

Ordre recommandé :

1. [ ] formaliser les règles globales de validation par type de feuille ;
2. [ ] distinguer explicitement lignes ignorables et erreurs bloquantes ;
3. [ ] compléter IMP-05 pour les erreurs métier qui ne passent pas par une exception technique.

## Questions ouvertes

- Quelle politique exacte veut-on pour l'import comptable si des écritures auto-générées existent déjà côté gestion ?
- Souhaite-t-on conserver un mode d'import partiel avec avertissements, ou viser un mode strictement bloquant dès qu'une feuille reconnue est incohérente ?
- Faut-il interdire explicitement la réimportation d'un même fichier dès maintenant, ou seulement la tracer dans un premier temps ?

## Journal synthétique

### 2026-04-11

- IMP-03 a progressé avec la normalisation partagée `Factures` / `Paiements`.
- L'ordre des feuilles n'est plus un facteur de comportement pour l'import gestion.
- IMP-03 a été étendu à `Caisse` et `Banque`, avec alignement preview/import sur des colonnes séparées `Entrée` / `Sortie` et `Débit` / `Crédit`.
- La détection d'en-têtes est désormais accent-insensible.
- IMP-03 a été complété pour `Contacts`, y compris sur une feuille sans colonne `Prénom`.
- IMP-04 a commencé avec un premier garde-fou : un fichier contenant une feuille reconnue mais invalide est désormais refusé avant tout import partiel.
- IMP-05 a commencé avec un rollback global validé sur erreur tardive pendant l'import.
- La suite `tests/integration/test_import_api.py` est verte avec 16 tests.
- Prochain objectif concret : approfondir la validation globale avant persistance, puis compléter la politique transactionnelle sur les erreurs métier.