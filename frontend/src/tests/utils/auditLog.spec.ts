import { describe, expect, it } from 'vitest'

import { auditActionLabel, formatAuditDetail, matchingActionCodes } from '../../utils/auditLog'

describe('auditActionLabel', () => {
  it('names a known action in French', () => {
    expect(auditActionLabel('bank.transaction.bulk_reconcile')).toBe(
      'Opération(s) bancaire(s) rapprochée(s)',
    )
  })

  it('falls back to the code for an unknown action', () => {
    expect(auditActionLabel('mystery.action')).toBe('mystery.action')
    expect(auditActionLabel('constructor')).toBe('constructor')
  })
})

describe('matchingActionCodes', () => {
  it('finds the codes behind a French word, ignoring accents and case', () => {
    const codes = matchingActionCodes('RAPPROCHEMENT')
    expect(codes).toContain('bank.reconcile.payment')
    expect(codes).toContain('bank.transaction.unreconcile')
    expect(matchingActionCodes('créée')).toEqual(matchingActionCodes('creee'))
  })

  it('returns nothing for a blank query', () => {
    expect(matchingActionCodes('  ')).toEqual([])
  })
})

describe('formatAuditDetail', () => {
  it('labels keys and formats amounts and booleans', () => {
    expect(formatAuditDetail({ amount: '1234.5', deposit_deleted: true, mystery: 3 })).toEqual([
      { label: 'Montant', values: ['1 234,50 €'] },
      { label: 'Bordereau supprimé', values: ['Oui'] },
      { label: 'mystery', values: ['3'] },
    ])
  })

  it('names bank categories and writes days the French way', () => {
    expect(formatAuditDetail({ category: 'other_credit', date: '2026-10-04' })).toEqual([
      { label: 'Catégorie', values: ['Autre crédit'] },
      { label: 'Date', values: ['04/10/2026'] },
    ])
  })

  it('keeps every line of a bulk reconciliation', () => {
    const [item] = formatAuditDetail({ transactions: ['ligne A', 'ligne B'] })
    expect(item).toEqual({ label: 'Opérations', values: ['ligne A', 'ligne B'] })
  })

  it('is empty without detail', () => {
    expect(formatAuditDetail(null)).toEqual([])
  })
})
