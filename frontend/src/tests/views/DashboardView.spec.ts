import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'
import { describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key: string) => key }),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
  RouterLink: defineComponent({
    props: ['to'],
    setup(_props, { slots }) {
      return () => h('a', slots.default?.())
    },
  }),
}))

const mockGetDashboard = vi.fn()
const mockGetMonthly = vi.fn()
const mockGetResources = vi.fn()

vi.mock('../../api/accounting', () => ({
  getDashboardApi: () => mockGetDashboard(),
  getMonthlyChartApi: () => mockGetMonthly(),
  getResourcesChartApi: () => mockGetResources(),
}))

vi.mock('../../api/bank', () => ({
  listDeposits: () => Promise.resolve([]),
}))

vi.mock('../../stores/fiscalYear', () => ({
  useFiscalYearStore: () => ({
    selectedFiscalYearId: 1,
    selectedFiscalYear: { id: 1, name: '2025' },
    initialized: true,
    initialize: vi.fn().mockResolvedValue(undefined),
  }),
}))

const ContainerStub = defineComponent({
  setup(_props, { slots }) {
    return () => h('div', [slots.actions?.(), slots.default?.(), slots.title?.()])
  },
})

const AppStatCardStub = defineComponent({
  props: ['label', 'value'],
  setup(props) {
    return () => h('div', { class: 'stat' }, `${props.label}:${props.value}`)
  },
})

const stubs = {
  AppPage: ContainerStub,
  AppPageHeader: ContainerStub,
  AppPanel: ContainerStub,
  AppStatCard: AppStatCardStub,
  Button: ContainerStub,
  Skeleton: true,
  QuickPaymentWizard: true,
  QuickInvoiceWizard: true,
  BankPendingDepositsPanel: true,
  RouterLink: defineComponent({
    props: ['to'],
    setup(_props, { slots }) {
      return () => h('a', slots.default?.())
    },
  }),
}

import DashboardView from '../../views/DashboardView.vue'

async function flush() {
  await Promise.resolve()
  await Promise.resolve()
  await nextTick()
  await nextTick()
}

describe('DashboardView', () => {
  it('renders the net treasury hero and the worklist', async () => {
    mockGetDashboard.mockResolvedValue({
      bank_balance: 1000,
      bank_epargne_balance: 500,
      cash_balance: 100,
      unpaid_count: 7,
      unpaid_total: 1200,
      overdue_count: 0,
      overdue_total: 0,
      undeposited_count: 0,
      to_reconcile_count: 3,
      current_fy_name: '2025',
      current_resultat: 300,
      alerts: [],
    })
    mockGetMonthly.mockResolvedValue([{ month: '2025-05', charges: 200, produits: 500 }])
    mockGetResources.mockResolvedValue([
      { month: '2025-04', net_resources: 1000, funds: 0, liquidities: 0, client_receivables: 0, undeposited_cheques: 0, supplier_payables: 0 },
      { month: '2025-05', net_resources: 1600, funds: 0, liquidities: 0, client_receivables: 0, undeposited_cheques: 0, supplier_payables: 0 },
    ])

    const wrapper = mount(DashboardView, { global: { stubs } })
    await flush()

    expect(wrapper.text()).toContain('dashboard.net_treasury')
    // net treasury = 1000 + 500 + 100 = 1600
    expect(wrapper.find('.dashboard-hero__amount').text()).toContain('600')
    // worklist surfaces the unpaid invoices item
    expect(wrapper.text()).toContain('dashboard.unpaid_invoices')
    // worklist surfaces the bank reconciliation backlog (to_reconcile_count > 0)
    expect(wrapper.text()).toContain('dashboard.to_reconcile')
    // a positive delta pill is shown (1000 -> 1600)
    expect(wrapper.find('.dashboard-hero__delta--up').exists()).toBe(true)
  })

  it('handles Decimal string balances without producing NaN', async () => {
    mockGetDashboard.mockResolvedValue({
      bank_balance: '36480.10',
      bank_epargne_balance: '4750.00',
      cash_balance: '455.73',
      unpaid_count: 0,
      unpaid_total: '0',
      overdue_count: 0,
      overdue_total: '0',
      undeposited_count: 0,
      to_reconcile_count: 0,
      current_fy_name: '2025',
      current_resultat: '0',
      alerts: [],
    })
    mockGetMonthly.mockResolvedValue([])
    mockGetResources.mockResolvedValue([])

    const wrapper = mount(DashboardView, { global: { stubs } })
    await flush()

    const amount = wrapper.find('.dashboard-hero__amount').text()
    expect(amount).not.toContain('NaN')
    // 36480.10 + 4750.00 + 455.73 = 41685.83
    expect(amount).toContain('685')
  })

  it('shows the current calendar month figures, not the last (empty) fiscal month', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 5, 15)) // 15 June 2026
    try {
      mockGetDashboard.mockResolvedValue({
        bank_balance: 0,
        bank_epargne_balance: 0,
        cash_balance: 0,
        unpaid_count: 0,
        unpaid_total: 0,
        overdue_count: 0,
        overdue_total: 0,
        undeposited_count: 0,
        to_reconcile_count: 0,
        current_fy_name: '2025',
        current_resultat: 0,
        alerts: [],
      })
      // Fiscal year Aug→Jul: the last row (July) is still empty; June is the current month.
      mockGetMonthly.mockResolvedValue([
        { month: '2026-05', charges: 100, produits: 100 },
        { month: '2026-06', charges: 2300, produits: 546 },
        { month: '2026-07', charges: 0, produits: 0 },
      ])
      mockGetResources.mockResolvedValue([])

      const wrapper = mount(DashboardView, { global: { stubs } })
      await flush()

      const cards = wrapper.findAll('.stat').map((c) => c.text())
      const income = cards.find((t) => t.startsWith('dashboard.month_income:'))
      const expense = cards.find((t) => t.startsWith('dashboard.month_expense:'))
      // Parse the formatted amount, handling the FR locale (thin spaces as thousands
      // separators, comma as decimal) so we can assert the exact value, not a substring.
      const amountOf = (text: string | undefined): number =>
        Number(
          (text ?? '')
            .replace(/^[^:]*:/, '')
            .replace(/[\s €]/g, '')
            .replace(',', '.'),
        )
      expect(amountOf(income)).toBe(546) // June produits, not July's 0
      expect(amountOf(expense)).toBe(2300) // June charges, not July's 0
    } finally {
      vi.useRealTimers()
    }
  })
})
