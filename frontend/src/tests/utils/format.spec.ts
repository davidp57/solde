import { describe, expect, it } from 'vitest'

import { formatDisplayDate, formatDisplayMonth } from '../../utils/format'

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
})
