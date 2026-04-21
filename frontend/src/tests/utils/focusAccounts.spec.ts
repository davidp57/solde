import { describe, expect, it, vi } from 'vitest'

import { formatFocusedAccountLabel, getFocusAccountKey } from '@/utils/focusAccounts'

describe('focusAccounts', () => {
  it('identifies configured focus accounts', () => {
    expect(getFocusAccountKey('411100')).toBe('member_receivables')
    expect(getFocusAccountKey('511200')).toBe('cheques_to_deposit')
    expect(getFocusAccountKey('706000')).toBeNull()
  })

  it('decorates focus account labels', () => {
    const t = vi.fn((key: string) => key)

    expect(formatFocusedAccountLabel('411100', 'Adhérents', t)).toContain(
      'accounting.balance.focus.member_receivables',
    )
    expect(formatFocusedAccountLabel('511200', 'Chèques à déposer', t)).toContain(
      'accounting.balance.focus.cheques_to_deposit',
    )
    expect(formatFocusedAccountLabel('706000', 'Produits', t)).toBe('706000 — Produits')
  })
})
