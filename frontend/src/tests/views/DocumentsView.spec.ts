import { mount } from '@vue/test-utils'
import { defineComponent, h, inject, nextTick, provide } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}))

vi.mock('../../api/document', () => ({
  listDocumentsApi: vi.fn(),
  listDocumentTagsApi: vi.fn(),
  uploadDocumentApi: vi.fn(),
  updateDocumentApi: vi.fn(),
  deleteDocumentApi: vi.fn(),
  getDocumentDownloadUrl: vi.fn((id: number) => `/api/documents/${id}/download`),
}))

const fiscalYearStoreMock = {
  fiscalYears: [{ id: 12, name: '2025', status: 'closed' }],
  selectedFiscalYearId: 12 as number | undefined,
  initialized: true,
  initialize: vi.fn().mockResolvedValue(undefined),
}

vi.mock('../../stores/fiscalYear', () => ({
  useFiscalYearStore: () => fiscalYearStoreMock,
}))

const authStoreMock = { canAccessManagement: true }

vi.mock('../../stores/auth', () => ({
  useAuthStore: () => authStoreMock,
}))

const toastAdd = vi.fn()
vi.mock('primevue/usetoast', () => ({ useToast: () => ({ add: toastAdd }) }))

let confirmAccept: (() => Promise<void>) | null = null
vi.mock('primevue/useconfirm', () => ({
  useConfirm: () => ({
    require: (options: { accept: () => Promise<void> }) => {
      confirmAccept = options.accept
    },
  }),
}))

import DocumentsView from '../../views/DocumentsView.vue'
import {
  deleteDocumentApi,
  listDocumentTagsApi,
  listDocumentsApi,
} from '../../api/document'

const mockList = vi.mocked(listDocumentsApi)
const mockTags = vi.mocked(listDocumentTagsApi)
const mockDelete = vi.mocked(deleteDocumentApi)

const ContainerStub = defineComponent({
  template: '<div><slot /><slot name="actions" /></div>',
})

const ButtonStub = defineComponent({
  props: { label: { type: String, default: '' } },
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
  template: '<select />',
})

const CurrentRowKey = Symbol('current-document-row')

const RowStub = defineComponent({
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
  props: { value: { type: Array, default: () => [] } },
  components: { RowStub },
  template:
    '<div><RowStub v-for="(row, index) in value" :key="row.id" :row="row" :row-index="index"><slot /></RowStub></div>',
})

const ColumnStub = defineComponent({
  props: { field: { type: String, default: '' } },
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
  await Promise.resolve()
  await nextTick()
}

function mountView() {
  return mount(DocumentsView, {
    global: {
      stubs: {
        AppPage: ContainerStub,
        AppPageHeader: ContainerStub,
        AppPanel: ContainerStub,
        AppListState: true,
        AppTableSkeleton: true,
        Button: ButtonStub,
        Column: ColumnStub,
        ConfirmDialog: true,
        DataTable: DataTableStub,
        Dialog: ContainerStub,
        InputText: true,
        Select: SelectStub,
        Tag: defineComponent({
          props: { value: { type: String, default: '' } },
          template: '<span class="tag">{{ value }}</span>',
        }),
        Textarea: true,
      },
    },
  })
}

const DOCUMENT = {
  id: 7,
  title: 'Bilan 2025',
  filename: 'bilan.pdf',
  mime_type: 'application/pdf',
  size_bytes: 2048,
  fiscal_year_id: 12,
  fiscal_year_name: '2025',
  tags: ['comptabilité'],
  notes: null,
  uploaded_by: 'david',
  uploaded_at: '2026-08-04T10:30:00',
}

describe('DocumentsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    confirmAccept = null
    authStoreMock.canAccessManagement = true
    mockList.mockResolvedValue({ items: [DOCUMENT], total: 1 })
    mockTags.mockResolvedValue([{ tag: 'comptabilité', count: 1 }])
  })

  it('lists documents with their year, tags and size', async () => {
    const wrapper = mountView()
    await flushView()

    const text = wrapper.text()
    expect(text).toContain('Bilan 2025')
    expect(text).toContain('bilan.pdf')
    expect(text).toContain('2025')
    expect(text).toContain('comptabilité')
    expect(text).toContain('2 Ko')
  })

  it('asks the server for documents without a fiscal year', async () => {
    const wrapper = mountView()
    await flushView()
    mockList.mockClear()

    ;(wrapper.vm as unknown as { fiscalYearFilter: string }).fiscalYearFilter = 'none'
    await (wrapper.vm as unknown as { loadDocuments: () => Promise<void> }).loadDocuments()

    expect(mockList).toHaveBeenCalledWith(
      expect.objectContaining({ without_fiscal_year: true, fiscal_year_id: null }),
    )
  })

  it('passes the search text and the selected tag to the server', async () => {
    const wrapper = mountView()
    await flushView()
    mockList.mockClear()

    const vm = wrapper.vm as unknown as {
      search: string
      tagFilter: string | null
      loadDocuments: () => Promise<void>
    }
    vm.search = 'statuts'
    vm.tagFilter = 'juridique'
    await vm.loadDocuments()

    expect(mockList).toHaveBeenCalledWith(
      expect.objectContaining({ search: 'statuts', tag: 'juridique' }),
    )
  })

  it('reloads the list after a deletion', async () => {
    mockDelete.mockResolvedValue(undefined)
    const wrapper = mountView()
    await flushView()
    mockList.mockClear()

    const vm = wrapper.vm as unknown as { confirmDelete: (doc: typeof DOCUMENT) => void }
    vm.confirmDelete(DOCUMENT)
    expect(confirmAccept).not.toBeNull()
    await confirmAccept?.()

    expect(mockDelete).toHaveBeenCalledWith(7)
    expect(mockList).toHaveBeenCalled()
  })

  it('hides the write actions from a read-only account', async () => {
    authStoreMock.canAccessManagement = false
    const wrapper = mountView()
    await flushView()

    expect(wrapper.find('[data-testid="document-upload-open"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="document-edit"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="document-delete"]').exists()).toBe(false)
    // Reading and downloading stay available.
    expect(wrapper.text()).toContain('Bilan 2025')
  })
})
