import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { describe, expect, it } from 'vitest'

const RouterLinkStub = defineComponent({
  props: ['to'],
  setup(props, { slots }) {
    return () => h('a', { 'data-to': JSON.stringify(props.to) }, slots.default?.())
  },
})

import AppWorklist, { type WorklistItem } from '../../components/ui/AppWorklist.vue'

const items: WorklistItem[] = [
  {
    key: 'unpaid',
    icon: 'pi-file',
    label: 'Factures impayées',
    sublabel: '7 factures clients',
    value: '12 450,00 €',
    severity: 'danger',
    to: { name: 'invoices-client', query: { unpaid: '1' } },
  },
  {
    key: 'deposit',
    icon: 'pi-wallet',
    label: 'Chèques à déposer',
    value: '5',
    severity: 'warn',
  },
]

describe('AppWorklist', () => {
  it('renders items with count, severity and clickable rows', () => {
    const wrapper = mount(AppWorklist, {
      props: { items, title: 'À traiter', countSeverity: 'danger' },
      global: { stubs: { RouterLink: RouterLinkStub } },
    })

    expect(wrapper.find('.app-worklist__count').text()).toBe('2')
    expect(wrapper.text()).toContain('Factures impayées')
    expect(wrapper.text()).toContain('12 450,00 €')

    // First item is a link (has `to`), second is a plain div
    const links = wrapper.findAll('a')
    expect(links).toHaveLength(1)
    expect(wrapper.find('.app-worklist__item--danger').exists()).toBe(true)
    expect(wrapper.find('.app-worklist__item--warn').exists()).toBe(true)
  })

  it('renders the empty state when there are no items', () => {
    const wrapper = mount(AppWorklist, {
      props: { items: [], emptyLabel: 'Rien à traiter' },
      global: { stubs: { RouterLink: RouterLinkStub } },
    })
    expect(wrapper.text()).toContain('Rien à traiter')
  })
})
