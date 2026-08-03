# BIZ-223 — Annuler un règlement client non encaissé (backend)

Status: ✅ done
Type: feature
Files: `backend/services/payment.py`, `backend/services/bank_service.py`,
`backend/routers/payment.py`, `backend/schemas/payment.py`,
`tests/unit/test_payment_service.py`, `tests/integration/test_payments_api.py`,
`CHANGELOG.md`

## What to build

Remplacer le refus systématique de `delete_payment` par une annulation encadrée,
réservée à l'administrateur.

- **Service** — `cancel_payment(db, payment_id)` dans `payment.py`, en lieu et place du
  corps actuel de `delete_payment`. Contrôles dans l'ordre, chacun levant une
  `PaymentCancelError` typée porteuse d'un code :
  1. facture de type `FOURNISSEUR` → `PAYMENT_SUPPLIER` ;
  2. `payment.deposited is True` → `PAYMENT_DEPOSITED` ;
  3. lien dans `bank_transaction_payments` **ou** `bank_transactions.payment_id` pointant
     ce paiement → `PAYMENT_RECONCILED` ;
  4. exercice de `payment.date` en `FiscalYearStatus.CLOSED` → `FISCAL_YEAR_CLOSED`.
- **Détachement du bordereau** — si `payment.in_deposit`, retrouver le bordereau via
  `deposit_payments` puis :
  - s'il reste d'autres paiements → `bank_service.update_deposit(db, deposit_id,
    DepositUpdate(payment_ids=<reste>))` (retire le lien, remet `in_deposit=False` /
    `deposit_date=None`, recalcule `total_amount`) ;
  - si c'était le seul → `bank_service.delete_deposit(db, deposit_id)`.
  Ajouter dans `bank_service` un helper `get_deposit_id_for_payment(db, payment_id)`.
- **Suppression** — `delete_entries_for_source(db, EntrySourceType.PAYMENT, payment_id)`,
  puis `db.delete(payment)`, puis `_refresh_invoice_status(db, invoice_id)`. Le tout dans
  la même transaction.
- **Routeur** — `DELETE /api/payments/{payment_id}` passe à
  `require_role(UserRole.ADMIN)` ; `PaymentCancelError` → `409` avec son code et un
  message français explicite. L'appel `record_audit(PAYMENT_DELETED)` existant est
  conservé, en ajoutant le bordereau impacté au détail.
- **Pré-vérification** — `GET /api/payments/{payment_id}/cancel-preview` (admin), schéma
  `PaymentCancelPreview` : `can_cancel`, `reason_code`, `deposit_id`, `deposit_date`,
  `deposit_total_before`, `deposit_total_after`, `deposit_will_be_deleted`.

## Acceptance criteria

- [ ] Chèque client libre annulé : paiement supprimé, écritures `source_type=payment`
      supprimées, `paid_amount` recalculé, facture repassée de `PAID` à `SENT`.
- [ ] Chèque en transit dans un bordereau à plusieurs chèques : bordereau conservé,
      `total_amount` recalculé, autres chèques inchangés.
- [ ] Chèque seul dans son bordereau : bordereau supprimé, aucune ligne orpheline dans
      `deposit_payments`.
- [ ] Refus `409` avec le bon code pour chacun des quatre cas d'inéligibilité, sans
      aucune modification en base.
- [ ] `403` pour secrétaire et trésorier ; succès pour admin.
- [ ] `cancel-preview` renvoie l'impact exact dans les trois scénarios d'annulation et le
      motif de refus dans les cas inéligibles.
- [ ] L'annulation est tracée dans `audit_logs` avec le paiement, la facture, le montant
      et le bordereau impacté.

## Blocked by

None — socle du lot.
