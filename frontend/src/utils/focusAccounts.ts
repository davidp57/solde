import type { ComposerTranslation } from 'vue-i18n'

export type FocusAccountKey =
  | 'member_receivables'
  | 'supplier_payables'
  | 'cash'
  | 'current_account'
  | 'cheques_to_deposit'

export const focusAccounts: ReadonlyArray<{ account_number: string; key: FocusAccountKey }> = [
  { account_number: '411100', key: 'member_receivables' },
  { account_number: '401000', key: 'supplier_payables' },
  { account_number: '531000', key: 'cash' },
  { account_number: '512100', key: 'current_account' },
  { account_number: '511200', key: 'cheques_to_deposit' },
]

const focusAccountByNumber: Record<string, FocusAccountKey> = Object.fromEntries(
  focusAccounts.map((focusAccount) => [focusAccount.account_number, focusAccount.key]),
) as Record<string, FocusAccountKey>

export function getFocusAccountKey(accountNumber: string): FocusAccountKey | null {
  return focusAccountByNumber[accountNumber] ?? null
}

export function formatFocusedAccountLabel(
  accountNumber: string,
  label: string,
  t: ComposerTranslation,
): string {
  const focusKey = getFocusAccountKey(accountNumber)
  if (!focusKey) {
    return `${accountNumber} — ${label}`
  }

  return `${accountNumber} — ${label} · ${t(`accounting.balance.focus.${focusKey}`)}`
}