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
  totalCounts: {} as Record<string, number>,
  init: vi.fn().mockResolvedValue(undefined),
  effectiveLimit: vi.fn().mockReturnValue(500),
  requestLimit: vi.fn().mockReturnValue(500),
  setTotalCount: vi.fn((viewKey: string, total: number) => {
    limitStoreMock.totalCounts[viewKey] = total
  }),
  isDisabled: vi.fn().mockReturnValue(false),
  hasMore: vi.fn().mockReturnValue(false),
}

vi.mock('../../stores/listLimit', () => ({
  useListLimitStore: () => limitStoreMock,
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
  listInvoicesWithCountApi: vi.fn(),
  deleteInvoiceApi: vi.fn(),
  duplicateInvoiceApi: vi.fn(),
  downloadInvoicePdfApi: vi.fn(() => Promise.resolve(new Blob(['%PDF'], { type: 'application/pdf' }))),
  sendInvoiceEmailApi: vi.fn(),
}))

vi.mock('../../api/payments', () => ({
  listPayments: vi.fn(),
  createPayment: vi.fn(),
  suggestChequeNumber: vi.fn().mockResolvedValue('20250101.01'),
}))

import ClientInvoicesView from '../../views/ClientInvoicesView.vue'
import { listContactsApi } from '../../api/contacts'
import { listInvoicesApi, listInvoicesWithCountApi } from '../../api/invoices'
import { createPayment, listPayments } from '../../api/payments'

const mockListContactsApi = vi.mocked(listContactsApi)
const mockListInvoicesApi = vi.mocked(listInvoicesApi)
const mockListInvoicesWithCountApi = vi.mocked(listInvoicesWithCountApi)
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

const AppListLimitBannerStub = defineComponent({
  props: {
    fetchedCount: { type: Number, default: 0 },
    limit: { type: Number, default: 0 },
    viewKey: { type: String, default: '' },
  },
  template:
    '<div data-testid="limit-banner-props">banner-fetched:{{ fetchedCount }}|banner-limit:{{ limit }}|banner-view:{{ viewKey }}</div>',
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
  return mount(ClientInvoicesView, {
    global: {
      stubs: {
        AppPage: ContainerStub,
        AppPageHeader: ContainerStub,
        AppPanel: ContainerStub,
        AppStatCard: AppStatCardStub,
        AppRowActions: InvoiceRowActionsStub,
        InvoiceTypeToggle: ContainerStub,
        AppListState: ContainerStub,
        AppDateRangeFilter: ContainerStub,
        AppFilterMultiSelect: ContainerStub,
        AppNumberRangeFilter: ContainerStub,
        ClientInvoiceForm: ContainerStub,
        Button: ButtonStub,
        Column: ColumnStub,
        ConfirmDialog: ContainerStub,
        DataTable: DataTableStub,
        AppDatePicker: DatePickerStub,
        Dialog: DialogStub,
        InputNumber: InputNumberStub,
        InputText: InputTextStub,
        ProgressSpinner: ContainerStub,
        Select: SelectStub,
        Tag: TagStub,
        Textarea: TextareaStub,
        AppListLimitBanner: AppListLimitBannerStub,
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
    mockListInvoicesWithCountApi.mockResolvedValue({ items: [invoiceFixture], total: 1 } as never)
    mockListInvoicesApi.mockResolvedValue([invoiceFixture, historicalInvoiceFixture] as never)
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

  it('renders the receivable funnel hero with the remaining-to-collect amount', async () => {
    const wrapper = mountView()
    await flushView()

    // Displayed set = invoiceFixture only (total 120, paid 20) → remaining 100.
    expect(wrapper.text()).toContain('invoices.funnel.remaining_client')
    // Full formatted amount locks the prop passed to the funnel (remaining = 120 - 20).
    expect(wrapper.find('.invoice-funnel__amount').text()).toContain('100,00')
  })

  it('reflects overdue amount in the funnel (due date + remaining, not only status)', async () => {
    const wrapper = mountView()
    await flushView()

    // invoiceFixture is past its due date with a remaining balance → overdue segment present.
    expect(wrapper.find('.invoice-funnel__segment--overdue').exists()).toBe(true)
    expect(wrapper.text()).toContain('invoices.funnel.overdue')
  })

  it('passes raw API fetched count to limit banner before local irrecoverable filtering', async () => {
    mockListInvoicesWithCountApi.mockResolvedValue({
      items: [
        invoiceFixture,
        {
          ...historicalInvoiceFixture,
          id: 3,
          status: 'irrecoverable',
        },
      ],
      total: 1200,
    } as never)

    const wrapper = mountView()
    await flushView()

    const banner = wrapper.get('[data-testid="limit-banner-props"]')
    expect(banner.text()).toContain('banner-fetched:2')
    expect(banner.text()).toContain('banner-limit:500')
    expect(banner.text()).toContain('banner-view:invoices-client')
  })
})

// ---------------------------------------------------------------------------
// History dialog navigation (BIZ-165 + BIZ-168)
// ---------------------------------------------------------------------------

describe('ClientInvoicesView — history dialog navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockListContactsApi.mockResolvedValue([
      { id: 10, type: 'client', nom: 'Dupont', prenom: 'Alice', email: null, telephone: null },
    ] as never)
    // Both invoices returned for every call so displayedInvoices has 2 entries
    mockListInvoicesWithCountApi.mockResolvedValue({ items: [invoiceFixture, historicalInvoiceFixture], total: 2 } as never)
    mockListInvoicesApi.mockResolvedValue([invoiceFixture, historicalInvoiceFixture] as never)
    mockListPayments.mockResolvedValue([])
  })

  it('shows navigation counter and advances to next invoice on click', async () => {
    const wrapper = mountView()
    await flushView()

    const historyButtons = wrapper
      .findAll('button')
      .filter((btn) => btn.attributes('title') === 'invoices.history')
    expect(historyButtons.length).toBeGreaterThanOrEqual(1)

    await historyButtons[0].trigger('click')
    await flushView()

    // Counter shows "1 / 2" (top bar or bottom bar)
    expect(wrapper.text()).toContain('1 / 2')

    // Click the first enabled Next button
    const nextButton = wrapper
      .findAll('button')
      .find((btn) => btn.attributes('title') === 'common.next' && !btn.element.disabled)
    expect(nextButton).toBeTruthy()
    await nextButton!.trigger('click')
    await flushView()

    // Counter now shows "2 / 2"
    expect(wrapper.text()).toContain('2 / 2')
  })

  it('disables the Previous button when at the first invoice', async () => {
    const wrapper = mountView()
    await flushView()

    const historyButtons = wrapper
      .findAll('button')
      .filter((btn) => btn.attributes('title') === 'invoices.history')
    await historyButtons[0].trigger('click')
    await flushView()

    const prevButtons = wrapper
      .findAll('button')
      .filter((btn) => btn.attributes('title') === 'common.previous')
    expect(prevButtons.length).toBeGreaterThanOrEqual(1)
    // All Previous buttons must be disabled at index 0
    expect(prevButtons.every((btn) => btn.element.disabled)).toBe(true)
  })
})
