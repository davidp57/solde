# Lot UNRECONCILE — Défaire le rapprochement d'une opération bancaire

Status: ✅ done
Branch: feature/unreconcile → PR → develop

## Problem Statement

**Un rapprochement est irréversible.** Il n'existe ni endpoint, ni action d'interface,
ni fonction de service pour le défaire : `reconciled` passe à `True`
(`bank_service.py:196`, `:344`, `:761`) et rien ne le remet jamais à `False`.

Ce n'est pas anodin, parce que le rapprochement est le **verrou** de tout le reste :

- `delete_transaction` refuse une opération rapprochée ;
- `PUT /bank/transactions/{id}` refuse d'en modifier la date, le montant, le compte ou
  la catégorie (`BANK_TRANSACTION_RECONCILED_LOCKED`) ;
- `_require_unreconciled_transaction` ferme la création et le rattachement de règlements.

Une opération rapprochée par erreur est donc **définitivement figée**, y compris quand
son rapprochement n'a produit aucune écriture comptable.

Cas réel qui a révélé le manque (lot IMPORT-DUP, 01/09/2026) : le relevé du compte
d'épargne portait deux fois le virement du 01/05/2026 — une saisie manuelle rapprochée
et son équivalent importé. La saisie manuelle, en catégorie `no_entry`, **n'avait généré
aucune écriture** : la dé-rapprocher n'aurait rien eu à défaire côté comptabilité. Elle
est pourtant restée intouchable, et il a fallu supprimer l'autre ligne — celle qui
portait la référence de la banque. Le lot IMPORT-DUP a ouvert cette porte de sortie,
mais quand c'est la ligne **rapprochée** qui est en trop, il n'y en a toujours aucune.

Un mauvais rapprochement s'attrape aussi hors de ce cas : catégorie erronée au moment du
« Tout rapprocher », ligne rapprochée sur le mauvais mois, geste involontaire sur
« Rapprocher avant… ».

## Solution

Une opération de **dé-rapprochement**, qui remet l'opération dans la file « à traiter »
et supprime les écritures que son rapprochement avait générées.

Le rapprochement se fait par plusieurs chemins, qui ne se défont pas de la même façon.
Ce lot ne traite que le premier ; les autres sont **refusés avec un motif nommé** qui
indique le bon chemin, plutôt que défaits à moitié.

| Chemin de rapprochement | Ce qu'il a produit | Traitement |
|---|---|---|
| `reconcile_transactions_bulk` (bouton Rapprocher, Tout rapprocher, Rapprocher avant…) | `reconciled=True` + écritures `bank_transaction:{id}` | **Défait par ce lot** |
| Création d'un règlement depuis la ligne | un `Payment`, ses écritures, les liens | Refus → passer par l'annulation de règlement (PAY-CANCEL) |
| Rattachement à un règlement existant | liens `bank_transaction_payments` | Refus → hors périmètre, à rouvrir si le besoin se présente |
| Confirmation ou fusion d'un bordereau | la ligne **est** le bordereau (`_mark_merged_deposit_reconciled`) | Refus → passer par les actions du bordereau |

## User Stories

1. En tant que trésorier, je veux annuler un rapprochement fait par erreur, pour pouvoir
   corriger la catégorie de l'opération puis la rapprocher correctement.
2. En tant que trésorier, je veux pouvoir supprimer une ligne de relevé en double même
   si je l'ai déjà rapprochée, sans intervention en base.
3. En tant que trésorier, je veux qu'on me dise **pourquoi** un dé-rapprochement est
   refusé et par où passer, plutôt qu'un refus sec.

## Implementation Decisions

- **Les écritures se suppriment par la source, pas par devinette** :
  `accounting_engine.delete_entries_for_source(db, EntrySourceType.BANK_TRANSACTION,
  tx.id)` — helper existant (`accounting_engine.py:364`), déjà utilisé pour les salaires
  et les factures. Une opération en catégorie `no_entry` n'a rien à supprimer : le
  chemin doit fonctionner sans écriture à défaire, c'est même le cas le plus courant.
- **Refus typés**, dans l'esprit de PAY-CANCEL : un code par motif
  (`RECONCILED_VIA_PAYMENT`, `RECONCILED_VIA_DEPOSIT`, `FISCAL_YEAR_CLOSED`) mappé en
  `409` avec un message français qui nomme le bon chemin.
- **Exercice clôturé** : refus. Défaire une écriture d'un exercice clos relève de la
  contre-passation, pas de la correction d'un geste.
- **Détection du chemin règlement** : `payment_id` renseigné, ou un lien dans
  `bank_transaction_payments`.
- **Détection du chemin bordereau** — le point ouvert à l'implémentation, tranché en
  regardant le code : **rien ne relie une ligne bancaire à un bordereau dans le schéma**.
  Les trois marques laissées par les chemins de remise sont donc lues à rebours, par
  ordre de fiabilité : la référence `DEP-(ESP|CHQ)-{id}` d'une ligne créée par Solde,
  l'étiquette `Bordereau #{id}` de `reconciled_with`, et enfin la **description**. Cette
  dernière est la seule qui survive à tous les cas : une ligne fusionnée prend la
  référence du relevé (`merge_deposit_transaction`, `_adopt_statement_row_for_deposit`),
  et `reconciled_with` reste vide quand le bordereau porte une référence bancaire saisie
  à la main — `_slip_label_from_reference` renvoie alors `None`. La description est
  désormais construite par `_deposit_description`, à côté de la regex qui la relit, pour
  que les deux ne divergent pas.
- **Rôle : trésorier et administrateur** (tranché par David le 01/09/2026). Le
  rapprochement lui-même reste ouvert au secrétaire : c'est de la gestion courante,
  alors que le défaire supprime des écritures comptables.
- **Journalisation** : nouvelle action d'audit, avec l'opération, sa catégorie et le
  nombre d'écritures supprimées.

## Testing Decisions

- Rapprochement simple avec écritures générées → dé-rapproché : `reconciled=False`,
  écritures `source_type=bank_transaction, source_id=tx.id` supprimées, journal cohérent.
- Opération en catégorie `no_entry` → dé-rapprochée sans erreur, rien à supprimer.
- Après dé-rapprochement, l'opération redevient **supprimable** et **éditable** — c'est
  la raison d'être du lot, à vérifier de bout en bout.
- Refus `409` avec le bon code pour : rapprochement via un règlement, via un bordereau,
  exercice clôturé. Dans chaque cas, aucune donnée modifiée.
- Une opération non rapprochée → refus explicite, pas une réussite silencieuse.
- Autorisation selon le rôle retenu.

## Out of Scope

- **Défaire un règlement ou un bordereau** : ce sont les lots PAY-CANCEL et les actions
  de bordereau. Ce lot refuse ces cas, il ne les recouvre pas.
- Le dé-rapprochement **en masse** : le geste corrige une erreur, il n'a pas à s'appliquer
  à une sélection. À rouvrir si un « Tout rapprocher » malheureux le justifie.
- La contre-passation d'écritures sur un exercice clôturé.

## Further Notes

Ouvert le 01/09/2026 à la demande de David, à l'issue du lot IMPORT-DUP qui a mis le
manque au jour. Voir la section *Out of Scope* de [`../IMPORT-DUP/PRD.md`](../IMPORT-DUP/PRD.md).
