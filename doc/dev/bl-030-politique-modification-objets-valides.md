# BL-030 — Politique de modification des objets métier validés

## But

Formaliser les garde-fous d'édition quand un objet métier a déjà produit des effets dérivés.

La règle générale retenue est la suivante :

- édition libre tant qu'un objet reste préparatoire ;
- édition encadrée avec régénération contrôlée quand l'objet a déjà déclenché des effets mais reste encore modifiable sans incohérence métier ;
- interdiction d'édition directe quand l'objet a déjà été consommé par d'autres effets métier ou comptables.

## Règles actuellement implémentées

### Factures

- une facture `draft` reste éditable librement ;
- une facture `sent` non réglée reste éditable ;
- quand une facture `sent` non réglée est modifiée, les écritures comptables auto-générées depuis cette facture sont supprimées puis régénérées dans le même flux transactionnel ;
- une facture hors de ce périmètre (`paid`, `partial`, `overdue`, `disputed`) n'est plus modifiable directement.

## Paiements

- un paiement devient quasi immuable après création ;
- les champs structurels (`montant`, `date`, `mode`, état de remise) ne sont plus modifiables ;
- seules des corrections mineures sans impact structurel restent autorisées : `reference`, `notes`, et `cheque_number` quand il s'agit d'un paiement par chèque.

## Imports réversibles

- le `undo/redo` des imports réversibles reste strict ;
- dès qu'un objet issu d'un import diverge manuellement de l'état attendu, le rejeu strict doit être bloqué ;
- la vérification stricte recharge explicitement l'instance ORM avant de calculer l'empreinte courante, afin d'éviter les faux comportements liés à des attributs expirés.

## Hors périmètre de ce lot

- mécanismes dédiés d'annulation métier (`avoir`, annulation comptable, reverse de paiement) ;
- matrice complète par statut pour tous les objets métier ;
- journal d'audit métier explicite des modifications.
