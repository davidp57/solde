import { describe, expect, it } from 'vitest'

import {
  normalizeReconciliationText,
  scoreInvoiceSuggestion,
  scorePaymentSuggestion,
} from '../../utils/bankReconciliation'

describe('bank reconciliation helpers', () => {
  it('normalizes accents and separators for matching', () => {
    expect(normalizeReconciliationText('VIR Fournisseur-ete')).toBe('VIR FOURNISSEUR ETE')
  })

  it('prioritizes invoice candidates that match amount and reference text', () => {
    const strongMatch = scoreInvoiceSuggestion({
      transactionAmount: 200,
      transactionDate: '2024-03-15',
      transactionDescription: 'VIR FAC-FOURN-001 FOURNISSEUR TEST',
      transactionReference: 'FOURN-2024-001',
      candidateNumber: 'A-2024-001',
      candidateReference: 'FAC-FOURN-001',
      candidateContactName: 'Fournisseur Test',
      candidateDate: '2024-03-14',
      candidateRemainingAmount: 200,
    })
    const weakMatch = scoreInvoiceSuggestion({
      transactionAmount: 200,
      transactionDate: '2024-03-15',
      transactionDescription: 'VIR FAC-FOURN-001 FOURNISSEUR TEST',
      transactionReference: 'FOURN-2024-001',
      candidateNumber: 'A-2024-002',
      candidateReference: 'AUTRE-REF',
      candidateContactName: 'Autre tiers',
      candidateDate: '2024-01-10',
      candidateRemainingAmount: 195,
    })

    expect(strongMatch).toBeGreaterThan(weakMatch)
  })

  it('prioritizes payments that match invoice number or reference from the bank label', () => {
    const strongMatch = scorePaymentSuggestion({
      transactionAmount: 150,
      transactionDate: '2024-03-15',
      transactionDescription: 'VIR DUPONT F-2024-103',
      transactionReference: 'LEGACY-VIR-001',
      candidateInvoiceNumber: 'F-2024-103',
      candidateReference: 'LEGACY-VIR-001',
      candidateContactName: 'Dupont',
      candidateDate: '2024-03-14',
      candidateAmount: 150,
    })
    const weakMatch = scorePaymentSuggestion({
      transactionAmount: 150,
      transactionDate: '2024-03-15',
      transactionDescription: 'VIR DUPONT F-2024-103',
      transactionReference: 'LEGACY-VIR-001',
      candidateInvoiceNumber: 'F-2024-999',
      candidateReference: 'OTHER-REF',
      candidateContactName: 'Martin',
      candidateDate: '2024-02-01',
      candidateAmount: 150,
    })

    expect(strongMatch).toBeGreaterThan(weakMatch)
  })
})
