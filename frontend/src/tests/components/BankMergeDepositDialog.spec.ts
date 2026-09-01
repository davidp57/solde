import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string, params?: Record<string, unknown>) =>
      params ? `${key}:${JSON.stringify(params)}` : key,
  }),
}))

vi.mock('primevue/usetoast', () => ({
  useToast: () => ({ add: vi.fn() }),
}))

const listDepositMergeCandidates = vi.fn()
const listDeposits = vi.fn()
const mergeDepositTransaction = vi.fn()

vi.mock('@/api/bank', () => ({
  listDepositMergeCandidates: (...args: unknown[]) => listDepositMergeCandidates(...args),
  listDeposits: (...args: unknown[]) => listDeposits(...args),
  mergeDepositTransaction: (...args: unknown[]) => mergeDepositTransaction(...args),
}))

import BankMergeDepositDialog from '../../components/bank/BankMergeDepositDialog.vue'

const stubs = {
  Dialog: defineComponent({
    props: ['visible'],
    setup(_props, { slots }) {
      return () => h('div', slots.default?.())
    },
  }),
  Button: defineComponent({
    props: ['label', 'loading', 'disabled'],
    emits: ['click'],
    setup(props, { emit }) {
      return () => h('button', { disabled: props.disabled, onClick: () => emit('click') }, props.label)
    },
  }),
  Message: defineComponent({
    setup(_props, { slots }) {
      return () => h('p', { class: 'message' }, slots.default?.())
    },
  }),
  Select: defineComponent({
    props: ['modelValue', 'options'],
    emits: ['update:modelValue'],
    setup(props) {
      return () => h('select', (props.options ?? []).map((o: { label: string }) => h('option', o.label)))
    },
  }),
}

const statementRow = {
  id: 42,
  date: '2026-08-04',
  amount: '111.00',
  reference: 'LFEO8TOCLO',
  description: 'REM CHQ REF05001A05',
  balance_after: '1191.72',
  bank_account: 'courant',
  reconciled: false,
  reconciled_with: null,
  source: 'import_ofx',
  detected_category: 'cheque_deposit',
  payment_id: null,
}

function mountDialog() {
  return mount(BankMergeDepositDialog, {
    props: { visible: false, transaction: statementRow },
    global: { stubs },
  })
}

async function open(wrapper: ReturnType<typeof mountDialog>) {
  await wrapper.setProps({ visible: true })
  await flushPromises()
}

describe('BankMergeDepositDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    listDeposits.mockResolvedValue([])
  })

  it('lists the candidate slip lines and preselects the closest one', async () => {
    listDepositMergeCandidates.mockResolvedValue([
      { ...statementRow, id: 7, description: 'Remise de chèques (bordereau #8)', source: 'manual' },
    ])
    const wrapper = mountDialog()
    await open(wrapper)

    expect(wrapper.find('option').text()).toContain('Remise de chèques (bordereau #8)')
    // No point asking about an unconfirmed slip when a line is already available.
    expect(listDeposits).not.toHaveBeenCalled()
  })

  it('points at the unconfirmed slip when no line can be merged', async () => {
    listDepositMergeCandidates.mockResolvedValue([])
    listDeposits.mockResolvedValue([
      { id: 8, date: '2026-08-04', type: 'cheques', total_amount: '111.00', confirmed: false },
    ])
    const wrapper = mountDialog()
    await open(wrapper)

    expect(listDeposits).toHaveBeenCalledWith({ confirmed: false })
    expect(wrapper.find('.message').text()).toContain('merge_deposit_unconfirmed_slip')
  })

  it('ignores a pending slip of another type or amount', async () => {
    listDepositMergeCandidates.mockResolvedValue([])
    listDeposits.mockResolvedValue([
      { id: 9, date: '2026-08-04', type: 'especes', total_amount: '111.00', confirmed: false },
      { id: 10, date: '2026-08-04', type: 'cheques', total_amount: '234.00', confirmed: false },
    ])
    const wrapper = mountDialog()
    await open(wrapper)

    expect(wrapper.find('.message').text()).toContain('merge_deposit_no_candidate')
  })

  it('does not break the dialog when the pending slips cannot be read', async () => {
    listDepositMergeCandidates.mockResolvedValue([])
    listDeposits.mockRejectedValue(new Error('offline'))
    const wrapper = mountDialog()
    await open(wrapper)

    expect(wrapper.find('.message').text()).toContain('merge_deposit_no_candidate')
  })
})
