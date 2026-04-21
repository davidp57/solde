import { mount } from '@vue/test-utils'
import { defineComponent, h, inject, nextTick, provide } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}))

vi.mock('../../api/accounting', () => ({
  getResultatApi: vi.fn(),
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

import AccountingResultatView from '../../views/AccountingResultatView.vue'
import { getResultatApi } from '../../api/accounting'

const mockGetResultatApi = vi.mocked(getResultatApi)

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

const CurrentRowKey = Symbol('current-resultat-row')

const DataTableRowStub = defineComponent({
  props: {
    row: { type: Object, required: true },
    rowIndex: { type: Number, required: true },
  },
  setup(props, { slots }) {
    provide(CurrentRowKey, props.row)
    return () => h('div', { 'data-row-index': props.rowIndex }, slots.default ? slots.default() : [])
  },
})

const DataTableStub = defineComponent({
  props: {
    value: { type: Array, default: () => [] },
  },
  components: { DataTableRowStub },
  template:
    '<div><div class="table-header"><slot /></div><DataTableRowStub v-for="(row, index) in value" :key="`${row.account_number}-${index}`" :row="row" :row-index="index"><slot /></DataTableRowStub></div>',
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
  return mount(AccountingResultatView, {
    global: {
      stubs: {
        AppPage: ContainerStub,
        AppPageHeader: ContainerStub,
        AppPanel: ContainerStub,
        Button: ButtonStub,
        Column: ColumnStub,
        DataTable: DataTableStub,
        Select: SelectStub,
      },
    },
  })
}

describe('AccountingResultatView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    fiscalYearStoreMock.initialize.mockResolvedValue(undefined)
    mockGetResultatApi.mockResolvedValue({
      total_charges: '-42.12',
      total_produits: '128.50',
      resultat: '-15.50',
      charges: [
        {
          account_number: '606100',
          account_label: 'Achats',
          account_type: 'charge',
          total_debit: '0.00',
          total_credit: '0.00',
          solde: '-42.12',
        },
      ],
      produits: [
        {
          account_number: '706000',
          account_label: 'Prestations',
          account_type: 'produit',
          total_debit: '0.00',
          total_credit: '0.00',
          solde: '128.50',
        },
      ],
    })
  })

  it('renders negative totals and net result with accounting parentheses', async () => {
    const wrapper = mountView()
    await flushView()

    const formattedCharge = new Intl.NumberFormat('fr-FR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(42.12)
    const formattedResult = new Intl.NumberFormat('fr-FR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(15.5)

    expect(wrapper.text()).toContain(`(${formattedCharge})`)
    expect(wrapper.text()).toContain(`(${formattedResult})`)
    expect(wrapper.text()).not.toContain('-42.12')
    expect(wrapper.text()).not.toContain('-15.50')
  })
})