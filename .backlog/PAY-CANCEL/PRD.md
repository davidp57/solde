# Lot PAY-CANCEL — Annulation d'un règlement non encore encaissé

Status: ⬜ ready
Branch: feature/payment-cancellation → PR → develop

## Problem Statement

Cas réel : deux chèques réglant la même facture ont été saisis comme **un seul**
paiement. Aucune correction n'est possible aujourd'hui :

- `delete_payment` lève **systématiquement** `PaymentDeleteError`
  (`backend/services/payment.py:305`) — verrou posé par la politique BL-030
  (commit `e5fee8c`), qui plaçait explicitement l'annulation métier « hors périmètre » ;
- `update_payment` refuse tout changement de montant, date, mode et état de remise ;
- seuls `cheque_number`, `reference` et `notes` restent modifiables.

Le seul recours est un contournement par les notes, ou une intervention SQL directe.

Or **tant que le règlement n'est pas arrivé sur le compte**, rien d'irréversible n'a
été produit : les écritures de la remise ne sont générées qu'à la **confirmation** du
bordereau (`bank_service.confirm_deposit`), moment où les paiements liés passent à
`deposited=True`. Avant cela, annuler revient à défaire des effets purement internes.

## Solution

Une opération d'**annulation de règlement**, réservée à l'**administrateur**, autorisée
tant que l'argent n'est pas sur le compte. Elle supprime le paiement, ses écritures
comptables auto-générées et son éventuel rattachement à un bordereau de remise non
confirmé, puis recalcule le statut de la facture.

Règle d'éligibilité, évaluée dans cet ordre (premier refus rencontré = motif renvoyé) :

1. la facture réglée est de type **client** — les règlements fournisseurs émis ne sont
   pas annulables ;
2. `payment.deposited is False` — le règlement n'est pas encore encaissé ;
3. aucun lien de rapprochement bancaire (`bank_transaction_payments`, ou l'ancien
   `bank_transactions.payment_id`) ;
4. l'exercice de la date du paiement n'est pas `CLOSED`.

## User Stories

1. En tant qu'administrateur, je veux annuler un règlement saisi par erreur tant qu'il
   n'est pas encaissé, pour que la secrétaire puisse le ressaisir correctement.
2. En tant qu'administrateur, je veux savoir **avant de valider** ce que l'annulation va
   toucher (bordereau de remise impacté, nouveau total), pour ne pas découvrir l'effet
   après coup.
3. En tant que secrétaire, je veux comprendre pourquoi une annulation est refusée, pour
   savoir si je dois passer par l'administrateur ou par une autre correction.

## Implementation Decisions

- **Le critère est l'état, pas le mode de paiement.** `deposited` vaut déjà `True` à la
  création pour les espèces (argent en caisse) et pour les virements issus du
  rapprochement bancaire : ces cas sont donc exclus mécaniquement, sans liste de modes à
  maintenir. Le filtre « facture client » exclut à lui seul les chèques fournisseurs
  émis. En pratique, seuls les chèques clients non encaissés (libres ou en transit dans
  un bordereau non confirmé) restent annulables.
- **Retrait du bordereau réutilisé tel quel.** Si le paiement est `in_deposit`, on
  appelle `bank_service.update_deposit` avec la sélection privée de ce paiement : la
  fonction supprime le lien, remet `in_deposit=False` / `deposit_date=None` et recalcule
  `total_amount` (`bank_service.py:868-902`). Si le paiement était le **seul** du
  bordereau, `update_deposit` refuse une sélection vide
  (`bank_service.py:842`) : on appelle alors `delete_deposit`, qui libère les paiements
  et nettoie les associations. Les deux refusent déjà d'agir sur un bordereau confirmé.
- **Écritures comptables** : `accounting_engine.delete_entries_for_source(db,
  EntrySourceType.PAYMENT, payment_id)` — helper existant, déjà utilisé pour la
  régénération des salaires et des factures.
- **Statut de la facture** : `_refresh_invoice_status` gère déjà le retour `PAID → SENT`
  après suppression (`payment.py:465`) ; aucun ajout nécessaire.
- **Rôle** : `DELETE /api/payments/{id}` passe de secrétaire+ à **admin uniquement**.
  Aucun risque de régression : cette route échoue systématiquement aujourd'hui.
- **Motif de refus explicite** : exception typée portant un code (`PAYMENT_DEPOSITED`,
  `PAYMENT_SUPPLIER`, `PAYMENT_RECONCILED`, `FISCAL_YEAR_CLOSED`) mappée en `409` avec un
  message compréhensible, à la place du 409 générique actuel.
- **Pré-vérification** : `GET /api/payments/{id}/cancel-preview` renvoie l'éligibilité et
  l'impact (bordereau concerné, total avant/après, suppression du bordereau ou non) pour
  alimenter la boîte de confirmation.
- **Audit** : `AuditAction.PAYMENT_DELETED` est déjà journalisé par le routeur
  (`routers/payment.py:165`) — il ne servait jamais.

## Testing Decisions

- Chèque client libre (`deposited=False`, `in_deposit=False`) → annulation OK : paiement
  supprimé, écritures `source_type=payment` supprimées, facture repassée à `SENT`.
- Chèque en transit dans un bordereau à plusieurs chèques → bordereau conservé, total
  recalculé, autres chèques intacts.
- Chèque seul dans son bordereau → bordereau supprimé, associations nettoyées.
- Refus (409 + code) pour : paiement encaissé (`deposited=True`), paiement sur facture
  fournisseur, paiement rapproché en banque, exercice clôturé. Dans chaque cas, aucune
  donnée modifiée.
- Autorisation : secrétaire et trésorier reçoivent un `403` ; admin passe.
- `cancel-preview` renvoie le bon impact dans les trois cas (libre / bordereau partagé /
  bordereau à supprimer) et le bon motif de refus quand l'annulation est impossible.

## Out of Scope

- Annulation d'un règlement **déjà encaissé** — relève d'une contre-passation comptable,
  pas d'une suppression.
- Chèque rejeté / impayé par la banque : workflow distinct (l'argent est arrivé puis
  reparti), à traiter séparément.
- Avoir sur facture, annulation de règlement fournisseur.
- Modification du montant ou de la date d'un paiement : la politique BL-030 reste
  inchangée, on annule et on ressaisit.
