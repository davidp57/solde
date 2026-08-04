import { describe, expect, it } from 'vitest'

import { getErrorDetail } from '../../utils/errorUtils'

describe('getErrorDetail', () => {
  it('reads the structured { code, detail } shape the API returns', () => {
    // backend/errors.py wraps every deliberate error this way; without support
    // for it the caller displayed "[object Object]" and lost the reason.
    const error = {
      response: {
        data: {
          detail: {
            code: 'FISCAL_YEAR_ERROR',
            detail: 'Report à nouveau déséquilibré : débit 100 ≠ crédit 90.',
          },
        },
      },
    }

    expect(getErrorDetail(error, 'fallback')).toBe(
      'Report à nouveau déséquilibré : débit 100 ≠ crédit 90.',
    )
  })

  it('still reads a plain string detail', () => {
    const error = { response: { data: { detail: 'Invoice not found' } } }
    expect(getErrorDetail(error, 'fallback')).toBe('Invoice not found')
  })

  it('reads the first message of a validation error array', () => {
    const error = { response: { data: { detail: [{ msg: 'field required' }] } } }
    expect(getErrorDetail(error, 'fallback')).toBe('field required')
  })

  it('falls back when the shape is unknown', () => {
    expect(getErrorDetail(new Error('boom'), 'fallback')).toBe('fallback')
    expect(getErrorDetail(null, 'fallback')).toBe('fallback')
  })
})
