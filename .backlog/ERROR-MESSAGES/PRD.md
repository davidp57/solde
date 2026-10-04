# Lot ERROR-MESSAGES — Messages d'erreur explicites et catégorie des opérations rapprochées

Status: 🔄 in-progress
Branch: fix/error-messages → PR → develop

## Problem Statement

Cas réel (04/10/2026) : la secrétaire a rapproché un virement de client resté en catégorie « Autre crédit ». En voulant corriger la catégorie, David a obtenu « Une erreur est survenue » et a dû lire la réponse HTTP pour comprendre que l'opération était verrouillée (`BANK_TRANSACTION_RECONCILED_LOCKED`).

Trois défauts s'additionnent :

1. **Le front jette la raison.** 60 `catch {}` nus affichent `common.error.unknown`. Le serveur renvoie un code précis, que personne ne lit. Une table `api_errors` existait dans `fr.ts` depuis le refactoring des codes d'erreur (`61cba9a`), jamais branchée.
2. **L'interface propose une action vouée à l'échec** : le crayon de catégorie reste actif sur une ligne verrouillée.
3. **L'étiquette reste fausse même quand le travail est juste** : créer ou rattacher un règlement depuis la ligne ne touche pas à sa catégorie, et le verrou s'applique aussi aux lignes portées par un règlement ou un bordereau, où la catégorie ne produit aucune écriture.

## Solution

- **TEC-260** — `getErrorDetail` devient le résolveur central : code traduit dans `api_errors`, puis 403, puis absence de réponse, puis texte du serveur, puis message générique. Tous les `catch` à message générique passent par lui. La table `api_errors` ne garde que les codes à sens fixe : un code qui enveloppe un message variable (`…_INVALID`, `…_FAILED`) garde le texte du serveur.
- **BIZ-262** — `is_category_locked` : seule une ligne rapprochée **directement** verrouille sa catégorie. Exposé dans l'API (`category_locked`) ; l'écran Banque affiche un cadenas explicatif à la place du crayon. Créer ou rattacher un règlement passe la catégorie en « Paiement client » ou « Paiement fournisseur ».

- **BIZ-263** — « Rapprocher » sur une ligne `other_credit`, `other_debit`, `customer_payment` ou `supplier_payment` ne génère aucune écriture : confirmation demandée (aussi en masse), renvoi vers le règlement.

## Out of Scope

- Traduire en français les messages variables des services (`ValueError` en anglais) : chantier à part, à ouvrir si le texte serveur gêne à l'usage.
- Masquer « Défaire le rapprochement » au secrétaire : le refus 403 dit désormais « Votre rôle ne permet pas cette action ».
