/// <reference types="vitest/globals" />

import { mount } from '@vue/test-utils'
import { nextTick, defineComponent } from 'vue'
import ToastService from 'primevue/toastservice'
import i18n from '../../i18n'
import * as accountingApi from '../../api/accounting'
import ImportHistoryView from '../../views/ImportHistoryView.vue'

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}))

const mockListImportHistoryApi = vi.spyOn(accountingApi, 'listImportHistoryApi')
const mockUndoImportRunApi = vi.spyOn(accountingApi, 'undoImportRunApi')
const mockRedoImportRunApi = vi.spyOn(accountingApi, 'redoImportRunApi')
const mockUndoImportOperationApi = vi.spyOn(accountingApi, 'undoImportOperationApi')
const mockRedoImportOperationApi = vi.spyOn(accountingApi, 'redoImportOperationApi')

const ButtonStub = defineComponent({
  props: {
    label: { type: String, default: '' },
    disabled: { type: Boolean, default: false },
    loading: { type: Boolean, default: false },
  },
  emits: ['click'],
  template:
    '<button :data-testid="$attrs[\'data-testid\']" :disabled="disabled || loading" @click="$emit(\'click\')">{{ label }}</button>',
})

const ContainerStub = defineComponent({
  template: '<div><slot /></div>',
})

function buildImportHistoryItem(overrides: Record<string, unknown> = {}) {
  return {
    id: 1,
    kind: 'legacy_log' as const,
    import_type: 'comptabilite' as const,
    status: 'failed',
    file_name: 'Comptabilite 2025.xlsx',
    file_hash: 'a'.repeat(64),
    comparison_start_date: null,
    comparison_end_date: null,
    created_at: '2026-04-20T09:30:00',
    updated_at: '2026-04-20T09:30:00',
    preview: null,
    summary: {
      contacts_created: 0,
      invoices_created: 0,
      payments_created: 0,
      salaries_created: 0,
      entries_created: 4,
      cash_created: 0,
      bank_created: 0,
      skipped: 0,
      ignored_rows: 0,
      blocked_rows: 2,
      warnings: [],
      errors: ['Journal — Compte manquant'],
      warning_details: [],
      error_details: [],
      sheets: [],
      created_objects: [
        {
          sheet_name: 'Journal',
          kind: 'entries',
          object_type: 'accounting_entry',
          object_id: 7,
          reference: 'OD-2025-001',
          details: { description: 'Journal importé' },
        },
      ],
    },
    operations: [],
    can_execute: false,
    can_undo: false,
    can_redo: false,
    ...overrides,
  } satisfies accountingApi.ImportHistoryItem
}

function buildImportOperation(overrides: Record<string, unknown> = {}) {
  return {
    id: 11,
    position: 1,
    operation_type: 'client_invoice_row_import',
    title: '2025-0142',
    description: null,
    source_sheet: 'Factures',
    source_row_numbers: [2],
    decision: 'apply' as const,
    status: 'applied' as const,
    diagnostics: [],
    error_message: null,
    can_undo: true,
    can_redo: false,
    effects: [],
    planned_effects: [],
    source_data: [],
    ...overrides,
  } satisfies accountingApi.ImportOperationRead
}

async function flushView() {
  await Promise.resolve()
  await nextTick()
}

function mountView() {
  return mount(ImportHistoryView, {
    global: {
      plugins: [i18n, ToastService],
      stubs: {
        AppPage: ContainerStub,
        AppPageHeader: ContainerStub,
        AppPanel: ContainerStub,
        Button: ButtonStub,
        Toast: true,
      },
    },
  })
}

describe('ImportHistoryView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUndoImportRunApi.mockReset()
    mockRedoImportRunApi.mockReset()
    mockUndoImportOperationApi.mockReset()
    mockRedoImportOperationApi.mockReset()
  })

  it('loads and displays import history with diagnostics and created objects', async () => {
    mockListImportHistoryApi.mockResolvedValueOnce([buildImportHistoryItem()])

    const wrapper = mountView()
    await flushView()
    await flushView()

    expect(mockListImportHistoryApi).toHaveBeenCalledTimes(1)
    expect(wrapper.get('[data-testid="import-history"]').text()).toContain('Comptabilite 2025.xlsx')
    expect(wrapper.get('[data-testid="import-history"]').text()).toContain('Compte manquant')
    expect(wrapper.get('[data-testid="import-history"]').text()).toContain('OD-2025-001')
  })

  it('shows an empty state when no import history exists', async () => {
    mockListImportHistoryApi.mockResolvedValueOnce([])

    const wrapper = mountView()
    await flushView()
    await flushView()

    expect(wrapper.get('[data-testid="import-history"]').text()).toContain(
      'Aucun historique d’import n’est encore disponible.',
    )
  })

  it('normalizes legacy success status to the translated completed label', async () => {
    mockListImportHistoryApi.mockResolvedValueOnce([
      buildImportHistoryItem({
        status: 'success',
      }),
    ])

    const wrapper = mountView()
    await flushView()
    await flushView()

    expect(wrapper.get('[data-testid="import-history"]').text()).toContain('Terminé')
    expect(wrapper.get('[data-testid="import-history"]').text()).not.toContain('success')
  })

  it('truncates long diagnostics by default and expands them on demand', async () => {
    mockListImportHistoryApi.mockResolvedValueOnce([
      buildImportHistoryItem({
        summary: {
          contacts_created: 0,
          invoices_created: 0,
          payments_created: 0,
          salaries_created: 0,
          entries_created: 4,
          cash_created: 0,
          bank_created: 0,
          skipped: 0,
          ignored_rows: 0,
          blocked_rows: 12,
          warnings: [],
          errors: Array.from({ length: 12 }, (_, index) => `Erreur ${index + 1}`),
          warning_details: [],
          error_details: [],
          sheets: [],
          created_objects: [],
        },
      }),
    ])

    const wrapper = mountView()
    await flushView()
    await flushView()

    expect(wrapper.get('[data-testid="import-history"]').text()).toContain('Erreur 8')
    expect(wrapper.get('[data-testid="import-history"]').text()).not.toContain('Erreur 9')
    expect(wrapper.get('[data-testid="history-errors-toggle-1"]').text()).toContain('Afficher 8/12')

    await wrapper.get('[data-testid="history-errors-toggle-1"]').trigger('click')
    await nextTick()

    expect(wrapper.get('[data-testid="import-history"]').text()).toContain('Erreur 12')
    expect(wrapper.get('[data-testid="history-errors-toggle-1"]').text()).toContain('Réduire')
  })

  it('shows failed operation errors and allows per-operation undo from history', async () => {
    mockListImportHistoryApi.mockResolvedValueOnce([
      buildImportHistoryItem({
        id: 7,
        kind: 'run',
        import_type: 'gestion',
        status: 'failed',
        can_undo: true,
        summary: {
          contacts_created: 0,
          invoices_created: 1,
          payments_created: 0,
          salaries_created: 0,
          entries_created: 0,
          cash_created: 0,
          bank_created: 0,
          skipped: 0,
          ignored_rows: 0,
          blocked_rows: 0,
          warnings: [],
          errors: ['Banque ligne 267 — forced payment generation failure'],
          warning_details: [],
          error_details: [],
          sheets: [],
          created_objects: [],
        },
        operations: [
          buildImportOperation({
            id: 41,
            title: '2025-0142',
            can_undo: true,
          }),
          buildImportOperation({
            id: 42,
            title: 'Banque ligne 267',
            status: 'failed',
            error_message: 'forced payment generation failure',
            can_undo: false,
            diagnostics: ['Paiement client détecté'],
          }),
        ],
      }),
    ])
    mockUndoImportOperationApi.mockResolvedValueOnce({} as accountingApi.ImportRunRead)
    mockListImportHistoryApi.mockResolvedValueOnce([
      buildImportHistoryItem({
        id: 7,
        kind: 'run',
        import_type: 'gestion',
        status: 'partially_reverted',
        can_undo: false,
        can_redo: true,
        operations: [
          buildImportOperation({
            id: 41,
            title: '2025-0142',
            status: 'undone',
            can_undo: false,
            can_redo: true,
          }),
          buildImportOperation({
            id: 42,
            title: 'Banque ligne 267',
            status: 'failed',
            error_message: 'forced payment generation failure',
            can_undo: false,
          }),
        ],
      }),
    ])

    const wrapper = mountView()
    await flushView()
    await flushView()

    expect(wrapper.get('[data-testid="import-history"]').text()).toContain(
      'forced payment generation failure',
    )
    await wrapper.get('[data-testid="history-operation-undo-41"]').trigger('click')
    await flushView()
    await flushView()

    expect(mockUndoImportOperationApi).toHaveBeenCalledWith(41)
    expect(wrapper.get('[data-testid="import-history"]').text()).toContain('Partiellement annulé')
  })

  it('reloads history after a timeout while undoing a run', async () => {
    mockListImportHistoryApi.mockResolvedValueOnce([
      buildImportHistoryItem({
        id: 9,
        kind: 'run',
        import_type: 'gestion',
        status: 'failed',
        can_undo: true,
      }),
    ])
    mockUndoImportRunApi.mockRejectedValueOnce({ code: 'ECONNABORTED' })
    mockListImportHistoryApi.mockResolvedValueOnce([
      buildImportHistoryItem({
        id: 9,
        kind: 'run',
        import_type: 'gestion',
        status: 'reverted',
        can_undo: false,
        can_redo: true,
      }),
    ])

    const wrapper = mountView()
    await flushView()
    await flushView()

    await wrapper.findAll('button').find((button) => button.text() === 'Annuler ce run')?.trigger('click')
    await flushView()
    await flushView()

    expect(mockUndoImportRunApi).toHaveBeenCalledWith(9)
    expect(mockListImportHistoryApi).toHaveBeenCalledTimes(2)
    expect(wrapper.get('[data-testid="import-history"]').text()).toContain('Annulé')
  })
})
