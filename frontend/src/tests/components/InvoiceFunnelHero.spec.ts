import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string, params?: Record<string, string | number>) => {
      const labels: Record<string, string> = {
        'invoices.funnel.remaining_client': 'Reste à encaisser',
        'invoices.funnel.remaining_supplier': 'Reste à payer',
        'invoices.funnel.collected_client': 'Encaissé',
        'invoices.funnel.collected_supplier': 'Payé',
        'invoices.funnel.upcoming': 'À venir',
        'invoices.funnel.overdue': 'En retard',
      }
      if (key === 'invoices.funnel.summary') {
        return `sur ${params?.total} facturés · ${params?.count} factures`
      }
      return labels[key] ?? key
    },
  }),
}))

const stubs = {
  AppPanel: defineComponent({
    setup(_props, { slots }) {
      return () => h('section', slots.default?.())
    },
  }),
}

import InvoiceFunnelHero from '../../components/invoices/InvoiceFunnelHero.vue'

describe('InvoiceFunnelHero', () => {
  it('shows the client remaining label and proportional bar segments', () => {
    const wrapper = mount(InvoiceFunnelHero, {
      props: {
        type: 'client',
        totalInvoiced: 1000,
        collected: 600,
        remaining: 400,
        overdue: 100,
        invoiceCount: 5,
      },
      global: { stubs },
    })

    expect(wrapper.text()).toContain('Reste à encaisser')
    expect(wrapper.text()).toContain('Encaissé')
    // collected 600/1000 = 60%, upcoming (400-100)=300/1000 = 30%, overdue 100/1000 = 10%
    const collected = wrapper.find('.invoice-funnel__segment--collected')
    const upcoming = wrapper.find('.invoice-funnel__segment--upcoming')
    const overdue = wrapper.find('.invoice-funnel__segment--overdue')
    expect(collected.attributes('style')).toContain('width: 60%')
    expect(upcoming.attributes('style')).toContain('width: 30%')
    expect(overdue.attributes('style')).toContain('width: 10%')
  })

  it('uses the supplier wording for the remaining amount', () => {
    const wrapper = mount(InvoiceFunnelHero, {
      props: {
        type: 'supplier',
        totalInvoiced: 500,
        collected: 500,
        remaining: 0,
        overdue: 0,
        invoiceCount: 2,
      },
      global: { stubs },
    })

    expect(wrapper.text()).toContain('Reste à payer')
    expect(wrapper.text()).toContain('Payé')
    // No remaining/overdue → those segments are not rendered
    expect(wrapper.find('.invoice-funnel__segment--upcoming').exists()).toBe(false)
    expect(wrapper.find('.invoice-funnel__segment--overdue').exists()).toBe(false)
    expect(wrapper.find('.invoice-funnel__segment--collected').exists()).toBe(true)
  })
})
