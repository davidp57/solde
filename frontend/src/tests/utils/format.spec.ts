import { describe, expect, it } from 'vitest'

import {
  formatAccountingAmount,
  formatDateInputDraft,
  formatDisplayDate,
  formatDisplayMonth,
  normalizeDateInput,
} from '../../utils/format'

describe('format helpers', () => {
  it('formats ISO dates for French display', () => {
    expect(formatDisplayDate('2025-07-14')).toBe('14/07/2025')
  })

  it('formats ISO months for French display', () => {
    expect(formatDisplayMonth('2025-07')).toBe('juillet 2025')
  })

  it('keeps invalid month strings unchanged', () => {
    expect(formatDisplayMonth('2025-13')).toBe('2025-13')
  })

  it('normalizes French dates to ISO while still accepting ISO input', () => {
    expect(normalizeDateInput('14/07/2025')).toBe('2025-07-14')
    expect(normalizeDateInput('2025-07-14')).toBe('2025-07-14')
  })

  it('formats stored ISO values back to a French draft for text inputs', () => {
    expect(formatDateInputDraft('2025-07-14')).toBe('14/07/2025')
  })

  it('formats positive accounting amounts without parentheses', () => {
    const expected = new Intl.NumberFormat('fr-FR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(1234.5)

    expect(formatAccountingAmount(1234.5)).toBe(expected)
  })

  it('formats negative accounting amounts with parentheses', () => {
    const expected = new Intl.NumberFormat('fr-FR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(1234.5)

    expect(formatAccountingAmount(-1234.5)).toBe(`(${expected})`)
  })
})
