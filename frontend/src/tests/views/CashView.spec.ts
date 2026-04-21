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

vi.mock('../../api/cash', () => ({
  getCashBalance: vi.fn(),
  getCashFundsChart: vi.fn(),
  listCashEntries: vi.fn(),
  addCashEntry: vi.fn(),
  getCashEntry: vi.fn(),
  updateCashEntry: vi.fn(),
  listCashCounts: vi.fn(),
  addCashCount: vi.fn(),
}))

import CashView from '../../views/CashView.vue'
import {
  getCashBalance,
  getCashFundsChart,
  listCashEntries,
  listCashCounts,
  updateCashEntry,
} from '../../api/cash'

const mockGetCashBalance = vi.mocked(getCashBalance)
const mockGetCashFundsChart = vi.mocked(getCashFundsChart)
const mockListCashEntries = vi.mocked(listCashEntries)
const mockListCashCounts = vi.mocked(listCashCounts)
const mockUpdateCashEntry = vi.mocked(updateCashEntry)

const cashEntryFixture = {
  id: 1,
  date: '2025-02-15',
  amount: '45.00',
  type: 'in' as const,
  contact_id: null,
  payment_id: null,
  reference: 'CAISSE-2025-001',
  description: 'Participation sortie',
  source: 'manual' as const,
  balance_after: '145.00',
  is_system_opening: false,
}

const ContainerStub = defineComponent({
  template: '<div><slot /></div>',
})

const AppStatCardStub = defineComponent({
  props: {
    label: { type: String, default: '' },
    value: { type: [String, Number], default: '' },
    caption: { type: String, default: '' },
    tone: { type: String, default: '' },
  },
  template: '<div>{{ label }} {{ value }} {{ caption }} {{ tone }}</div>',
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
  emits: ['update:modelValue'],
  setup(props, { attrs, emit }) {
    return () =>
      h('input', {
        'data-testid': attrs['data-testid'],
        type: props.type,
        value: props.modelValue ?? '',
        disabled: props.disabled,
        onInput: (event: Event) =>
          emit('update:modelValue', (event.target as HTMLInputElement).value),
      })
  },
})

const InputNumberStub = defineComponent({
  props: {
    modelValue: { type: [String, Number], default: 0 },
  },
  emits: ['update:modelValue'],
  setup(props, { attrs, emit }) {
    return () =>
      h('input', {
        'data-testid': attrs['data-testid'],
        type: 'number',
        value: props.modelValue ?? 0,
        onInput: (event: Event) =>
          emit('update:modelValue', (event.target as HTMLInputElement).value),
      })
  },
})

const DatePickerStub = defineComponent({
  props: {
    modelValue: { type: [String, Date], default: '' },
  },
  emits: ['update:modelValue'],
  setup(props, { attrs, emit }) {
    return () =>
      h('input', {
        'data-testid': attrs['data-testid'],
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
  setup(props, { attrs, emit }) {
    return () =>
      h(
        'select',
        {
          'data-testid': attrs['data-testid'],
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

const TextareaStub = defineComponent({
  props: {
    modelValue: { type: String, default: '' },
  },
  emits: ['update:modelValue'],
  setup(props, { attrs, emit }) {
    return () =>
      h('textarea', {
        'data-testid': attrs['data-testid'],
        value: props.modelValue,
        onInput: (event: Event) =>
          emit('update:modelValue', (event.target as HTMLTextAreaElement).value),
      })
  },
})

const TagStub = defineComponent({
  props: { value: { type: String, default: '' } },
  template: '<span>{{ value }}</span>',
})

const DialogStub = defineComponent({
  props: {
    visible: { type: Boolean, default: false },
    header: { type: String, default: '' },
  },
  template: '<div v-if="visible"><h2>{{ header }}</h2><slot /><slot name="footer" /></div>',
})

const TabsStub = defineComponent({ template: '<div><slot /></div>' })
const TabListStub = defineComponent({ template: '<div><slot /></div>' })
const TabStub = defineComponent({ template: '<button><slot /></button>' })
const TabPanelsStub = defineComponent({ template: '<div><slot /></div>' })
const TabPanelStub = defineComponent({ template: '<div><slot /></div>' })

const CurrentRowKey = Symbol('current-cash-row')

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
  return mount(CashView, {
    global: {
      stubs: {
        AppPage: ContainerStub,
        AppPageHeader: ContainerStub,
        AppPanel: ContainerStub,
        AppStatCard: AppStatCardStub,
        Button: ButtonStub,
        Column: ColumnStub,
        DataTable: DataTableStub,
        DatePicker: DatePickerStub,
        Dialog: DialogStub,
        InputNumber: InputNumberStub,
        InputText: InputTextStub,
        Select: SelectStub,
        Tab: TabStub,
        TabList: TabListStub,
        TabPanel: TabPanelStub,
        TabPanels: TabPanelsStub,
        Tabs: TabsStub,
        Tag: TagStub,
        Textarea: TextareaStub,
        TrendLineChart: ContainerStub,
      },
    },
  })
}

describe('CashView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    fiscalYearStoreMock.selectedFiscalYearId = 2
    fiscalYearStoreMock.selectedFiscalYear = {
      id: 2,
      name: 'Exercice 2025',
      start_date: '2025-01-01',
      end_date: '2025-12-31',
    }
    fiscalYearStoreMock.initialized = true
    mockGetCashBalance.mockResolvedValue({ balance: '145.00' })
    mockGetCashFundsChart.mockResolvedValue([
      { month: '2025-01', balance: 110 },
      { month: '2025-02', balance: 145 },
    ])
    mockListCashEntries.mockResolvedValue([cashEntryFixture])
    mockListCashCounts.mockResolvedValue([])
    mockUpdateCashEntry.mockResolvedValue({ ...cashEntryFixture, reference: 'CAISSE-2025-002' })
  })

  it('loads journal and counts using the selected fiscal year dates', async () => {
    mountView()
    await flushView()

    expect(fiscalYearStoreMock.initialize).toHaveBeenCalled()
    expect(mockListCashEntries).toHaveBeenCalledWith({
      from_date: '2025-01-01',
      to_date: '2025-12-31',
    })
    expect(mockListCashCounts).toHaveBeenCalledWith({
      from_date: '2025-01-01',
      to_date: '2025-12-31',
    })
    expect(mockGetCashFundsChart).toHaveBeenCalledWith(6)
  })

  it('displays a global current balance and the selected fiscal year variation', async () => {
    const wrapper = mountView()
    await flushView()

    expect(wrapper.text()).toContain('cash.current_balance')
    expect(wrapper.text()).toContain('145.00 €')
    expect(wrapper.text()).toContain('cash.metrics.visible_scope_caption')
    expect(wrapper.text()).toContain('cash.period_variation')
    expect(wrapper.text()).toContain('+45.00 €')
    expect(wrapper.text()).toContain('cash.metrics.period_variation_caption')
  })

  it('displays the cash entry reference in the journal', async () => {
    const wrapper = mountView()
    await flushView()

    expect(wrapper.text()).toContain('cash.entry_reference')
    expect(wrapper.text()).toContain('CAISSE-2025-001')
  })

  it('opens the detail dialog for a cash entry', async () => {
    const wrapper = mountView()
    await flushView()

    await wrapper.get('[data-testid="cash-detail-button"]').trigger('click')
    await flushView()

    expect(wrapper.text()).toContain('cash.entry_details')
    expect(wrapper.text()).toContain('Participation sortie')
  })

  it('renders the system opening indicator when a cash entry is flagged', async () => {
    mockListCashEntries.mockResolvedValue([
      { ...cashEntryFixture, source: 'system_opening', is_system_opening: true },
    ])

    const wrapper = mountView()
    await flushView()

    expect(wrapper.text()).toContain('cash.origins.system_opening')
    expect(wrapper.find('.cash-entry-type__system-opening').exists()).toBe(true)
  })

  it('edits a cash entry from the journal', async () => {
    const wrapper = mountView()
    await flushView()

    await wrapper.get('[data-testid="cash-edit-button"]').trigger('click')
    await wrapper.get('[data-testid="cash-reference-input"]').setValue('CAISSE-2025-002')
    await wrapper.get('[data-testid="cash-save-button"]').trigger('click')
    await flushView()

    expect(mockUpdateCashEntry).toHaveBeenCalledWith(
      1,
      expect.objectContaining({
        amount: '45',
        date: '2025-02-15',
        type: 'in',
        reference: 'CAISSE-2025-002',
        description: 'Participation sortie',
      }),
    )
  })
})
