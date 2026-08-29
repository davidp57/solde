import { nextTick, ref } from 'vue'
import { describe, expect, it, vi, beforeEach } from 'vitest'

vi.mock('../../api/cash', () => ({
  getCashBalance: vi.fn(),
}))

import { getCashBalance } from '../../api/cash'
import {
  useCashPaymentGuard,
  type GuardedPaymentMethod,
} from '../../composables/useCashPaymentGuard'

function makeForm(method: GuardedPaymentMethod = 'cheque', amount: number | null = 100) {
  return ref({ method, amount, reference: '' })
}

describe('useCashPaymentGuard', () => {
  beforeEach(() => {
    vi.mocked(getCashBalance).mockReset()
  })

  it('clears the amount when the method switches to cash', async () => {
    const form = makeForm('cheque', 310)
    useCashPaymentGuard(form, ref(310), ref('in'))

    form.value.method = 'especes'
    await nextTick()

    expect(form.value.amount).toBeNull()
  })

  it('restores the invoice balance when the method switches back', async () => {
    const form = makeForm('especes', null)
    useCashPaymentGuard(form, ref(310), ref('in'))

    form.value.method = 'cheque'
    await nextTick()

    expect(form.value.amount).toBe(310)
  })

  it('reports the amount a form should open with, per method', () => {
    const form = makeForm()
    const { initialAmount } = useCashPaymentGuard(form, ref(270), ref('in'))

    expect(initialAmount('especes')).toBeNull()
    expect(initialAmount('cheque')).toBe(270)
  })

  it('applies the remaining amount on demand', () => {
    const form = makeForm('especes', null)
    const { applyRemaining } = useCashPaymentGuard(form, ref(270), ref('in'))

    applyRemaining()

    expect(form.value.amount).toBe(270)
  })

  it('projects the till balance from the amount being typed', async () => {
    vi.mocked(getCashBalance).mockResolvedValue({ balance: '120.00' })
    const form = makeForm('especes', null)
    const { projectedCashBalance, loadCashBalance } = useCashPaymentGuard(form, ref(270), ref('in'))

    await loadCashBalance()
    expect(projectedCashBalance.value).toBe(120)

    form.value.amount = 270
    await nextTick()
    expect(projectedCashBalance.value).toBe(390)
  })

  it('subtracts a supplier payment from the till instead of adding it', async () => {
    vi.mocked(getCashBalance).mockResolvedValue({ balance: '500.00' })
    const form = makeForm('especes', 80)
    const { projectedCashBalance, loadCashBalance } = useCashPaymentGuard(
      form,
      ref(80),
      ref('out'),
    )

    await loadCashBalance()

    expect(projectedCashBalance.value).toBe(420)
  })

  it('fetches the till balance as soon as the method becomes cash', async () => {
    vi.mocked(getCashBalance).mockResolvedValue({ balance: '120.00' })
    const form = makeForm('cheque', 310)
    const { cashBalance } = useCashPaymentGuard(form, ref(310), ref('in'))

    expect(getCashBalance).not.toHaveBeenCalled()

    form.value.method = 'especes'
    await nextTick()
    await Promise.resolve()

    expect(getCashBalance).toHaveBeenCalledTimes(1)
    expect(cashBalance.value).toBe(120)
  })

  it('has no projection outside cash payments', async () => {
    vi.mocked(getCashBalance).mockResolvedValue({ balance: '120.00' })
    const form = makeForm('cheque', 310)
    const { projectedCashBalance, loadCashBalance } = useCashPaymentGuard(form, ref(310), ref('in'))

    await loadCashBalance()

    expect(projectedCashBalance.value).toBeNull()
  })

  it('drops the projection when the balance cannot be read', async () => {
    vi.mocked(getCashBalance).mockRejectedValue(new Error('offline'))
    const form = makeForm('especes', 270)
    const { cashBalance, projectedCashBalance, loadCashBalance } = useCashPaymentGuard(
      form,
      ref(270),
      ref('in'),
    )

    await loadCashBalance()

    expect(cashBalance.value).toBeNull()
    expect(projectedCashBalance.value).toBeNull()
  })
})
