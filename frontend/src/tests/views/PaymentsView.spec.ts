import { mount } from '@vue/test-utils'
import { defineComponent, h, inject, nextTick, provide } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}))

const toastAdd = vi.fn()
const confirmRequire = vi.fn()

vi.mock('primevue/usetoast', () => ({
  useToast: () => ({
    add: toastAdd,
  }),
}))

vi.mock('primevue/useconfirm', () => ({
  useConfirm: () => ({
    require: confirmRequire,
  }),
}))

vi.mock('../../api/payments', () => ({
  listPayments: vi.fn(),
  updatePayment: vi.fn(),
  deletePayment: vi.fn(),
}))

const fiscalYearStoreMock: {
  selectedFiscalYearId: number | undefined
  selectedFiscalYear:
    | {
        id: number
        name: string
        start_date: string
        end_date: string
        status: string
      }
    | undefined
  initialized: boolean
  initialize: ReturnType<typeof vi.fn>
  setSelectedFiscalYear: ReturnType<typeof vi.fn>
} = {
  selectedFiscalYearId: 12,
  selectedFiscalYear: {
    id: 12,
    name: '2025',
    start_date: '2025-01-01',
    end_date: '2025-12-31',
    status: 'open',
  },
  initialized: true,
  initialize: vi.fn().mockResolvedValue(undefined),
  setSelectedFiscalYear: vi.fn(),
}

vi.mock('../../stores/fiscalYear', () => ({
  useFiscalYearStore: () => fiscalYearStoreMock,
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
}))

import PaymentsView from '../../views/PaymentsView.vue'
import { listPayments, updatePayment } from '../../api/payments'

const mockListPayments = vi.mocked(listPayments)
const mockUpdatePayment = vi.mocked(updatePayment)

const paymentFixture = {
  id: 1,
  invoice_id: 10,
  invoice_number: '2025-0142',
  invoice_type: 'client' as const,
  contact_id: 20,
  amount: '60.00',
  date: '2025-02-01',
  method: 'cheque' as const,
  cheque_number: 'CHQ-001',
  reference: 'REF-2025-001',
  notes: 'Premier reglement',
  deposited: false,
  deposit_date: null,
  created_at: '2025-02-01T12:00:00',
}

const ContainerStub = defineComponent({
  template: '<div><slot /></div>',
})

const ButtonStub = defineComponent({
  props: {
    label: { type: String, default: '' },
    disabled: { type: Boolean, default: false },
    loading: { type: Boolean, default: false },
  },
  emits: ['click'],
  setup(props, { attrs, emit, slots }) {
    return () =>
      h(
        'button',
        {
          'data-testid': attrs['data-testid'],
          disabled: props.disabled || props.loading,
          onClick: () => emit('click'),
        },
        slots.default ? slots.default() : props.label,
      )
  },
})

const InputTextStub = defineComponent({
  props: {
    modelValue: { type: [String, Number], default: '' },
    type: { type: String, default: 'text' },
    disabled: { type: Boolean, default: false },
  },
  emits: ['update:modelValue', 'blur'],
  setup(props, { attrs, emit }) {
    return () =>
      h('input', {
        'data-testid': attrs['data-testid'],
        type: props.type,
        value: props.modelValue ?? '',
        disabled: props.disabled,
        onInput: (event: Event) =>
          emit('update:modelValue', (event.target as HTMLInputElement).value),
        onBlur: () => emit('blur'),
      })
  },
})

const SelectStub = defineComponent({
  props: {
    modelValue: { type: [String, Number], default: undefined },
    options: { type: Array, default: () => [] },
    optionLabel: { type: String, default: 'label' },
    optionValue: { type: String, default: 'value' },
    disabled: { type: Boolean, default: false },
  },
  emits: ['update:modelValue', 'change'],
  setup(props, { attrs, emit }) {
    return () =>
      h(
        'select',
        {
          'data-testid': attrs['data-testid'],
          value: props.modelValue ?? '',
          disabled: props.disabled,
          onChange: (event: Event) => {
            const value = (event.target as HTMLSelectElement).value || undefined
            emit('update:modelValue', value)
            emit('change')
          },
        },
        [
          h('option', { value: '' }, ''),
          ...(props.options as Array<Record<string, string>>).map((option) =>
            h(
              'option',
              { key: option[props.optionValue], value: option[props.optionValue] },
              option[props.optionLabel],
            ),
          ),
        ],
      )
  },
})

const ToggleButtonStub = defineComponent({
  props: {
    modelValue: { type: Boolean, default: false },
    onLabel: { type: String, default: '' },
    offLabel: { type: String, default: '' },
  },
  emits: ['update:modelValue', 'change'],
  setup(props, { emit }) {
    return () =>
      h('input', {
        type: 'checkbox',
        checked: props.modelValue,
        onChange: (event: Event) => {
          emit('update:modelValue', (event.target as HTMLInputElement).checked)
          emit('change')
        },
      })
  },
})

const TagStub = defineComponent({
  props: {
    value: { type: String, default: '' },
  },
  template: '<span>{{ value }}</span>',
})

const DialogStub = defineComponent({
  props: {
    visible: { type: Boolean, default: false },
    header: { type: String, default: '' },
  },
  emits: ['update:visible'],
  template: '<div v-if="visible"><h2>{{ header }}</h2><slot /><slot name="footer" /></div>',
})

const CurrentRowKey = Symbol('current-row')

const DataTableRowStub = defineComponent({
  props: {
    row: { type: Object, required: true },
  },
  setup(props, { slots }) {
    provide(CurrentRowKey, props.row)
    return () => h('div', { class: 'data-row' }, slots.default ? slots.default() : [])
  },
})

const DataTableStub = defineComponent({
  props: {
    value: { type: Array, default: () => [] },
  },
  components: { DataTableRowStub },
  template:
    '<div><div class="data-table__header"><slot /></div><DataTableRowStub v-for="row in value" :key="row.id" :row="row"><slot /></DataTableRowStub></div>',
})

const ColumnStub = defineComponent({
  props: {
    field: { type: String, default: '' },
    header: { type: String, default: '' },
  },
  setup(props, { slots }) {
    const row = inject<Record<string, unknown> | null>(CurrentRowKey, null)

    return () =>
      h('div', { class: 'column-stub' }, [
        props.header ? h('div', { class: 'column-stub__header' }, props.header) : null,
        row
          ? slots.body
            ? slots.body({ data: row })
            : h('div', { class: 'column-stub__value' }, String(row[props.field] ?? ''))
          : null,
      ])
  },
})

async function flushView() {
  await Promise.resolve()
  await nextTick()
}

function mountView() {
  return mount(PaymentsView, {
    global: {
      stubs: {
        AppPage: ContainerStub,
        AppPageHeader: ContainerStub,
        AppPanel: ContainerStub,
        AppStatCard: ContainerStub,
        Button: ButtonStub,
        Column: ColumnStub,
        ConfirmDialog: true,
        DataTable: DataTableStub,
        Dialog: DialogStub,
        InputText: InputTextStub,
        Select: SelectStub,
        Tag: TagStub,
        ToggleButton: ToggleButtonStub,
      },
    },
  })
}

describe('PaymentsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    fiscalYearStoreMock.initialize.mockResolvedValue(undefined)
    mockListPayments.mockResolvedValue([paymentFixture])
    mockUpdatePayment.mockResolvedValue({ ...paymentFixture, reference: 'REF-2025-002' })
  })

  it('displays the payment reference in the table', async () => {
    const wrapper = mountView()
    await flushView()

    expect(mockListPayments).toHaveBeenCalledWith(
      expect.objectContaining({
        invoice_type: 'client',
        from_date: '2025-01-01',
        to_date: '2025-12-31',
      }),
    )
    expect(wrapper.text()).toContain('payments.reference')
    expect(wrapper.text()).toContain('REF-2025-001')
  })

  it('falls back to the invoice number when the payment reference is empty', async () => {
    mockListPayments.mockResolvedValue([{ ...paymentFixture, reference: null }])

    const wrapper = mountView()
    await flushView()

    expect(wrapper.text()).toContain('2025-0142')
  })

  it('loads all payments when no fiscal year is selected', async () => {
    fiscalYearStoreMock.selectedFiscalYearId = undefined
    fiscalYearStoreMock.selectedFiscalYear = undefined

    const wrapper = mountView()
    await flushView()

    expect(mockListPayments).toHaveBeenCalledWith(
      expect.objectContaining({
        invoice_type: 'client',
        from_date: undefined,
        to_date: undefined,
      }),
    )

    wrapper.unmount()
    fiscalYearStoreMock.selectedFiscalYearId = 12
    fiscalYearStoreMock.selectedFiscalYear = {
      id: 12,
      name: '2025',
      start_date: '2025-01-01',
      end_date: '2025-12-31',
      status: 'open',
    }
  })

  it('opens an edit dialog and updates the payment', async () => {
    const wrapper = mountView()
    await flushView()

    await wrapper.get('[data-testid="payment-edit-button"]').trigger('click')
    await wrapper.get('[data-testid="payment-reference-input"]').setValue('REF-2025-002')
    await wrapper.get('[data-testid="payment-save-button"]').trigger('click')
    await flushView()

    expect(mockUpdatePayment).toHaveBeenCalledWith(
      1,
      {
        cheque_number: 'CHQ-001',
        reference: 'REF-2025-002',
        notes: 'Premier reglement',
      },
    )
  })

  it('locks structural payment fields in the edit dialog', async () => {
    const wrapper = mountView()
    await flushView()

    await wrapper.get('[data-testid="payment-edit-button"]').trigger('click')
    await flushView()

    expect(wrapper.get('input[type="date"]').element).toHaveProperty('disabled', true)
    expect(wrapper.get('input[type="number"]').element).toHaveProperty('disabled', true)
    expect(wrapper.get('select').element).toHaveProperty('disabled', true)
  })
})
