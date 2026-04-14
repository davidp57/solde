import { mount } from '@vue/test-utils'
import { computed, defineComponent, nextTick, ref } from 'vue'
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

vi.mock('../../api/accounting', () => ({
  listSalariesApi: vi.fn(),
  getSalarySummaryApi: vi.fn(),
  createSalaryApi: vi.fn(),
  updateSalaryApi: vi.fn(),
  deleteSalaryApi: vi.fn(),
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
    name: '2024-2025',
    start_date: '2024-08-01',
    end_date: '2025-07-31',
    status: 'open',
  },
  initialized: true,
  initialize: vi.fn().mockResolvedValue(undefined),
  setSelectedFiscalYear: vi.fn(),
}

vi.mock('../../stores/fiscalYear', () => ({
  useFiscalYearStore: () => fiscalYearStoreMock,
}))

vi.mock('../../api/client', () => ({
  default: {
    get: vi.fn(),
  },
}))

import SalaryView from '../../views/SalaryView.vue'
import apiClient from '../../api/client'
import { getSalarySummaryApi, listSalariesApi } from '../../api/accounting'

const mockListSalariesApi = vi.mocked(listSalariesApi)
const mockGetSalarySummaryApi = vi.mocked(getSalarySummaryApi)
const mockApiClientGet = vi.mocked(apiClient.get)

const ContainerStub = defineComponent({
  template: '<div><slot /></div>',
})

const AppStatCardStub = defineComponent({
  props: {
    label: { type: String, default: '' },
    value: { type: [String, Number], default: '' },
  },
  template: '<div class="stat-card">{{ label }}:{{ value }}</div>',
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
  template: '<select @change="$emit(\'change\')"></select>',
})

const InputTextStub = defineComponent({
  props: {
    modelValue: { type: [String, Number], default: '' },
  },
  emits: ['update:modelValue', 'change'],
  template: '<input :value="modelValue" @change="$emit(\'change\')" />',
})

const InputNumberStub = defineComponent({
  props: {
    modelValue: { type: [String, Number], default: 0 },
  },
  emits: ['update:modelValue'],
  template: '<input :value="modelValue" />',
})

vi.mock('../../composables/useTableFilter', () => ({
  useTableFilter: (source: { value: unknown[] }) => {
    const filterText = ref('')
    return {
      filterText,
      filtered: computed(() => source.value),
    }
  },
  applyFilter: <T>(rows: T[]) => rows,
}))

async function flushView() {
  await Promise.resolve()
  await nextTick()
}

function mountView() {
  return mount(SalaryView, {
    global: {
      stubs: {
        AppPage: ContainerStub,
        AppPageHeader: ContainerStub,
        AppPanel: ContainerStub,
        AppStatCard: AppStatCardStub,
        Button: ButtonStub,
        Column: ContainerStub,
        ConfirmDialog: true,
        DataTable: ContainerStub,
        Dialog: ContainerStub,
        InputNumber: InputNumberStub,
        InputText: InputTextStub,
        Select: SelectStub,
        Textarea: true,
        Toast: true,
      },
    },
  })
}

describe('SalaryView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockApiClientGet.mockResolvedValue({
      data: [{ id: 1, nom: 'Martin', prenom: 'Alice' }],
    })
    mockListSalariesApi.mockResolvedValue([
      {
        id: 1,
        employee_id: 1,
        employee_name: 'Alice Martin',
        month: '2025-07',
        hours: '10.50' as unknown as number,
        gross: '1200.40' as unknown as number,
        employee_charges: '150.10' as unknown as number,
        employer_charges: '300.20' as unknown as number,
        tax: '80.30' as unknown as number,
        net_pay: '970.00' as unknown as number,
        total_cost: '1500.60' as unknown as number,
        notes: null,
        created_at: '2026-04-13T08:00:00',
      },
      {
        id: 2,
        employee_id: 1,
        employee_name: 'Alice Martin',
        month: '2025-08',
        hours: '12.00' as unknown as number,
        gross: '1800.00' as unknown as number,
        employee_charges: '220.00' as unknown as number,
        employer_charges: '420.00' as unknown as number,
        tax: '120.00' as unknown as number,
        net_pay: '1460.00' as unknown as number,
        total_cost: '2220.00' as unknown as number,
        notes: null,
        created_at: '2026-04-13T08:00:00',
      },
    ])
    mockGetSalarySummaryApi.mockResolvedValue([])
  })

  it('aggregates salary metrics without rendering NaN when numeric fields arrive as strings', async () => {
    const wrapper = mountView()
    await flushView()

    const expectedGross = new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
    }).format(3000.4)
    const expectedNet = new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
    }).format(2430)
    const expectedTotalCost = new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
    }).format(3720.6)

    expect(wrapper.text()).not.toContain('NaN')
    expect(wrapper.text()).toContain(`salary.gross:${expectedGross}`)
    expect(wrapper.text()).toContain(`salary.net_pay:${expectedNet}`)
    expect(wrapper.text()).toContain(`salary.total_cost:${expectedTotalCost}`)
  })

  it('loads salaries and summary for the selected fiscal year range', async () => {
    mountView()
    await flushView()

    expect(mockListSalariesApi).toHaveBeenCalledWith({
      from_month: '2024-08',
      to_month: '2025-07',
      employee_id: undefined,
      month: undefined,
    })
    expect(mockGetSalarySummaryApi).toHaveBeenCalledWith({
      from_month: '2024-08',
      to_month: '2025-07',
    })
  })
})
