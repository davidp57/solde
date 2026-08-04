import { mount } from '@vue/test-utils'
import { defineComponent, h, inject, nextTick, provide } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}))

const toastAdd = vi.fn()
const confirmRequire = vi.fn()

vi.mock('primevue/usetoast', () => ({
  useToast: () => ({ add: toastAdd }),
}))

vi.mock('primevue/useconfirm', () => ({
  useConfirm: () => ({ require: confirmRequire }),
}))

// The view now refreshes the shared store so the header year selector follows.
const fiscalYearStoreMock = { refresh: vi.fn().mockResolvedValue(undefined) }

vi.mock('../../stores/fiscalYear', () => ({
  useFiscalYearStore: () => fiscalYearStoreMock,
}))

vi.mock('../../api/accounting', () => ({
  listFiscalYearsApi: vi.fn(),
  createFiscalYearApi: vi.fn(),
  closeFiscalYearApi: vi.fn(),
  closeFiscalYearAdministrativeApi: vi.fn(),
  getFiscalYearPreCloseChecksApi: vi.fn(),
  openNextFiscalYearApi: vi.fn(),
}))

import FiscalYearView from '../../views/FiscalYearView.vue'
import {
  closeFiscalYearApi,
  getFiscalYearPreCloseChecksApi,
  listFiscalYearsApi,
  openNextFiscalYearApi,
} from '../../api/accounting'

const mockList = vi.mocked(listFiscalYearsApi)
const mockClose = vi.mocked(closeFiscalYearApi)
const mockChecks = vi.mocked(getFiscalYearPreCloseChecksApi)
const mockOpenNext = vi.mocked(openNextFiscalYearApi)

const openYear = {
  id: 1,
  name: '2025-2026',
  start_date: '2025-08-01',
  end_date: '2026-07-31',
  status: 'open' as const,
}

const closedYear = { ...openYear, status: 'closed' as const }

const ContainerStub = defineComponent({ template: '<div><slot /></div>' })

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
          title: props.label,
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
  },
  emits: ['update:modelValue'],
  setup(props, { attrs, emit }) {
    return () =>
      h('input', {
        'data-testid': attrs['data-testid'],
        type: props.type,
        value: props.modelValue ?? '',
        onInput: (event: Event) =>
          emit('update:modelValue', (event.target as HTMLInputElement).value),
      })
  },
})

const DialogStub = defineComponent({
  props: {
    visible: { type: Boolean, default: false },
    header: { type: String, default: '' },
  },
  emits: ['update:visible'],
  template: '<div v-if="visible"><h2>{{ header }}</h2><slot /><slot name="footer" /></div>',
})

const CurrentRowKey = Symbol('current-row')

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
    '<div><DataTableRowStub v-for="row in value" :key="row.id" :row="row"><slot /></DataTableRowStub></div>',
})

const ColumnStub = defineComponent({
  props: { field: { type: String, default: '' }, header: { type: String, default: '' } },
  setup(props, { slots }) {
    const row = inject<Record<string, unknown> | null>(CurrentRowKey, null)
    return () =>
      h('div', { class: 'column-stub' }, [
        row
          ? slots.body
            ? slots.body({ data: row })
            : h('div', {}, String(row[props.field] ?? ''))
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
  return mount(FiscalYearView, {
    global: {
      stubs: {
        AppPage: ContainerStub,
        AppPageHeader: ContainerStub,
        AppPanel: ContainerStub,
        AppListState: ContainerStub,
        AppMobileCardList: ContainerStub,
        AppDateRangeFilter: true,
        AppFilterMultiSelect: true,
        Button: ButtonStub,
        Column: ColumnStub,
        ConfirmDialog: true,
        DataTable: DataTableStub,
        Dialog: DialogStub,
        InputText: InputTextStub,
        Message: ContainerStub,
        Tag: true,
      },
    },
  })
}

describe('FiscalYearView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockList.mockResolvedValue([openYear])
    mockChecks.mockResolvedValue([])
    mockClose.mockResolvedValue(closedYear)
    mockOpenNext.mockResolvedValue({
      id: 2,
      name: '2026-2027',
      start_date: '2026-08-01',
      end_date: '2027-07-31',
      status: 'open',
    })
  })

  it('shows the pre-close warnings before closing', async () => {
    mockChecks.mockResolvedValue(['3 écriture(s) sans exercice associé — vérifier avant clôture.'])

    const wrapper = mountView()
    await flushView()

    await wrapper.get('[title="accounting.fiscalYear.close"]').trigger('click')
    await flushView()

    expect(mockChecks).toHaveBeenCalledWith(1)
    expect(wrapper.text()).toContain('3 écriture(s) sans exercice associé')
    expect(wrapper.text()).toContain('accounting.fiscalYear.checks_warning_intro')
  })

  it('reports a clean check and closes on confirmation', async () => {
    const wrapper = mountView()
    await flushView()

    await wrapper.get('[title="accounting.fiscalYear.close"]').trigger('click')
    await flushView()
    expect(wrapper.text()).toContain('accounting.fiscalYear.pre_close_ok')

    await wrapper.get('[data-testid="fy-close-confirm"]').trigger('click')
    await flushView()

    expect(mockClose).toHaveBeenCalledWith(1)
  })

  it('offers the rollover only on a closed year with no successor', async () => {
    const wrapper = mountView()
    await flushView()
    expect(wrapper.find('[data-testid="fy-open-next"]').exists()).toBe(false)

    mockList.mockResolvedValue([closedYear])
    const closedWrapper = mountView()
    await flushView()
    expect(closedWrapper.find('[data-testid="fy-open-next"]').exists()).toBe(true)

    mockList.mockResolvedValue([
      closedYear,
      { id: 2, name: '2026-2027', start_date: '2026-08-01', end_date: '2027-07-31', status: 'open' },
    ])
    const rolledWrapper = mountView()
    await flushView()
    expect(rolledWrapper.find('[data-testid="fy-open-next"]').exists()).toBe(false)
  })

  it('prefills the next year in the continuity of the closed one', async () => {
    mockList.mockResolvedValue([closedYear])

    const wrapper = mountView()
    await flushView()
    await wrapper.get('[data-testid="fy-open-next"]').trigger('click')
    await flushView()

    expect((wrapper.get('[data-testid="fy-next-name"]').element as HTMLInputElement).value).toBe(
      '2026-2027',
    )

    await wrapper.get('[data-testid="fy-next-confirm"]').trigger('click')
    await flushView()

    expect(mockOpenNext).toHaveBeenCalledWith(1, {
      name: '2026-2027',
      start_date: '2026-08-01',
      end_date: '2027-07-31',
    })
    // Without this the header selector would not offer the year just created.
    expect(fiscalYearStoreMock.refresh).toHaveBeenCalled()
  })
})
