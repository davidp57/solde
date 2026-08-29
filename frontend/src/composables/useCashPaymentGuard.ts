import { computed, ref, watch, type Ref } from 'vue'
import { getCashBalance } from '../api/cash'

export type GuardedPaymentMethod = 'especes' | 'cheque'

export interface GuardedPaymentForm {
  method: GuardedPaymentMethod
  amount: number | null
}

/**
 * Which way the till moves: a client receipt comes in, a supplier payment goes
 * out — mirroring `_create_treasury_entries_for_payment` on the backend.
 */
export type CashDirection = 'in' | 'out'

/**
 * Guard against recording a cash amount nobody counted (BIZ-250).
 *
 * Cash is the only payment method with no external document to contradict the
 * entry: a cheque carries its own amount, a transfer is settled by the bank
 * statement. Pre-filling the field with the invoice balance therefore lets a
 * wrong sum be recorded in a single click — which is how invoice 2026-0135 was
 * settled at 310 € when 270 € had been handed over.
 *
 * So the amount is cleared when the method switches to cash, and restored to
 * the invoice balance when it switches back. Reporting the balance stays one
 * click away through `applyRemaining`, but as a deliberate choice rather than a
 * default. This narrows the mistake, it does not remove it: nothing can stop
 * someone typing an uncounted amount. What it removes is the case where the
 * error needs no gesture at all.
 */
export function useCashPaymentGuard<T extends GuardedPaymentForm>(
  form: Ref<T>,
  remaining: Ref<number>,
  direction: Ref<CashDirection>,
) {
  const cashBalance = ref<number | null>(null)

  const isCash = computed(() => form.value.method === 'especes')

  /** Till balance once this payment is recorded, or null when not applicable. */
  const projectedCashBalance = computed(() => {
    if (!isCash.value || cashBalance.value === null) return null
    const movement = form.value.amount ?? 0
    return cashBalance.value + (direction.value === 'out' ? -movement : movement)
  })

  /** What the amount field should hold when the form opens for a given method. */
  function initialAmount(method: GuardedPaymentMethod): number | null {
    return method === 'especes' ? null : remaining.value
  }

  function applyRemaining(): void {
    form.value.amount = remaining.value
  }

  async function loadCashBalance(): Promise<void> {
    try {
      const { balance } = await getCashBalance()
      cashBalance.value = parseFloat(balance)
    } catch {
      // The projection is a convenience, never a gate: drop it and let the
      // payment be entered as before.
      cashBalance.value = null
    }
  }

  watch(
    () => form.value.method,
    (next, previous) => {
      if (next === previous) return
      form.value.amount = initialAmount(next)
    },
  )

  // The till balance is only ever shown for cash, so it is only ever fetched
  // then — and refreshed on each switch, since another payment may have moved
  // it while the dialog was open.
  watch(isCash, (cash) => {
    if (cash) void loadCashBalance()
  })

  return {
    isCash,
    cashBalance,
    projectedCashBalance,
    initialAmount,
    applyRemaining,
    loadCashBalance,
  }
}
