import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key: string) => key }),
}))

const RouterLinkStub = defineComponent({
  props: ['to'],
  setup(props, { slots }) {
    return () => h('a', { 'data-to': props.to?.name }, slots.default?.())
  },
})

import InvoiceTypeToggle from '../../components/invoices/InvoiceTypeToggle.vue'

describe('InvoiceTypeToggle', () => {
  it('renders both spaces and marks the current type active', () => {
    const wrapper = mount(InvoiceTypeToggle, {
      props: { type: 'supplier' },
      global: { stubs: { RouterLink: RouterLinkStub } },
    })

    const tabs = wrapper.findAll('.invoice-type-toggle__tab')
    expect(tabs).toHaveLength(2)
    expect(wrapper.text()).toContain('invoices.type_toggle.client')
    expect(wrapper.text()).toContain('invoices.type_toggle.supplier')

    const active = wrapper.find('.invoice-type-toggle__tab--active')
    expect(active.text()).toContain('invoices.type_toggle.supplier')
    expect(active.attributes('data-to')).toBe('invoices-supplier')
  })
})
