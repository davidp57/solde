import { mount } from '@vue/test-utils'
import { defineComponent, h, inject, nextTick, provide } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}))

vi.mock('../../api/accounting', () => ({
  getBilanApi: vi.fn(),
  getExportCsvUrl: vi.fn(() => '/bilan.csv'),
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

import AccountingBilanView from '../../views/AccountingBilanView.vue'
import { getBilanApi } from '../../api/accounting'

const mockGetBilanApi = vi.mocked(getBilanApi)

const ContainerStub = defineComponent({
  template: '<div><slot /><slot name="actions" /></div>',
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

const CurrentRowKey = Symbol('current-bilan-row')

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
  return mount(AccountingBilanView, {
    global: {
      stubs: {
        AppPage: ContainerStub,
        AppPageHeader: ContainerStub,
        AppPanel: ContainerStub,
        Button: ButtonStub,
        Column: ColumnStub,
        DataTable: DataTableStub,
        ProgressSpinner: true,
        Select: SelectStub,
      },
    },
  })
}

describe('AccountingBilanView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    fiscalYearStoreMock.initialize.mockResolvedValue(undefined)
    mockGetBilanApi.mockResolvedValue({
      actif: [
        {
          account_number: '512000',
          account_label: 'Banque',
          solde: '250.00',
        },
      ],
      passif: [
        {
          account_number: '401000',
          account_label: 'Fournisseurs',
          solde: '-42.12',
        },
      ],
      total_actif: '250.00',
      total_passif: '-42.12',
      resultat: '-12.34',
    })
  })

  it('renders negative signed amounts with accounting parentheses', async () => {
    const wrapper = mountView()
    await flushView()

    const formattedPassif = new Intl.NumberFormat('fr-FR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(42.12)
    const formattedResult = new Intl.NumberFormat('fr-FR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(12.34)

    expect(wrapper.text()).toContain(`(${formattedPassif})`)
    expect(wrapper.text()).toContain(`(${formattedResult}) €`)
    expect(wrapper.text()).not.toContain('-42.12')
    expect(wrapper.text()).not.toContain('-12.34')
  })
})