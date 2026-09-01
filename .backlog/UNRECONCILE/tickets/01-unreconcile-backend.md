# BIZ-260 — Défaire le rapprochement d'une opération bancaire (backend)

Status: ⬜ ready
Type: feature
Files: `backend/services/bank_service.py`, `backend/routers/bank_transactions.py`,
`backend/services/audit_service.py`, `tests/integration/test_bank_api.py`,
`tests/unit/test_bank_service.py`, `CHANGELOG.md`

## What to build

- **Service** — `unreconcile_transaction(db, tx)` dans `bank_service.py`. Contrôles dans
  l'ordre, chacun levant une erreur typée porteuse d'un code :
  1. `tx.reconciled is False` → `NOT_RECONCILED` (ne pas réussir en silence) ;
  2. liens dans `bank_transaction_payments` **ou** `bank_transactions.payment_id`
     renseigné → `RECONCILED_VIA_PAYMENT`, message renvoyant vers l'annulation de
     règlement ;
  3. rapprochement issu d'un bordereau (voir *Detection* ci-dessous) →
     `RECONCILED_VIA_DEPOSIT`, message renvoyant vers les actions du bordereau ;
  4. exercice de `tx.date` en `FiscalYearStatus.CLOSED` → `FISCAL_YEAR_CLOSED`.

  Puis : `accounting_engine.delete_entries_for_source(db,
  EntrySourceType.BANK_TRANSACTION, tx.id)`, `tx.reconciled = False`,
  `tx.reconciled_with = None`. Une opération `no_entry` n'a aucune écriture à
  supprimer — le chemin doit passer sans erreur.

- **Detection du chemin bordereau** — établir le marqueur fiable avant de coder :
  `_mark_merged_deposit_reconciled` (`bank_service.py:336`) pose `reconciled_with` au
  libellé du bordereau sans créer de lien de paiement, et la confirmation d'un bordereau
  passe par un autre chemin encore. Vérifier les deux et retenir un critère qui ne laisse
  passer aucun des deux cas.

- **Routeur** — `POST /api/bank/transactions/{tx_id}/unreconcile`, rôle à confirmer avec
  David (reco : trésorier+, cf. PRD). Erreurs typées → `409` avec code et message
  français. Nouvelle action d'audit `BANK_TRANSACTION_UNRECONCILED`, détail :
  identifiant, catégorie, nombre d'écritures supprimées.

## Acceptance criteria

- [ ] Un rapprochement simple ayant généré des écritures est défait : `reconciled=False`,
      écritures `source_type=bank_transaction, source_id=tx.id` supprimées.
- [ ] Une opération en catégorie `no_entry` se dé-rapproche sans erreur.
- [ ] Après dé-rapprochement, l'opération est de nouveau **supprimable** et **éditable**
      (date, montant, compte, catégorie).
- [ ] Refus `409` avec le bon code pour : rapprochement via règlement, via bordereau,
      exercice clôturé, opération déjà non rapprochée — sans modification en base.
- [ ] L'action est tracée dans `audit_logs`.

## Blocked by

None — socle du lot.
