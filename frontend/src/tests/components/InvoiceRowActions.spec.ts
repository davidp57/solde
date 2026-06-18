import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { describe, expect, it, vi } from 'vitest'

const stubs = {
  Button: defineComponent({
    props: ['label', 'icon', 'severity', 'ariaLabel'],
    emits: ['click'],
    setup(props, { emit }) {
      return () =>
        h('button', { 'aria-label': props.ariaLabel, onClick: (e: Event) => emit('click', e) }, props.label ?? '')
    },
  }),
  Menu: defineComponent({
    props: ['model'],
    setup(props) {
      return () =>
        h(
          'ul',
          (props.model ?? []).map((item: { label?: string; class?: string }) =>
            h('li', { class: item.class }, item.label ?? ''),
          ),
        )
    },
  }),
}

import InvoiceRowActions from '../../components/invoices/InvoiceRowActions.vue'

describe('InvoiceRowActions', () => {
  it('renders the primary action and triggers its command', async () => {
    const command = vi.fn()
    const wrapper = mount(InvoiceRowActions, {
      props: {
        primary: { key: 'pay', label: 'Encaisser', icon: 'pi pi-wallet', command },
        menuItems: [],
      },
      global: { stubs },
    })

    const primaryBtn = wrapper.findAll('button').find((b) => b.text() === 'Encaisser')
    expect(primaryBtn).toBeTruthy()
    await primaryBtn!.trigger('click')
    expect(command).toHaveBeenCalledTimes(1)
  })

  it('passes overflow items to the menu and tints the destructive one', () => {
    const wrapper = mount(InvoiceRowActions, {
      props: {
        primary: { key: 'view', label: 'Voir', icon: 'pi pi-eye', command: () => {} },
        menuItems: [
          { label: 'PDF' },
          { separator: true },
          { label: 'Supprimer', class: 'invoice-row-actions-danger' },
        ],
      },
      global: { stubs },
    })

    expect(wrapper.text()).toContain('PDF')
    expect(wrapper.find('.invoice-row-actions-danger').text()).toContain('Supprimer')
  })
})
