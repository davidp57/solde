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

const limitStoreMock = {
  systemLimit: 500,
  init: vi.fn().mockResolvedValue(undefined),
  effectiveLimit: vi.fn().mockReturnValue(500),
  requestLimit: vi.fn().mockReturnValue(500),
  setTotalCount: vi.fn(),
  isDisabled: vi.fn().mockReturnValue(false),
  hasMore: vi.fn().mockReturnValue(false),
}

vi.mock('../../stores/listLimit', () => ({
  useListLimitStore: () => limitStoreMock,
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ replace: vi.fn() }),
}))

vi.mock('../../api/contacts', () => ({
  listContactsApi: vi.fn(),
}))

vi.mock('../../api/invoices', () => ({
  listInvoicesWithCountApi: vi.fn(),
  deleteInvoiceApi: vi.fn(),
  downloadInvoiceFileApi: vi.fn(() =>
    Promise.resolve(new Blob(['%PDF'], { type: 'application/pdf' })),
  ),
  uploadInvoiceFileApi: vi.fn(),
}))

vi.mock('../../api/payments', () => ({
  listPayments: vi.fn(),
  createPayment: vi.fn(),
  suggestChequeNumber: vi.fn().mockResolvedValue('20250101.01'),
}))

import SupplierInvoicesView from '../../views/SupplierInvoicesView.vue'
import { listContactsApi } from '../../api/contacts'
import { listInvoicesWithCountApi } from '../../api/invoices'
import { createPayment, listPayments, suggestChequeNumber } from '../../api/payments'

const mockListContactsApi = vi.mocked(listContactsApi)
const mockListInvoicesWithCountApi = vi.mocked(listInvoicesWithCountApi)
const mockListPayments = vi.mocked(listPayments)
const mockCreatePayment = vi.mocked(createPayment)
const mockSuggestChequeNumber = vi.mocked(suggestChequeNumber)

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

// Renders the contextual primary action and every overflow item as a button
// (title = label) so existing "find by title" interactions keep working.
const InvoiceRowActionsStub = defineComponent({
  props: ['primary', 'menuItems', 'menuAriaLabel'],
  setup(props) {
    return () =>
      h('div', { class: 'invoice-row-actions-stub' }, [
        h(
          'button',
          { title: props.primary.label, onClick: () => props.primary.command() },
          props.primary.label,
        ),
        ...(props.menuItems ?? [])
          .filter((item: { separator?: boolean }) => !item.separator)
          .map((item: { label?: string; class?: string; command?: () => void }) =>
            h('button', { title: item.label, class: item.class, onClick: () => item.command?.() }, item.label),
          ),
      ])
  },
})

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
        InvoiceRowActions: InvoiceRowActionsStub,
        AppListState: ContainerStub,
        AppDateRangeFilter: ContainerStub,
        AppFilterMultiSelect: ContainerStub,
        AppNumberRangeFilter: ContainerStub,
        AppTableSkeleton: ContainerStub,
        SupplierInvoiceForm: ContainerStub,
        AppListLimitBanner: ContainerStub,
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
    mockListInvoicesWithCountApi.mockResolvedValue({ items: [invoiceFixture, paidInvoiceFixture, draftInvoiceFixture], total: 3 } as never)
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
    // override: suggestion returns empty so the field stays empty
    mockSuggestChequeNumber.mockResolvedValueOnce('')

    const wrapper = mountView()
    await flushView()

    const paymentButton = wrapper
      .findAll('button')
      .find((btn) => btn.attributes('title') === 'invoices.record_payment')
    await paymentButton!.trigger('click')
    await flushView()

    // method is 'cheque', cheque_number is empty — submit should be blocked
    const paymentForm = wrapper.findAll('form').at(-1)!
    await paymentForm.trigger('submit')
    await flushView()

    expect(mockCreatePayment).not.toHaveBeenCalled()
    expect(toastAdd).toHaveBeenCalledWith(
      expect.objectContaining({ severity: 'warn' }),
    )
  })
})

// ---------------------------------------------------------------------------
// Preview dialog bottom navigation (BIZ-168)
// ---------------------------------------------------------------------------

describe('SupplierInvoicesView — preview dialog bottom navigation', () => {
  // Variants with file_path so the preview button (v-if="data.file_path") is rendered
  const invoiceWithFile = { ...invoiceFixture, file_path: 'uploads/FF-2025-001.pdf' }
  const paidInvoiceWithFile = { ...paidInvoiceFixture, file_path: 'uploads/FF-2025-002.pdf' }

  beforeEach(() => {
    vi.clearAllMocks()
    mockListContactsApi.mockResolvedValue([
      { id: 10, type: 'fournisseur', nom: 'Martin', prenom: 'Bob', email: null, telephone: null },
    ] as never)
    // Two invoices with file_path so the preview button is rendered for each
    mockListInvoicesWithCountApi.mockResolvedValue({ items: [invoiceWithFile, paidInvoiceWithFile], total: 2 } as never)
    mockListPayments.mockResolvedValue([])
  })

  it('shows navigation counter and advances via bottom bar Next button', async () => {
    const wrapper = mountView()
    await flushView()

    const previewButtons = wrapper
      .findAll('button')
      .filter((btn) => btn.attributes('title') === 'invoices.supplier.preview_file')
    expect(previewButtons.length).toBeGreaterThanOrEqual(1)

    await previewButtons[0].trigger('click')
    await flushView()

    // Counter shows "1 / 2"
    expect(wrapper.text()).toContain('1 / 2')

    // Click the last enabled Next button (bottom bar is last in the DOM)
    const nextButtons = wrapper
      .findAll('button')
      .filter((btn) => btn.attributes('title') === 'common.next' && !btn.element.disabled)
    expect(nextButtons.length).toBeGreaterThanOrEqual(1)
    await nextButtons[nextButtons.length - 1].trigger('click')
    await flushView()

    // Counter now shows "2 / 2"
    expect(wrapper.text()).toContain('2 / 2')
  })

  it('disables Previous at the first invoice in both nav bars', async () => {
    const wrapper = mountView()
    await flushView()

    const previewButtons = wrapper
      .findAll('button')
      .filter((btn) => btn.attributes('title') === 'invoices.supplier.preview_file')
    await previewButtons[0].trigger('click')
    await flushView()

    const prevButtons = wrapper
      .findAll('button')
      .filter((btn) => btn.attributes('title') === 'common.previous')
    expect(prevButtons.length).toBeGreaterThanOrEqual(1)
    // All Previous buttons must be disabled at index 0
    expect(prevButtons.every((btn) => btn.element.disabled)).toBe(true)
  })
})
