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
})
