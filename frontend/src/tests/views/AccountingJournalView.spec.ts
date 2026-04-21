import { mount } from '@vue/test-utils'
import { defineComponent, h, inject, nextTick, provide } from 'vue'
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

vi.mock('../../api/accounting', () => ({
  getJournalGroupsApi: vi.fn(),
  createManualEntryApi: vi.fn(),
  updateManualEntryApi: vi.fn(),
  getExportCsvUrl: vi.fn(() => '/journal.csv'),
}))

const routerPush = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: routerPush,
  }),
}))

const fiscalYearStoreMock = {
  fiscalYears: [{ id: 12, name: '2025', status: 'open' }],
  selectedFiscalYearId: 12 as number | undefined,
  initialized: true,
  initialize: vi.fn().mockResolvedValue(undefined),
  setSelectedFiscalYear: vi.fn((value?: number) => {
    fiscalYearStoreMock.selectedFiscalYearId = value
  }),
}

vi.mock('../../stores/fiscalYear', () => ({
  useFiscalYearStore: () => fiscalYearStoreMock,
}))

import AccountingJournalView from '../../views/AccountingJournalView.vue'
import { getJournalGroupsApi } from '../../api/accounting'

const mockGetJournalGroupsApi = vi.mocked(getJournalGroupsApi)

const ContainerStub = defineComponent({
  template: '<div><slot /></div>',
})

const AppStatCardStub = defineComponent({
  props: {
    label: { type: String, default: '' },
    value: { type: [String, Number], default: '' },
  },
  template: '<div>{{ label }}:{{ value }}</div>',
})

const ButtonStub = defineComponent({
  props: {
    label: { type: String, default: '' },
    disabled: { type: Boolean, default: false },
    title: { type: String, default: '' },
  },
  emits: ['click'],
  template:
    '<button :disabled="disabled" :title="title" @click="$emit(\'click\')">{{ label || title }}</button>',
})

const InputTextStub = defineComponent({
  props: {
    modelValue: { type: String, default: '' },
    placeholder: { type: String, default: '' },
  },
  emits: ['update:modelValue', 'keydown.enter'],
  template:
    '<input :value="modelValue" :placeholder="placeholder" @input="$emit(\'update:modelValue\', $event.target.value)" @keydown.enter="$emit(\'keydown.enter\')" />',
})

const SelectStub = defineComponent({
  props: {
    modelValue: { type: [String, Number], default: undefined },
    options: { type: Array, default: () => [] },
    optionLabel: { type: String, default: 'label' },
    optionValue: { type: String, default: 'value' },
    placeholder: { type: String, default: '' },
  },
  emits: ['update:modelValue'],
  methods: {
    optionValueOf(option: Record<string, unknown>) {
      return option[this.optionValue] as string | number | undefined
    },
    optionLabelOf(option: Record<string, unknown>) {
      return option[this.optionLabel] as string | number | undefined
    },
  },
  template: `
    <select
      :value="modelValue == null ? '' : String(modelValue)"
      @change="$emit('update:modelValue', $event.target.value || undefined)"
    >
      <option value="">{{ placeholder }}</option>
      <option
        v-for="option in options"
        :key="String(optionValueOf(option))"
        :value="String(optionValueOf(option) ?? '')"
      >
        {{ optionLabelOf(option) }}
      </option>
    </select>
  `,
})

const TagStub = defineComponent({
  props: {
    value: { type: String, default: '' },
    severity: { type: String, default: '' },
  },
  template: '<span data-testid="journal-source-tag" :data-severity="severity">{{ value }}</span>',
})

const CurrentRowKey = Symbol('current-journal-row')

const DataTableRowStub = defineComponent({
  props: {
    row: { type: Object, required: true },
  },
  setup(props, { slots }) {
    provide(CurrentRowKey, props.row)
    return () => h('div', slots.default ? slots.default() : [])
  },
})

const DataTableStub = defineComponent({
  props: {
    value: { type: Array, default: () => [] },
  },
  components: { DataTableRowStub },
  template:
    '<div><div class="table-header"><slot /></div><DataTableRowStub v-for="row in value" :key="row.group_key" :row="row"><slot /></DataTableRowStub></div>',
})

const ColumnStub = defineComponent({
  props: {
    field: { type: String, default: '' },
  },
  setup(props, { slots }) {
    const row = inject<Record<string, unknown> | null>(CurrentRowKey, null)
    return () =>
      row
        ? h('div', slots.body ? slots.body({ data: row }) : String(row[props.field] ?? ''))
        : h('div')
  },
})

async function flushView() {
  await Promise.resolve()
  await nextTick()
}

function mountView() {
  return mount(AccountingJournalView, {
    global: {
      stubs: {
        AppPage: ContainerStub,
        AppPageHeader: ContainerStub,
        AppPanel: ContainerStub,
        AppStatCard: AppStatCardStub,
        Button: ButtonStub,
        Column: ColumnStub,
        DataTable: DataTableStub,
        Dialog: ContainerStub,
        InputText: InputTextStub,
        Select: SelectStub,
        Tag: TagStub,
      },
    },
  })
}

describe('AccountingJournalView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    fiscalYearStoreMock.selectedFiscalYearId = 12
    mockGetJournalGroupsApi.mockResolvedValue([
      {
        group_key: 'salary-import:2025-07:accrual',
        date: '2025-08-01',
        label: 'Charges patronales 2025.07 (+3)',
        fiscal_year_id: 12,
        source_type: 'salary',
        source_id: null,
        source_reference: null,
        source_contact_name: null,
        source_invoice_id: null,
        source_invoice_type: null,
        source_invoice_number: null,
        line_count: 5,
        total_debit: '1938.62',
        total_credit: '1938.62',
        account_numbers: ['645100', '641000', '421000', '431100'],
        editable: false,
        lines: [],
      },
    ])
    fiscalYearStoreMock.initialize.mockResolvedValue(undefined)
  })

  it('loads the journal for the selected fiscal year', async () => {
    mountView()
    await flushView()

    expect(fiscalYearStoreMock.initialize).toHaveBeenCalledTimes(1)
    expect(mockGetJournalGroupsApi).toHaveBeenCalledWith(
      expect.objectContaining({
        fiscal_year_id: 12,
      }),
    )
  })

  it('uses a dedicated non-manual color for salary source tags', async () => {
    const wrapper = mountView()
    await flushView()

    expect(wrapper.get('[data-testid="journal-source-tag"]').attributes('data-severity')).toBe(
      'secondary',
    )
  })

  it('reloads when the source filter dropdown changes', async () => {
    const wrapper = mountView()
    await flushView()
    mockGetJournalGroupsApi.mockClear()

    const selects = wrapper.findAll('select')
    await selects[0]?.setValue('salary')
    await flushView()

    expect(mockGetJournalGroupsApi).toHaveBeenCalledWith(
      expect.objectContaining({
        source_type: 'salary',
        fiscal_year_id: 12,
      }),
    )
  })

  it('resets remote filters and reloads the journal', async () => {
    const wrapper = mountView()
    await flushView()

    const selects = wrapper.findAll('select')
    await selects[0]?.setValue('salary')
    await flushView()
    mockGetJournalGroupsApi.mockClear()

    const resetButton = wrapper
      .findAll('button')
      .find((button) => button.text() === 'common.reset_filters')

    expect(resetButton?.attributes('disabled')).toBeUndefined()

    await resetButton?.trigger('click')
    await flushView()

    expect(fiscalYearStoreMock.setSelectedFiscalYear).toHaveBeenCalledWith(undefined)
    expect(mockGetJournalGroupsApi).toHaveBeenCalledWith(
      expect.objectContaining({
        source_type: undefined,
      }),
    )
  })
})
