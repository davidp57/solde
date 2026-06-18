import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key: string) => key }),
}))

const SlotStub = defineComponent({
  setup(_props, { slots }) {
    return () => h('div', [slots.actions?.(), slots.default?.()])
  },
})

const Button = defineComponent({
  props: ['label'],
  emits: ['click'],
  setup(props, { emit }) {
    return () => h('button', { onClick: () => emit('click') }, props.label ?? '')
  },
})

const stubs = {
  AppPage: SlotStub,
  AppPageHeader: SlotStub,
  AppPanel: SlotStub,
  AppListState: SlotStub,
  InvoiceTypeToggle: true,
  InvoiceFunnelHero: true,
  InvoiceFilterSegments: true,
  InputText: true,
  Button,
}

import InvoiceWorkspace from '../../components/invoices/InvoiceWorkspace.vue'

const baseProps = {
  type: 'client' as const,
  title: 'Factures clients',
  subtitle: 'sous-titre',
  panelTitle: 'Portefeuille',
  panelSubtitle: 'panel sub',
  filtersHint: 'hint',
  funnel: { totalInvoiced: 0, collected: 0, remaining: 0, overdue: 0, count: 0 },
  segments: [],
  activeSegment: 'all',
  searchValue: '',
  displayedCount: 0,
  totalCount: 0,
}

describe('InvoiceWorkspace', () => {
  it('renders the default and dialogs slots', () => {
    const wrapper = mount(InvoiceWorkspace, {
      props: baseProps,
      slots: {
        default: () => h('div', { class: 'table-slot' }, 'TABLE'),
        dialogs: () => h('div', { class: 'dialogs-slot' }, 'DIALOGS'),
      },
      global: { stubs },
    })

    expect(wrapper.find('.table-slot').exists()).toBe(true)
    expect(wrapper.find('.dialogs-slot').exists()).toBe(true)
  })

  it('emits new when the default header action is clicked', async () => {
    const wrapper = mount(InvoiceWorkspace, { props: baseProps, global: { stubs } })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('new')).toBeTruthy()
  })
})
