import { mount } from '@vue/test-utils'
import { computed, defineComponent, h, inject, nextTick, provide } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}))

vi.mock('../../api/accounting', () => ({
  getBalanceApi: vi.fn(),
}))

const fiscalYearStoreMock = {
  fiscalYears: [{ id: 12, name: '2025', status: 'open' }],
  selectedFiscalYearId: 12 as number | undefined,
  initialized: true,
  initialize: vi.fn().mockResolvedValue(undefined),
  setSelectedFiscalYear: vi.fn(),
}

vi.mock('../../stores/fiscalYear', () => ({
  useFiscalYearStore: () => fiscalYearStoreMock,
}))

import AccountingBalanceView from '../../views/AccountingBalanceView.vue'
import { getBalanceApi } from '../../api/accounting'

const mockGetBalanceApi = vi.mocked(getBalanceApi)

const ContainerStub = defineComponent({
  template: '<div><slot /></div>',
})

const ButtonStub = defineComponent({
  props: {
    label: { type: String, default: '' },
  },
  emits: ['click'],
  template: '<button @click="$emit(\'click\')">{{ label }}</button>',
})

const SelectStub = defineComponent({
  props: {
    modelValue: { type: [String, Number], default: undefined },
    options: { type: Array, default: () => [] },
    optionLabel: { type: String, default: undefined },
    optionValue: { type: String, default: undefined },
  },
  emits: ['update:modelValue', 'change'],
  template:
    '<select @change="$emit(\'change\')"><option v-for="option in options" :key="option[optionValue] ?? option" :value="option[optionValue] ?? option">{{ option[optionLabel] ?? option }}</option></select>',
})

const CurrentRowKey = Symbol('current-balance-row')

const DataTableRowStub = defineComponent({
  props: {
    row: { type: Object, required: true },
    rowClass: { type: Function, default: undefined },
  },
  setup(props, { slots }) {
    provide(CurrentRowKey, props.row)
    return () =>
      h(
        'div',
        {
          class: [
            'data-table-row',
            props.rowClass ? props.rowClass(props.row as Record<string, unknown>) : undefined,
          ],
        },
        slots.default ? slots.default() : [],
      )
  },
})

const DataTableStub = defineComponent({
  props: {
    value: { type: Array, default: () => [] },
    rowClass: { type: Function, default: undefined },
  },
  components: { DataTableRowStub },
  template:
    '<div><div class="table-header"><slot /></div><DataTableRowStub v-for="row in value" :key="row.account_number" :row="row" :row-class="rowClass"><slot /></DataTableRowStub></div>',
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

vi.mock('../../composables/useDataTableFilters', () => ({
  useDataTableFilters: (_rows: unknown, initialFilters: Record<string, unknown>) => ({
    filters: initialFilters,
    globalFilter: '',
    hasActiveFilters: computed(() => false),
    resetFilters: vi.fn(),
  }),
  textFilter: (value = '') => value,
  numericRangeFilter: () => null,
  inFilter: () => null,
}))

async function flushView() {
  await Promise.resolve()
  await nextTick()
}

function mountView() {
  return mount(AccountingBalanceView, {
    global: {
      stubs: {
        AppDateInput: true,
        AppFilterMultiSelect: true,
        AppNumberRangeFilter: true,
        AppPage: ContainerStub,
        AppPageHeader: ContainerStub,
        AppPanel: ContainerStub,
        Button: ButtonStub,
        Column: ColumnStub,
        DataTable: DataTableStub,
        InputText: true,
        Select: SelectStub,
      },
    },
  })
}

describe('AccountingBalanceView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    fiscalYearStoreMock.initialize.mockResolvedValue(undefined)
    mockGetBalanceApi.mockResolvedValue([
      {
        account_number: '411100',
        account_label: 'Adhérents',
        account_type: 'actif',
        total_debit: '761.50',
        total_credit: '0.00',
        solde: '761.50',
      },
      {
        account_number: '401000',
        account_label: 'Fournisseurs',
        account_type: 'passif',
        total_debit: '100.00',
        total_credit: '142.12',
        solde: '-42.12',
      },
      {
        account_number: '706110',
        account_label: 'Cours de soutien',
        account_type: 'produit',
        total_debit: '0.00',
        total_credit: '250.00',
        solde: '-250.00',
      },
    ])
  })

  it('renders negative balances with parentheses instead of a minus sign', async () => {
    const wrapper = mountView()
    await flushView()

    const expected = new Intl.NumberFormat('fr-FR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(42.12)

    expect(wrapper.text()).toContain(`(${expected})`)
    expect(wrapper.text()).not.toContain('-42.12')
  })

  it('highlights the key accounts in the balance table', async () => {
    const wrapper = mountView()
    await flushView()

    expect(wrapper.text()).toContain('accounting.balance.focus_label')
    expect(wrapper.find('.balance-row--focus-member_receivables').exists()).toBe(true)
    expect(wrapper.find('.balance-row--focus-supplier_payables').exists()).toBe(true)
    expect(wrapper.find('.balance-row--focus-current_account').exists()).toBe(false)
    expect(wrapper.findAll('.data-table-row').at(-1)?.classes()).not.toContain('balance-row--focus')
  })
})