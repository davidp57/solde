# Lot SALARY-FIX — Fiabiliser les écritures comptables des salaires

Status: ✅ done
Branch: feature/salary-entries-fix → PR → develop

## Problem Statement

Un cas réel (paie WOLFF mai 2026) a produit un trou comptable : la constatation du
salaire a bien été générée (641/421, 421/431, 645/431) mais **l'écriture de paiement
banque** (421000 D / 512100 C) **manquait**, ce qui a faussé le solde du compte 512100
de 157,50 €. Cause racine établie par l'`audit_logs` :

1. **Saisie** : à la création, le champ « Net à payer » du formulaire est **manuel**,
   initialisé à `0`, et **découplé** du « Net calculé » affiché (brut − charges − impôt).
   Le salaire a été enregistré avec `net_pay = 0`, donc l'étape 5 de
   `generate_entries_for_salary` (`if rule_payment and salary.net_pay > 0`) a été
   **sautée en silence** — sans erreur.
2. **Correction sans régénération** : ~2 min plus tard, le net a été corrigé à 157,50 €
   via une édition. Mais `update_salary` ne fait que `setattr` + flush : il **ne
   régénère aucune écriture comptable**. L'écriture de paiement, absente depuis la
   création, n'a jamais été créée.

La donnée PROD a été corrigée ponctuellement (écriture manuelle 421000/512100). Ce lot
corrige les **trois défauts logiciels** sous-jacents pour que le cas ne se reproduise pas.

## Solution

- **A (BIZ-222)** — Le champ « Net à payer » se remplit automatiquement depuis le net
  calculé (brut − charges − impôt) tout en restant éditable ; le formulaire refuse un
  net ≤ 0. On ne peut plus enregistrer un salaire au net nul par inadvertance.
- **B (TEC-213)** — `update_salary` régénère les écritures comptables du salaire quand
  un **montant comptable** change ; refuse si l'exercice concerné est clôturé. C'est le
  défaut qui transforme une erreur de saisie rattrapée en trou permanent.
- **C (TEC-214)** — Garde-fou moteur : journaliser un avertissement quand une
  constatation de salaire est générée **sans** paiement (net ≤ 0), et fournir un moyen
  de lister les salaires structurellement incomplets.

## User Stories

1. En tant que secrétaire, je veux que le net soit pré-rempli et cohérent, pour ne pas
   enregistrer une paie au net nul.
2. En tant que trésorier, je veux que corriger un salaire mette à jour ses écritures
   comptables, pour ne pas garder un journal incohérent.
3. En tant que trésorier, je veux être alerté d'un salaire constaté mais non payé, pour
   détecter un trou avant qu'il ne fausse la trésorerie.

## Implementation Decisions

- **B** : à l'édition, si `gross`, `employee_charges`, `employer_charges`, `tax` ou
  `net_pay` change, supprimer les écritures `source_type=salary, source_id=<id>` puis
  rappeler `generate_entries_for_salary`. **Refuser** (exception typée → 409) si
  l'exercice de l'ancienne date d'écriture **ou** de la nouvelle est `CLOSED`. Un
  changement qui ne touche aucun montant (notes seules) ne régénère rien.
- **A** : `watch` sur (gross, employee_charges, tax) → `form.net_pay = round2(net
  calculé)` ; le champ reste éditable. À l'ouverture en **édition**, on charge la valeur
  stockée sans l'écraser. `save()` bloque (toast) si `net_pay <= 0`.
- **C** : `log.warning` dans `generate_entries_for_salary` si `gross > 0` et
  `net_pay <= 0` (constatation sans paiement). Helper `find_incomplete_salaries`
  (salaires avec écritures mais sans ligne 512100) testé. Pas d'écran dédié (hors scope).

## Testing Decisions

- **B** : édition changeant un montant → anciennes écritures supprimées, nouvelles
  cohérentes (paiement présent quand net > 0) ; édition « notes seules » → écritures
  inchangées ; édition sur exercice clôturé → refus, écritures intactes.
- **A** : net auto-calculé au changement de brut/charges ; net éditable conservé ; submit
  refusé si net ≤ 0 (test composant).
- **C** : warning émis sur salaire net ≤ 0 ; `find_incomplete_salaries` détecte le cas
  constaté-sans-paiement et ignore les paies complètes.

## Out of Scope

- Écran dédié de revue des salaires incomplets (un helper + log suffisent ici).
- Rattachement rétroactif des paiements manuels existants à leur salaire.
- Rapprochement bancaire des écritures de salaire.
