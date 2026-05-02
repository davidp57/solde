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

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ replace: vi.fn() }),
}))

vi.mock('../../api/contacts', () => ({
  listContactsApi: vi.fn(),
}))

vi.mock('../../api/invoices', () => ({
  listInvoicesApi: vi.fn(),
  deleteInvoiceApi: vi.fn(),
  downloadInvoiceFileApi: vi.fn(() =>
    Promise.resolve(new Blob(['%PDF'], { type: 'application/pdf' })),
  ),
  uploadInvoiceFileApi: vi.fn(),
}))

vi.mock('../../api/payments', () => ({
  listPayments: vi.fn(),
  createPayment: vi.fn(),
}))

import SupplierInvoicesView from '../../views/SupplierInvoicesView.vue'
import { listContactsApi } from '../../api/contacts'
import { listInvoicesApi } from '../../api/invoices'
import { createPayment, listPayments } from '../../api/payments'

const mockListContactsApi = vi.mocked(listContactsApi)
const mockListInvoicesApi = vi.mocked(listInvoicesApi)
const mockListPayments = vi.mocked(listPayments)
const mockCreatePayment = vi.mocked(createPayment)

const invoiceFixture = {
  id: 1,
  number: 'FF-2025-001',
  type: 'fournisseur' as const,
  contact_id: 10,
  date: '2025-02-10',
  due_date: '2025-03-10',
  label: null,
  description: 'Fournitures',
  reference: 'REF-001',
  total_amount: '200.00',
  paid_amount: '50.00',
  status: 'partial' as const,
  pdf_path: null,
  file_path: null,
  created_at: '2025-02-10T00:00:00',
  updated_at: '2025-02-10T00:00:00',
  lines: [],
}

const paidInvoiceFixture = {
  ...invoiceFixture,
  id: 2,
  number: 'FF-2025-002',
  total_amount: '100.00',
  paid_amount: '100.00',
  status: 'paid' as const,
}

const draftInvoiceFixture = {
  ...invoiceFixture,
  id: 3,
  number: 'FF-2025-003',
  total_amount: '80.00',
  paid_amount: '0.00',
  status: 'draft' as const,
}

// ---------------------------------------------------------------------------
// Stubs
// ---------------------------------------------------------------------------

const ContainerStub = defineComponent({
  template: '<div><slot /><slot name="actions" /></div>',
})

const AppStatCardStub = defineComponent({
  props: {
    label: { type: String, default: '' },
    value: { type: [String, Number], default: '' },
    caption: { type: String, default: '' },
  },
  template: '<div>{{ label }} {{ value }}</div>',
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
  props: { modelValue: { type: String, default: '' } },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () =>
      h('input', {
        value: props.modelValue,
        onInput: (e: Event) => emit('update:modelValue', (e.target as HTMLInputElement).value),
      })
  },
})

const TextareaStub = defineComponent({
  props: { modelValue: { type: String, default: '' } },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () =>
      h('textarea', {
        value: props.modelValue,
        onInput: (e: Event) => emit('update:modelValue', (e.target as HTMLTextAreaElement).value),
      })
  },
})

const InputNumberStub = defineComponent({
  props: { modelValue: { type: [String, Number], default: 0 } },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () =>
      h('input', {
        type: 'number',
        value: props.modelValue,
        onInput: (e: Event) =>
          emit('update:modelValue', Number((e.target as HTMLInputElement).value)),
      })
  },
})

const DatePickerStub = defineComponent({
  props: { modelValue: { type: [String, Date], default: '' } },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () =>
      h('input', {
        type: 'date',
        value:
          props.modelValue instanceof Date
            ? props.modelValue.toISOString().slice(0, 10)
            : props.modelValue,
        onInput: (e: Event) => emit('update:modelValue', (e.target as HTMLInputElement).value),
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
          onChange: (e: Event) =>
            emit('update:modelValue', (e.target as HTMLSelectElement).value),
        },
        (props.options as Array<Record<string, string>>).map((opt) =>
          h('option', { key: opt[props.optionValue], value: opt[props.optionValue] }, opt[props.optionLabel]),
        ),
      )
  },
})

const DialogStub = defineComponent({
  props: {
    visible: { type: Boolean, default: false },
    modelValue: { type: Boolean, default: false },
    header: { type: String, default: '' },
  },
  template: '<div v-if="visible || modelValue"><h2>{{ header }}</h2><slot /></div>',
})

const TagStub = defineComponent({
  props: { value: { type: String, default: '' } },
  template: '<span>{{ value }}</span>',
})

const CurrentRowKey = Symbol('supplier-invoices-row')

const DataTableRowStub = defineComponent({
  props: { row: { type: Object, required: true } },
  setup(props, { slots }) {
    provide(CurrentRowKey, props.row)
    return () => h('div', { class: 'data-row' }, slots.default ? slots.default() : [])
  },
})

const DataTableStub = defineComponent({
  props: { value: { type: Array, default: () => [] } },
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

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function flushView() {
  await Promise.resolve()
  await Promise.resolve()
  await nextTick()
}

function mountView() {
  return mount(SupplierInvoicesView, {
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
        AppTableSkeleton: ContainerStub,
        SupplierInvoiceForm: ContainerStub,
        Button: ButtonStub,
        Column: ColumnStub,
        ConfirmDialog: ContainerStub,
        DataTable: DataTableStub,
        AppDatePicker: DatePickerStub,
        Dialog: DialogStub,
        FileUpload: ContainerStub,
        InputNumber: InputNumberStub,
        InputText: InputTextStub,
        Select: SelectStub,
        Tag: TagStub,
        Textarea: TextareaStub,
      },
    },
  })
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('SupplierInvoicesView — payment dialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockListContactsApi.mockResolvedValue([
      { id: 10, type: 'fournisseur', nom: 'Martin', prenom: 'Bob', email: null, telephone: null },
    ] as never)
    mockListInvoicesApi.mockResolvedValue([invoiceFixture, paidInvoiceFixture, draftInvoiceFixture] as never)
    mockListPayments.mockResolvedValue([])
    mockCreatePayment.mockResolvedValue({
      id: 5,
      invoice_id: 1,
      invoice_number: 'FF-2025-001',
      invoice_type: 'fournisseur',
      contact_id: 10,
      amount: '150.00',
      date: '2025-03-01',
      method: 'especes',
      cheque_number: null,
      reference: null,
      notes: null,
      deposited: true,
      in_deposit: false,
      deposit_date: '2025-03-01',
      created_at: '2025-03-01T00:00:00',
    })
  })

  it('shows the payment button only for invoices with remaining balance and not draft', async () => {
    const wrapper = mountView()
    await flushView()

    const paymentButtons = wrapper
      .findAll('button')
      .filter((btn) => btn.attributes('title') === 'invoices.record_payment')

    // Only invoiceFixture (partial, remaining=150) should show the button
    // paidInvoiceFixture (remaining=0) and draftInvoiceFixture (draft) must not
    expect(paymentButtons).toHaveLength(1)
  })

  it('pre-fills amount with remaining balance when opening the dialog', async () => {
    const wrapper = mountView()
    await flushView()

    const paymentButton = wrapper
      .findAll('button')
      .find((btn) => btn.attributes('title') === 'invoices.record_payment')
    expect(paymentButton).toBeTruthy()

    await paymentButton!.trigger('click')
    await flushView()

    const amountInput = wrapper.find('input[type="number"]')
    // remaining = 200 - 50 = 150
    expect(Number((amountInput.element as HTMLInputElement).value)).toBe(150)
  })

  it('records a cash payment and calls createPayment with correct payload', async () => {
    const wrapper = mountView()
    await flushView()

    const paymentButton = wrapper
      .findAll('button')
      .find((btn) => btn.attributes('title') === 'invoices.record_payment')
    await paymentButton!.trigger('click')
    await flushView()

    // Switch method to especes
    const selects = wrapper.findAll('select')
    const methodSelect = selects.at(-1)!
    await methodSelect.setValue('especes')

    const paymentForm = wrapper.findAll('form').at(-1)!
    await paymentForm.trigger('submit')
    await flushView()

    expect(mockCreatePayment).toHaveBeenCalledWith(
      expect.objectContaining({
        invoice_id: 1,
        contact_id: 10,
        amount: '150.00',
        method: 'especes',
        cheque_number: null,
      }),
    )
  })

  it('requires a cheque number when method is cheque', async () => {
    const wrapper = mountView()
    await flushView()

    const paymentButton = wrapper
      .findAll('button')
      .find((btn) => btn.attributes('title') === 'invoices.record_payment')
    await paymentButton!.trigger('click')
    await flushView()

    // method is 'cheque' by default, cheque_number is empty — submit should be blocked
    const paymentForm = wrapper.findAll('form').at(-1)!
    await paymentForm.trigger('submit')
    await flushView()

    expect(mockCreatePayment).not.toHaveBeenCalled()
    expect(toastAdd).toHaveBeenCalledWith(
      expect.objectContaining({ severity: 'warn' }),
    )
  })
})
