import { mount } from '@vue/test-utils'
import { defineComponent, h, inject, nextTick, provide, reactive } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}))

const toastAdd = vi.fn()

vi.mock('primevue/usetoast', () => ({
  useToast: () => ({
    add: toastAdd,
  }),
}))

vi.mock('primevue/useconfirm', () => ({
  useConfirm: () => ({
    require: vi.fn(),
  }),
}))

const fiscalYearStoreMock = reactive({
  selectedFiscalYearId: 2 as number | undefined,
  selectedFiscalYear: {
    id: 2,
    name: 'Exercice 2025',
    start_date: '2025-01-01',
    end_date: '2025-12-31',
  } as { id: number; name: string; start_date: string; end_date: string } | undefined,
  initialized: true,
  initialize: vi.fn().mockResolvedValue(undefined),
})

vi.mock('../../stores/fiscalYear', () => ({
  useFiscalYearStore: () => fiscalYearStoreMock,
}))

const replaceMock = vi.fn()

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ replace: replaceMock }),
}))

vi.mock('../../api/contacts', () => ({
  listContactsApi: vi.fn(),
}))

vi.mock('../../api/invoices', () => ({
  listInvoicesApi: vi.fn(),
  deleteInvoiceApi: vi.fn(),
  duplicateInvoiceApi: vi.fn(),
  downloadInvoicePdfApi: vi.fn(() => Promise.resolve(new Blob(['%PDF'], { type: 'application/pdf' }))),
  sendInvoiceEmailApi: vi.fn(),
}))

vi.mock('../../api/payments', () => ({
  listPayments: vi.fn(),
  createPayment: vi.fn(),
}))

import ClientInvoicesView from '../../views/ClientInvoicesView.vue'
import { listContactsApi } from '../../api/contacts'
import { listInvoicesApi } from '../../api/invoices'
import { createPayment, listPayments } from '../../api/payments'

const mockListContactsApi = vi.mocked(listContactsApi)
const mockListInvoicesApi = vi.mocked(listInvoicesApi)
const mockListPayments = vi.mocked(listPayments)
const mockCreatePayment = vi.mocked(createPayment)

const invoiceFixture = {
  id: 1,
  number: 'F-2025-001',
  type: 'client' as const,
  contact_id: 10,
  date: '2025-02-10',
  due_date: '2025-03-10',
  label: 'general' as const,
  description: 'Cotisation',
  reference: null,
  total_amount: '120.00',
  paid_amount: '20.00',
  status: 'partial' as const,
  pdf_path: null,
  file_path: null,
  created_at: '2025-02-10T00:00:00',
  updated_at: '2025-02-10T00:00:00',
  lines: [],
}

const historicalInvoiceFixture = {
  ...invoiceFixture,
  id: 2,
  number: 'F-2024-087',
  date: '2024-11-18',
  due_date: '2024-12-18',
  total_amount: '80.00',
  paid_amount: '0.00',
  status: 'overdue' as const,
  updated_at: '2024-11-18T00:00:00',
}

const ContainerStub = defineComponent({
  template: '<div><slot /><slot name="actions" /></div>',
})

const AppStatCardStub = defineComponent({
  props: {
    label: { type: String, default: '' },
    value: { type: [String, Number], default: '' },
    caption: { type: String, default: '' },
  },
  template: '<div>{{ label }} {{ value }} {{ caption }}</div>',
})

const ButtonStub = defineComponent({
  props: {
    label: { type: String, default: '' },
    disabled: { type: Boolean, default: false },
    loading: { type: Boolean, default: false },
    icon: { type: String, default: '' },
    title: { type: String, default: '' },
  },
  emits: ['click'],
  setup(props, { emit, slots }) {
    return () =>
      h(
        'button',
        {
          disabled: props.disabled || props.loading,
          title: props.title,
          onClick: () => emit('click'),
        },
        slots.default ? slots.default() : props.label || props.icon,
      )
  },
})

const InputTextStub = defineComponent({
  props: {
    modelValue: { type: String, default: '' },
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () =>
      h('input', {
        value: props.modelValue,
        onInput: (event: Event) =>
          emit('update:modelValue', (event.target as HTMLInputElement).value),
      })
  },
})

const TextareaStub = defineComponent({
  props: {
    modelValue: { type: String, default: '' },
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () =>
      h('textarea', {
        value: props.modelValue,
        onInput: (event: Event) =>
          emit('update:modelValue', (event.target as HTMLTextAreaElement).value),
      })
  },
})

const InputNumberStub = defineComponent({
  props: {
    modelValue: { type: [String, Number], default: 0 },
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () =>
      h('input', {
        type: 'number',
        value: props.modelValue,
        onInput: (event: Event) =>
          emit('update:modelValue', Number((event.target as HTMLInputElement).value)),
      })
  },
})

const DatePickerStub = defineComponent({
  props: {
    modelValue: { type: [String, Date], default: '' },
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () =>
      h('input', {
        type: 'date',
        value:
          props.modelValue instanceof Date
            ? props.modelValue.toISOString().slice(0, 10)
            : props.modelValue,
        onInput: (event: Event) =>
          emit('update:modelValue', (event.target as HTMLInputElement).value),
      })
  },
})

const SelectStub = defineComponent({
  props: {
    modelValue: { type: [String, Number], default: undefined },
    options: { type: Array, default: () => [] },
    optionLabel: { type: String, default: 'label' },
    optionValue: { type: String, default: 'value' },
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () =>
      h(
        'select',
        {
          value: props.modelValue ?? '',
          onChange: (event: Event) =>
            emit('update:modelValue', (event.target as HTMLSelectElement).value),
        },
        (props.options as Array<Record<string, string>>).map((option) =>
          h(
            'option',
            { key: option[props.optionValue], value: option[props.optionValue] },
            option[props.optionLabel],
          ),
        ),
      )
  },
})

const DialogStub = defineComponent({
  props: {
    visible: { type: Boolean, default: false },
    header: { type: String, default: '' },
  },
  template: '<div v-if="visible"><h2>{{ header }}</h2><slot /></div>',
})

const TagStub = defineComponent({
  props: { value: { type: String, default: '' } },
  template: '<span>{{ value }}</span>',
})

const CurrentRowKey = Symbol('client-invoices-row')

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
    '<div><slot /><DataTableRowStub v-for="row in value" :key="row.id" :row="row"><slot /></DataTableRowStub></div>',
})

const ColumnStub = defineComponent({
  props: {
    field: { type: String, default: '' },
    header: { type: String, default: '' },
  },
  setup(props, { slots }) {
    const row = inject<Record<string, unknown> | null>(CurrentRowKey, null)
    return () =>
      h('div', [
        props.header ? h('div', props.header) : null,
        row
          ? slots.body
            ? slots.body({ data: row })
            : h('div', String(row[props.field] ?? ''))
          : null,
      ])
  },
})

async function flushView() {
  await Promise.resolve()
  await Promise.resolve()
  await nextTick()
}

function mountView() {
  return mount(ClientInvoicesView, {
    global: {
      stubs: {
        AppPage: ContainerStub,
        AppPageHeader: ContainerStub,
        AppPanel: ContainerStub,
        AppStatCard: AppStatCardStub,
        AppListState: ContainerStub,
        AppDateRangeFilter: ContainerStub,
        AppFilterMultiSelect: ContainerStub,
        AppNumberRangeFilter: ContainerStub,
        ClientInvoiceForm: ContainerStub,
        Button: ButtonStub,
        Column: ColumnStub,
        ConfirmDialog: ContainerStub,
        DataTable: DataTableStub,
        DatePicker: DatePickerStub,
        Dialog: DialogStub,
        InputNumber: InputNumberStub,
        InputText: InputTextStub,
        ProgressSpinner: ContainerStub,
        Select: SelectStub,
        Tag: TagStub,
        Textarea: TextareaStub,
      },
    },
  })
}

describe('ClientInvoicesView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockListContactsApi.mockResolvedValue([
      { id: 10, type: 'client', nom: 'Dupont', prenom: 'Alice', email: null, telephone: null },
    ] as never)
    mockListInvoicesApi.mockImplementation(async (filters) => {
      if (filters?.from_date === '2025-01-01' && filters?.to_date === '2025-12-31') {
        return [invoiceFixture] as never
      }
      return [invoiceFixture, historicalInvoiceFixture] as never
    })
    mockListPayments.mockResolvedValue([])
    mockCreatePayment.mockResolvedValue({
      id: 7,
      invoice_id: 1,
      invoice_number: 'F-2025-001',
      invoice_type: 'client',
      contact_id: 10,
      amount: '100.00',
      date: '2025-03-01',
      method: 'cheque',
      cheque_number: 'CHQ-001',
      reference: null,
      notes: null,
      deposited: false,
      deposit_date: null,
      created_at: '2025-03-01T00:00:00',
    })
  })

  it('creates a cash payment from an unpaid client invoice', async () => {
    const wrapper = mountView()
    await flushView()

    const recordButton = wrapper
      .findAll('button')
      .find((button) => button.attributes('title') === 'invoices.record_payment')

    expect(recordButton).toBeTruthy()

    await recordButton!.trigger('click')
    await flushView()

    const amountInput = wrapper.find('input[type="number"]')
    expect((amountInput.element as HTMLInputElement).value).toBe('100')

    const methodSelect = wrapper.findAll('select').at(-1)
    expect(methodSelect).toBeTruthy()
    await methodSelect!.setValue('especes')

    const paymentForm = wrapper.findAll('form').at(-1)
    expect(paymentForm).toBeTruthy()

    await paymentForm!.trigger('submit')
    await flushView()

    expect(mockCreatePayment).toHaveBeenCalledWith({
      invoice_id: 1,
      contact_id: 10,
      amount: '100.00',
      date: expect.any(String),
      method: 'especes',
      cheque_number: null,
      reference: null,
      notes: null,
    })
  })

  it('shows separate exercise and total receivable metrics', async () => {
    const wrapper = mountView()
    await flushView()

    expect(wrapper.text()).toContain('invoices.client.metrics.remaining_exercise_amount')
    expect(wrapper.text()).toContain('100.00 €')
    expect(wrapper.text()).toContain('invoices.client.metrics.exercise_count')
    expect(wrapper.text()).toContain('invoices.client.metrics.total_receivables_amount')
    expect(wrapper.text()).toContain('180.00 €')
    expect(wrapper.text()).toContain('invoices.client.metrics.historical_carryover')
  })

  it('computes overdue metrics from due date and remaining amount, not only status', async () => {
    const wrapper = mountView()
    await flushView()

    expect(wrapper.text()).toContain('invoices.client.metrics.overdue_amount')
    expect(wrapper.text()).toContain('180.00 €')
    expect(wrapper.text()).toContain('invoices.client.metrics.overdue_count')
  })
})
