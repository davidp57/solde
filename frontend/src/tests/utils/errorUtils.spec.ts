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

  it('prefers the French message of a known code over the server text', () => {
    // The secretary changed the category of a reconciled line and got
    // "Une erreur est survenue": the reason was only in the HTTP response.
    const error = {
      response: {
        status: 422,
        data: {
          detail: {
            code: 'BANK_TRANSACTION_RECONCILED_LOCKED',
            detail: "A reconciled transaction's ... cannot be edited; unreconcile it first",
          },
        },
      },
    }
    expect(getErrorDetail(error, 'fallback')).toContain('défaire le rapprochement')
  })

  it('keeps the server text for a code without a translation', () => {
    const error = {
      response: { status: 422, data: { detail: { code: 'PAYMENT_INVALID', detail: 'Amount exceeds' } } },
    }
    expect(getErrorDetail(error, 'fallback')).toBe('Amount exceeds')
  })

  it('reads the { code, message } shape of the auth routes', () => {
    const error = { response: { status: 400, data: { detail: { code: 'X', message: 'Nope' } } } }
    expect(getErrorDetail(error, 'fallback')).toBe('Nope')
  })

  it('explains a 403 as a role restriction', () => {
    const error = { response: { status: 403, data: { detail: 'Insufficient permissions' } } }
    expect(getErrorDetail(error, 'fallback')).toBe('Votre rôle ne permet pas cette action.')
  })

  it('reports an unreachable server when no response came back', () => {
    const error = { request: {}, response: undefined, message: 'Network Error' }
    expect(getErrorDetail(error, 'fallback')).toContain('Impossible de contacter le serveur')
  })

  it('falls back when the shape is unknown', () => {
    expect(getErrorDetail(new Error('boom'), 'fallback')).toBe('fallback')
    expect(getErrorDetail(null, 'fallback')).toBe('fallback')
  })
})
