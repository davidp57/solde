import { describe, expect, it } from 'vitest'
import { isOverdueInvoice } from '../../composables/useInvoiceMetrics'
import type { Invoice } from '../../api/invoices'

function makeInvoice(overrides: Partial<Invoice>): Invoice {
  return {
    id: 1,
    number: '2025-001',
    type: 'client',
    contact_id: 1,
    date: '2020-01-01',
    due_date: '2020-02-01',
    label: null,
    description: null,
    reference: null,
    total_amount: '100.00',
    paid_amount: '0.00',
    status: 'sent',
    pdf_path: null,
    file_path: null,
    reminder_dates: [],
    created_at: '2020-01-01T00:00:00',
    updated_at: '2020-01-01T00:00:00',
    lines: [],
    ...overrides,
  }
}

describe('isOverdueInvoice', () => {
  it('is true for a sent invoice past due with an outstanding balance', () => {
    expect(isOverdueInvoice(makeInvoice({ status: 'sent' }))).toBe(true)
  })

  it('is false for an irrecoverable invoice even if past due with a balance', () => {
    expect(isOverdueInvoice(makeInvoice({ status: 'irrecoverable' }))).toBe(false)
  })

  it('is false for a draft invoice', () => {
    expect(isOverdueInvoice(makeInvoice({ status: 'draft' }))).toBe(false)
  })

  it('is false for an archived invoice', () => {
    expect(isOverdueInvoice(makeInvoice({ status: 'archived' }))).toBe(false)
  })

  it('is false when fully paid (no outstanding balance)', () => {
    expect(isOverdueInvoice(makeInvoice({ paid_amount: '100.00' }))).toBe(false)
  })

  it('is false when the due date is in the future', () => {
    expect(isOverdueInvoice(makeInvoice({ due_date: '2999-01-01' }))).toBe(false)
  })
})
