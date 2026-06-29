# Lot EDIT-OPS — Édition/suppression des opérations bancaires manuelles

Status: 🔄 in-progress
Branch: feat/edit-manual-bank-ops → PR → develop

## Problem Statement

Les opérations bancaires créées **manuellement** depuis `BankView` (opérations sans
import source) ne peuvent être ni modifiées ni supprimées une fois saisies. Une erreur
de saisie (montant, date, libellé, catégorie) ne peut être corrigée qu'en contournant
l'écran, ce qui est frustrant et source d'incohérences.

## Solution

Permettre de **modifier** ou **supprimer** une opération bancaire manuelle (uniquement
celles sans source d'import) depuis `BankView`, avec les contrôles d'autorisation et
les garde-fous comptables habituels (une opération rapprochée / ayant généré une
écriture doit être traitée avec précaution).

## User Stories

1. En tant que trésorier, je veux corriger une opération manuelle erronée sans la
   recréer, pour garder un relevé propre.
2. En tant que trésorier, je veux supprimer une opération manuelle saisie par erreur.

## Implementation Decisions

- Restreindre l'édition/suppression aux opérations **manuelles** (pas d'`import source`).
- Vérifier l'impact d'un rapprochement / d'écritures comptables liées avant suppression
  (refuser ou nettoyer proprement, à arbitrer à l'implémentation).
- Autorisation au niveau routeur (écriture : Trésorier+).

## Testing Decisions

- Édition d'une opération manuelle (montant/date/libellé/catégorie) reflétée en base.
- Suppression d'une opération manuelle ; refus sur une opération issue d'un import.
- Garde-fous sur opération rapprochée / avec écriture liée.

## Out of Scope

- Édition des opérations **importées** (OFX/CSV/Excel) — restent en lecture seule.

## Further Notes

Ancien ticket hors-lot BIZ-169 (créé 2026-05-04). Repris ici à `⬜ ready`.

**Constat à l'implémentation (2026-06-29) :** la feature était **déjà implémentée** par
les lots banque (UI `BankView` : actions Modifier/Supprimer sur les lignes manuelles non
rapprochées via `canEditOrDelete` ; endpoints `PUT`/`DELETE /bank/transactions/{id}` avec
refus sur opération importée, et refus de suppression sur opération rapprochée). Ce lot
s'est donc réduit à une **consolidation** : (1) durcir le `PUT` pour refuser l'édition des
champs comptablement sensibles (date, montant, compte, catégorie) d'une opération
rapprochée — cohérent avec le `DELETE` — et (2) ajouter la couverture de tests des
garde-fous, jusque-là absente.
