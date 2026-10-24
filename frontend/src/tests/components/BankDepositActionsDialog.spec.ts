import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key: string) => key }),
}))

vi.mock('primevue/usetoast', () => ({
  useToast: () => ({ add: vi.fn() }),
}))

vi.mock('primevue/useconfirm', () => ({
  useConfirm: () => ({ require: vi.fn() }),
}))

vi.mock('@/api/bank', () => ({
  confirmDeposit: vi.fn(),
  deleteDeposit: vi.fn(),
  updateDeposit: vi.fn(),
}))

vi.mock('@/api/payments', () => ({
  listPayments: vi.fn().mockResolvedValue([]),
}))

import BankDepositActionsDialog from '../../components/bank/BankDepositActionsDialog.vue'

const passthrough = defineComponent({
  setup(_props, { slots }) {
    return () => h('div', slots.default?.())
  },
})

const stubs = {
  Dialog: passthrough,
  Message: passthrough,
  Button: defineComponent({
    props: ['label'],
    setup(props) {
      return () => h('button', props.label)
    },
  }),
  Checkbox: true,
  InputNumber: true,
  // Rendered as a marker so a re-introduced instance would be caught below.
  ConfirmDialog: defineComponent({
    setup() {
      return () => h('div', { class: 'local-confirm-dialog' })
    },
  }),
}

const deposit = {
  id: 8,
  date: '2026-08-04',
  type: 'cheques' as const,
  total_amount: '111.00',
  bank_reference: null,
  notes: null,
  denomination_details: null,
  confirmed: false,
  confirmed_date: null,
  payment_ids: [],
}

describe('BankDepositActionsDialog', () => {
  it('leaves the ConfirmDialog to its host view', async () => {
    // Two mounted instances both answer the confirmation service, but accepting on
    // one only hides that one: the other stays on screen and can replay the action.
    const wrapper = mount(BankDepositActionsDialog, {
      props: { visible: true, deposit },
      global: { stubs },
    })
    await flushPromises()

    expect(wrapper.find('.local-confirm-dialog').exists()).toBe(false)
  })
})
