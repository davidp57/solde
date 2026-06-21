import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import Tag from 'primevue/tag'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => {
      const labels: Record<string, string> = {
        'invoices.statuses.draft': 'Brouillon',
        'invoices.statuses.sent': 'Envoyée',
        'invoices.statuses.paid': 'Payée',
        'invoices.statuses.partial': 'Partielle',
        'invoices.statuses.overdue': 'En retard',
        'invoices.statuses.disputed': 'Litige',
        'invoices.statuses.irrecoverable': 'Irrécouvrable',
        'invoices.statuses.archived': 'Archivée',
      }
      return labels[key] ?? key
    },
  }),
}))

import InvoiceStatusBadge from '../../components/invoices/InvoiceStatusBadge.vue'
import { invoiceStatusSeverity } from '../../components/invoices/invoiceStatus'

describe('invoiceStatusSeverity', () => {
  it('maps every known status to its severity', () => {
    expect(invoiceStatusSeverity('draft')).toBe('secondary')
    expect(invoiceStatusSeverity('sent')).toBe('info')
    expect(invoiceStatusSeverity('paid')).toBe('success')
    expect(invoiceStatusSeverity('partial')).toBe('warn')
    expect(invoiceStatusSeverity('overdue')).toBe('danger')
    expect(invoiceStatusSeverity('disputed')).toBe('danger')
    expect(invoiceStatusSeverity('irrecoverable')).toBe('secondary')
    expect(invoiceStatusSeverity('archived')).toBe('secondary')
  })

  it('falls back to secondary for an unknown status', () => {
    expect(invoiceStatusSeverity('unknown')).toBe('secondary')
  })
})

describe('InvoiceStatusBadge', () => {
  it('renders the translated label and the matching severity', () => {
    const wrapper = mount(InvoiceStatusBadge, { props: { status: 'paid' } })
    expect(wrapper.text()).toContain('Payée')
    expect(wrapper.findComponent(Tag).props('severity')).toBe('success')
  })

  it('renders a danger badge for an overdue invoice', () => {
    const wrapper = mount(InvoiceStatusBadge, { props: { status: 'overdue' } })
    expect(wrapper.text()).toContain('En retard')
    expect(wrapper.findComponent(Tag).props('severity')).toBe('danger')
  })
})
