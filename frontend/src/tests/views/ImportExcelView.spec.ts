/// <reference types="vitest/globals" />

import { mount } from '@vue/test-utils'
import { nextTick, defineComponent } from 'vue'
import ToastService from 'primevue/toastservice'
import i18n from '../../i18n'
import * as accountingApi from '../../api/accounting'
import * as settingsApi from '../../api/settings'
import ImportExcelView from '../../views/ImportExcelView.vue'

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}))

const mockExecuteImportRunApi = vi.spyOn(accountingApi, 'executeImportRunApi')
const mockImportTestShortcutApi = vi.spyOn(accountingApi, 'importTestShortcutApi')
const mockListTestImportShortcutsApi = vi.spyOn(accountingApi, 'listTestImportShortcutsApi')
const mockPrepareGestionRunApi = vi.spyOn(accountingApi, 'prepareGestionRunApi')
const mockPrepareComptabiliteRunApi = vi.spyOn(accountingApi, 'prepareComptabiliteRunApi')
const mockGetSettingsApi = vi.spyOn(settingsApi, 'getSettingsApi')
const scrollIntoViewMock = vi.fn()

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

const CheckboxStub = defineComponent({
  props: {
    modelValue: { type: Boolean, default: false },
  },
  emits: ['update:modelValue'],
  template:
    '<input type="checkbox" :data-testid="$attrs[\'data-testid\']" :checked="modelValue" @change="$emit(\'update:modelValue\', $event.target.checked)" />',
})

const RadioButtonStub = defineComponent({
  props: {
    modelValue: { type: String, default: '' },
    value: { type: String, required: true },
    inputId: { type: String, default: undefined },
  },
  emits: ['update:modelValue'],
  template:
    '<input :id="inputId" type="radio" :checked="modelValue === value" @change="$emit(\'update:modelValue\', value)" />',
})

const ContainerStub = defineComponent({
  template: '<div><slot /></div>',
})

function buildPreviewResult(overrides: Record<string, unknown> = {}) {
  return {
    sheets: [],
    estimated_contacts: 1,
    estimated_invoices: 2,
    estimated_payments: 3,
    estimated_salaries: 0,
    estimated_entries: 0,
    errors: [],
    warnings: [],
    error_details: [],
    warning_details: [],
    can_import: true,
    sample_rows: [],
    ...overrides,
  } satisfies accountingApi.PreviewResult
}

function buildImportResult(overrides: Record<string, unknown> = {}) {
  return {
    contacts_created: 1,
    invoices_created: 2,
    payments_created: 3,
    salaries_created: 0,
    entries_created: 4,
    cash_created: 0,
    bank_created: 1,
    skipped: 0,
    ignored_rows: 2,
    blocked_rows: 1,
    warnings: [],
    errors: [],
    error_details: [],
    warning_details: [],
    sheets: [],
    created_objects: [],
    ...overrides,
  } satisfies accountingApi.ImportResult
}

function buildImportRun(overrides: Record<string, unknown> = {}) {
  return {
    id: 1,
    kind: 'run' as const,
    import_type: 'gestion' as const,
    status: 'prepared' as const,
    file_name: 'Gestion 2025.xlsx',
    file_hash: 'd'.repeat(64),
    comparison_start_date: '2025-08-01',
    comparison_end_date: '2026-07-31',
    created_at: '2026-04-20T09:30:00',
    updated_at: '2026-04-20T09:30:00',
    preview: buildPreviewResult(),
    summary: null,
    operations: [],
    can_execute: true,
    can_undo: false,
    can_redo: false,
    ...overrides,
  } satisfies accountingApi.ImportRunRead
}

async function flushView() {
  await Promise.resolve()
  await nextTick()
}

function mountView() {
  return mount(ImportExcelView, {
    global: {
      plugins: [i18n, ToastService],
      stubs: {
        AppPage: ContainerStub,
        AppPageHeader: ContainerStub,
        AppPanel: ContainerStub,
        Button: ButtonStub,
        Checkbox: CheckboxStub,
        RadioButton: RadioButtonStub,
        Toast: true,
      },
    },
  })
}

async function selectFile(wrapper: ReturnType<typeof mountView>, name = 'historique.xlsx') {
  const input = wrapper.get('input[type="file"]')
  const file = new File(['excel'], name, {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  })
  Object.defineProperty(input.element, 'files', {
    value: [file],
    configurable: true,
  })
  await input.trigger('change')
  return file
}

describe('ImportExcelView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    scrollIntoViewMock.mockReset()
    mockListTestImportShortcutsApi.mockResolvedValue([])
    mockGetSettingsApi.mockResolvedValue({
      association_name: 'Solde',
      association_address: '',
      association_siret: '',
      association_logo_path: '',
      fiscal_year_start_month: 8,
      smtp_host: null,
      smtp_port: 587,
      smtp_user: null,
      smtp_from_email: null,
      smtp_use_tls: true,
    })
    Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', {
      value: scrollIntoViewMock,
      configurable: true,
      writable: true,
    })
  })

  it('keeps import disabled until preview succeeds', async () => {
    mockPrepareGestionRunApi.mockResolvedValueOnce(buildImportRun())

    const wrapper = mountView()
    await selectFile(wrapper, 'Gestion 2025.xlsx')

    expect(
      (wrapper.get('[data-testid="primary-import-button"]').element as HTMLButtonElement).disabled,
    ).toBe(true)

    await wrapper.get('[data-testid="preview-button"]').trigger('click')
    await flushView()

    expect(mockPrepareGestionRunApi).toHaveBeenCalledTimes(1)
    expect(mockPrepareGestionRunApi).toHaveBeenCalledWith(expect.any(File), {
      comparison_start_date: '2025-08-01',
      comparison_end_date: '2026-07-31',
    })
    expect(scrollIntoViewMock).toHaveBeenCalled()
    expect(
      (wrapper.get('[data-testid="primary-import-button"]').element as HTMLButtonElement).disabled,
    ).toBe(false)
    expect(
      (wrapper.get('[data-testid="confirm-import-button"]').element as HTMLButtonElement).disabled,
    ).toBe(false)
  })

  it('hides the preview state until a preview exists', async () => {
    const wrapper = mountView()

    expect(wrapper.find('.import-preview-state').exists()).toBe(false)

    await selectFile(wrapper)

    expect(wrapper.find('.import-preview-state').exists()).toBe(false)
  })

  it('prefills the comparison window from the fiscal year settings and file name', async () => {
    const wrapper = mountView()

    await selectFile(wrapper, 'Gestion 2025.xlsx')

    expect(
      (wrapper.get('[data-testid="comparison-start-date"]').element as HTMLInputElement).value,
    ).toBe('2025-08-01')
    expect(
      (wrapper.get('[data-testid="comparison-end-date"]').element as HTMLInputElement).value,
    ).toBe('2026-07-31')
  })

  it('requires explicit warning acknowledgment before import', async () => {
    mockPrepareGestionRunApi.mockResolvedValueOnce(
      buildImportRun({
        preview: buildPreviewResult({
          warnings: ['warning'],
          warning_details: [
            {
              severity: 'warning',
              sheet_name: 'Factures',
              kind: 'invoices',
              row_number: 4,
              message: 'warning',
              display_message: 'Factures — Ligne 4 : warning',
            },
          ],
        }),
      }),
    )

    const wrapper = mountView()
    await selectFile(wrapper)
    await wrapper.get('[data-testid="preview-button"]').trigger('click')
    await flushView()

    await wrapper.get('[data-testid="preview-tab-warnings"]').trigger('click')
    await nextTick()

    expect(wrapper.text()).toContain('Factures — Ligne 4 : warning')

    expect(
      (wrapper.get('[data-testid="primary-import-button"]').element as HTMLButtonElement).disabled,
    ).toBe(true)
    expect(
      (wrapper.get('[data-testid="confirm-import-button"]').element as HTMLButtonElement).disabled,
    ).toBe(true)

    await wrapper.get('[data-testid="warning-ack-checkbox"]').setValue(true)
    await nextTick()

    expect(
      (wrapper.get('[data-testid="primary-import-button"]').element as HTMLButtonElement).disabled,
    ).toBe(false)
    expect(
      (wrapper.get('[data-testid="confirm-import-button"]').element as HTMLButtonElement).disabled,
    ).toBe(false)
  })

  it('shows extra rows already present only in Solde inside the comparison summary', async () => {
    mockPrepareGestionRunApi.mockResolvedValueOnce(
      buildImportRun({
        preview: buildPreviewResult({
          errors: ['Fichier deja importe (gestion) le 2026-04-18 18:52:06'],
          error_details: [
            {
              category: 'already-imported',
              severity: 'error',
              sheet_name: null,
              kind: null,
              row_number: null,
              message: 'Fichier deja importe (gestion) le 2026-04-18 18:52:06',
              display_message: 'Fichier deja importe (gestion) le 2026-04-18 18:52:06',
            },
          ],
          warnings: ['warning'],
          warning_details: [
            {
              severity: 'warning',
              sheet_name: 'Factures',
              kind: 'invoices',
              row_number: 4,
              message: 'warning',
              display_message: 'Factures — Ligne 4 : warning',
            },
          ],
          comparison: {
            mode: 'gestion-excel-to-solde',
            direction: 'excel-to-solde',
            domains: [
              {
                kind: 'invoices',
                file_rows: 2,
                already_in_solde: 1,
                missing_in_solde: 1,
                extra_in_solde: 3,
                extra_in_solde_details: [
                  {
                    summary: '2025-0199 · 2025-08-02',
                    number: '2025-0199',
                    date: '2025-08-02',
                  },
                ],
                ignored_by_policy: 0,
                blocked: 0,
              },
            ],
            totals: {
              file_rows: 2,
              already_in_solde: 1,
              missing_in_solde: 1,
              extra_in_solde: 3,
              ignored_by_policy: 0,
              blocked: 0,
            },
          },
        }),
      }),
    )

    const wrapper = mountView()
    await selectFile(wrapper)
    await wrapper.get('[data-testid="preview-button"]').trigger('click')
    await flushView()

    await wrapper.get('[data-testid="preview-tab-full-summary"]').trigger('click')
    await nextTick()

    expect(wrapper.text()).toContain('3 en trop dans Solde')
    expect(wrapper.text()).toContain('2025-0199 · 2025-08-02')
    expect(wrapper.text()).toContain('Numéro: 2025-0199')
    expect(wrapper.text()).toContain('Comparaison de convergence')
  })

  it('hides the convergence comparison for a file that has never been imported', async () => {
    mockPrepareGestionRunApi.mockResolvedValueOnce(
      buildImportRun({
        preview: buildPreviewResult({
          comparison: {
            mode: 'gestion-excel-to-solde',
            direction: 'excel-to-solde',
            domains: [
              {
                kind: 'invoices',
                file_rows: 2,
                already_in_solde: 1,
                missing_in_solde: 1,
                extra_in_solde: 3,
                ignored_by_policy: 0,
                blocked: 0,
              },
            ],
            totals: {
              file_rows: 2,
              already_in_solde: 1,
              missing_in_solde: 1,
              extra_in_solde: 3,
              ignored_by_policy: 0,
              blocked: 0,
            },
          },
          warnings: ['warning'],
          warning_details: [
            {
              severity: 'warning',
              sheet_name: 'Factures',
              kind: 'invoices',
              row_number: 4,
              message: 'warning',
              display_message: 'Factures — Ligne 4 : warning',
            },
          ],
        }),
      }),
    )

    const wrapper = mountView()
    await selectFile(wrapper)
    await wrapper.get('[data-testid="preview-button"]').trigger('click')
    await flushView()

    await wrapper.get('[data-testid="preview-tab-full-summary"]').trigger('click')
    await nextTick()

    expect(wrapper.text()).not.toContain('Comparaison de convergence')
    expect(wrapper.text()).not.toContain('3 en trop dans Solde')

    await wrapper.get('[data-testid="preview-tab-warnings"]').trigger('click')
    await nextTick()

    expect(wrapper.text()).toContain('Factures — Ligne 4 : warning')
  })

  it('shows the global convergence title for comptabilite comparisons', async () => {
    mockPrepareComptabiliteRunApi.mockResolvedValueOnce(
      buildImportRun({
        import_type: 'comptabilite',
        file_name: 'Comptabilite 2025.xlsx',
        preview: buildPreviewResult({
          errors: ['Fichier deja importe (comptabilite) le 2026-04-18 18:52:06'],
          error_details: [
            {
              category: 'already-imported',
              severity: 'error',
              sheet_name: null,
              kind: null,
              row_number: null,
              message: 'Fichier deja importe (comptabilite) le 2026-04-18 18:52:06',
              display_message: 'Fichier deja importe (comptabilite) le 2026-04-18 18:52:06',
            },
          ],
          comparison: {
            mode: 'global-convergence',
            direction: 'bidirectional',
            domains: [
              {
                kind: 'entries',
                file_rows: 2,
                already_in_solde: 1,
                missing_in_solde: 1,
                extra_in_solde: 1,
                ignored_by_policy: 0,
                blocked: 0,
              },
            ],
            totals: {
              file_rows: 2,
              already_in_solde: 1,
              missing_in_solde: 1,
              extra_in_solde: 1,
              ignored_by_policy: 0,
              blocked: 0,
            },
          },
        }),
      }),
    )

    const wrapper = mountView()
    await wrapper.get('#type-compta').trigger('change')
    await nextTick()
    await selectFile(wrapper, 'Comptabilite 2025.xlsx')
    await wrapper.get('[data-testid="preview-button"]').trigger('click')
    await flushView()

    await wrapper.get('[data-testid="preview-tab-full-summary"]').trigger('click')
    await nextTick()

    expect(wrapper.text()).toContain('Convergence globale Excel et Solde')
  })

  it('clears a previous preview when the import type changes', async () => {
    mockPrepareGestionRunApi.mockResolvedValueOnce(buildImportRun())

    const wrapper = mountView()
    await selectFile(wrapper)
    await wrapper.get('[data-testid="preview-button"]').trigger('click')
    await flushView()

    expect(
      (wrapper.get('[data-testid="primary-import-button"]').element as HTMLButtonElement).disabled,
    ).toBe(false)

    await wrapper.get('#type-compta').trigger('change')
    await nextTick()

    expect(
      (wrapper.get('[data-testid="primary-import-button"]').element as HTMLButtonElement).disabled,
    ).toBe(true)
    expect(wrapper.find('[data-testid="confirm-import-button"]').exists()).toBe(false)
  })

  it('shows a persistent result banner after import completes', async () => {
    mockPrepareGestionRunApi.mockResolvedValueOnce(buildImportRun())
    mockExecuteImportRunApi.mockResolvedValueOnce(
      buildImportRun({
        status: 'completed',
        can_execute: false,
        can_undo: true,
        summary: buildImportResult(),
      }),
    )

    const wrapper = mountView()
    await selectFile(wrapper)
    await wrapper.get('[data-testid="preview-button"]').trigger('click')
    await flushView()
    await wrapper.get('[data-testid="primary-import-button"]').trigger('click')
    await flushView()

    expect(wrapper.get('[data-testid="import-result-banner"]').text()).toContain(
      'Import terminé avec succès',
    )
    expect(wrapper.get('[data-testid="import-result-banner"]').text()).toContain(
      'Le détail complet reste affiché ci-dessous.',
    )
  })

  it('does not show an import result banner after preview only', async () => {
    mockPrepareGestionRunApi.mockResolvedValueOnce(
      buildImportRun({
        status: 'blocked',
        can_execute: false,
        summary: buildImportResult({
          blocked_rows: 2,
          ignored_rows: 1,
        }),
      }),
    )

    const wrapper = mountView()
    await selectFile(wrapper, 'Gestion 2025.xlsx')
    await wrapper.get('[data-testid="preview-button"]').trigger('click')
    await flushView()

    expect(wrapper.find('[data-testid="import-result-banner"]').exists()).toBe(false)
  })

  it('renders a compact grouped operations table with filtering and expandable details', async () => {
    mockPrepareGestionRunApi.mockResolvedValueOnce(
      buildImportRun({
        operations: [
          {
            id: 101,
            position: 1,
            operation_type: 'client_invoice_row_import',
            title: '2024-0056',
            description: 'Facture Alice Martin',
            source_sheet: 'Factures',
            source_row_numbers: [12],
            decision: 'apply',
            status: 'prepared',
            diagnostics: ['Facture prête à être créée'],
            error_message: null,
            can_undo: false,
            can_redo: false,
            effects: [
              {
                id: 1,
                entity_type: 'invoice',
                action: 'create',
                entity_id: null,
                entity_reference: '2024-0056',
                details: {},
                status: 'applied',
              },
              {
                id: 3,
                entity_type: 'accounting_entry',
                action: 'create',
                entity_id: null,
                entity_reference: 'VEN-2024-0056',
                details: {},
                status: 'applied',
              },
            ],
          },
          {
            id: 102,
            position: 2,
            operation_type: 'client_payment_row_import',
            title: '2024-0056',
            description: 'Paiement associé à la facture',
            source_sheet: 'Paiements',
            source_row_numbers: [18, 19],
            decision: 'apply',
            status: 'prepared',
            diagnostics: [],
            error_message: null,
            can_undo: false,
            can_redo: false,
            effects: [
              {
                id: 2,
                entity_type: 'payment',
                action: 'create',
                entity_id: null,
                entity_reference: 'PAY-2024-0056',
                details: {},
                status: 'applied',
              },
            ],
          },
        ],
      }),
    )

    const wrapper = mountView()
    await selectFile(wrapper, 'Gestion 2025.xlsx')
    await wrapper.get('[data-testid="preview-button"]').trigger('click')
    await flushView()

    expect(wrapper.get('[data-testid="preview-quick-summary"]').text()).toContain(
      'Opérations préparées',
    )

    expect(wrapper.get('[data-testid="operations-table"]').text()).toContain('Factures')
    expect(wrapper.get('[data-testid="operations-table"]').text()).toContain('Paiements')
    expect(wrapper.get('[data-testid="operations-table"]').text()).toContain(
      'Créer facture 2024-0056',
    )
    expect(wrapper.text()).not.toContain('Facture Alice Martin')

    await wrapper.get('[data-testid="operations-search"]').setValue('paiement')
    await nextTick()

    expect(wrapper.get('[data-testid="operations-table"]').text()).toContain(
      'Créer paiement 2024-0056',
    )
    expect(wrapper.get('[data-testid="operations-table"]').text()).not.toContain(
      'Créer facture 2024-0056',
    )

    await wrapper.get('[data-testid="operations-search"]').setValue('')
    await nextTick()
    await wrapper.get('[data-testid="toggle-operation-101"]').trigger('click')
    await nextTick()

    expect(wrapper.get('[data-testid="operation-detail-101"]').text()).toContain(
      'Facture Alice Martin',
    )
    expect(wrapper.get('[data-testid="operation-detail-101"]').text()).toContain(
      'Créer facture 2024-0056',
    )
    expect(wrapper.get('[data-testid="operation-detail-101"]').text()).toContain(
      'Opérations générées (gestion)',
    )
    expect(wrapper.get('[data-testid="operation-detail-101"]').text()).toContain(
      'Écritures générées (compta)',
    )
    expect(wrapper.get('[data-testid="operation-detail-101"]').text()).toContain('Création facture')
    expect(wrapper.get('[data-testid="operation-detail-101"]').text()).toContain(
      'Création écriture comptable',
    )
  })

  it('renders planned effects when the operation has not been executed yet', async () => {
    mockPrepareGestionRunApi.mockResolvedValueOnce(
      buildImportRun({
        operations: [
          {
            id: 301,
            position: 1,
            operation_type: 'client_invoice_row_import',
            title: '2025-0142',
            description: 'Facture Christine LOPES',
            source_sheet: 'Factures',
            source_row_numbers: [4],
            decision: 'apply',
            status: 'prepared',
            diagnostics: [],
            error_message: null,
            can_undo: false,
            can_redo: false,
            effects: [],
            planned_effects: [
              {
                id: null,
                entity_type: 'invoice',
                action: 'create',
                entity_id: null,
                entity_reference: '2025-0142',
                details: {
                  amount: '55',
                  date: '2025-08-01',
                },
                status: 'planned',
              },
              {
                id: null,
                entity_type: 'accounting_entry',
                action: 'create',
                entity_id: null,
                entity_reference: '000123',
                details: {
                  account_number: '411100',
                  debit: '55',
                  credit: '0',
                  label: 'Fact. 2025-0142 1',
                },
                status: 'planned',
              },
            ],
          },
        ],
      }),
    )

    const wrapper = mountView()
    await selectFile(wrapper, 'Gestion 2025.xlsx')
    await wrapper.get('[data-testid="preview-button"]').trigger('click')
    await flushView()
    await wrapper.get('[data-testid="toggle-operation-301"]').trigger('click')
    await nextTick()

    expect(wrapper.get('[data-testid="operation-detail-301"]').text()).toContain('Création facture')
    expect(wrapper.get('[data-testid="operation-detail-301"]').text()).toContain('55')
    expect(wrapper.get('[data-testid="operation-detail-301"]').text()).toContain('411100')
    expect(wrapper.get('[data-testid="operation-detail-301"]').text()).toContain(
      'Fact. 2025-0142 1',
    )
  })

  it('guides the user to blocked operations when the preview is not executable', async () => {
    mockPrepareGestionRunApi.mockResolvedValueOnce(
      buildImportRun({
        can_execute: false,
        preview: buildPreviewResult({
          can_import: false,
          errors: ['Compte comptable introuvable'],
          error_details: [
            {
              severity: 'error',
              sheet_name: 'Journal',
              kind: 'entries',
              row_number: 14,
              message: 'Compte comptable introuvable',
              display_message: 'Journal — Ligne 14 : compte comptable introuvable',
            },
          ],
        }),
        operations: [
          {
            id: 201,
            position: 1,
            operation_type: 'blocked_by_validation',
            title: 'Ligne 14',
            description: 'Compte 706200 absent du plan comptable',
            source_sheet: 'Journal',
            source_row_numbers: [14],
            decision: 'block',
            status: 'blocked',
            diagnostics: ['Créer ou mapper le compte 706200 avant import'],
            error_message: 'Compte comptable introuvable',
            can_undo: false,
            can_redo: false,
            effects: [],
            source_data: [
              {
                source_row_number: 14,
                entry_date: '2025-09-15',
                account_number: '706200',
                label: 'Cours septembre',
                debit: '0',
                credit: '85',
              },
            ],
          },
        ],
      }),
    )

    const wrapper = mountView()
    await selectFile(wrapper, 'Comptabilite 2025.xlsx')
    await wrapper.get('[data-testid="preview-button"]').trigger('click')
    await flushView()

    expect(wrapper.get('[data-testid="preview-blocked-guidance"]').text()).toContain(
      'Des opérations bloquent encore l’import',
    )

    await wrapper.get('[data-testid="show-blocked-operations"]').trigger('click')
    await nextTick()

    expect(wrapper.get('[data-testid="preview-details-tab"]').text()).toContain('Ligne 14')
    expect(
      (wrapper.get('[data-testid="operations-status-filter"]').element as HTMLSelectElement).value,
    ).toBe('blocked')
    expect(wrapper.get('[data-testid="operation-detail-201"]').text()).toContain(
      'Données source Excel',
    )
    expect(wrapper.get('[data-testid="operation-detail-201"]').text()).toContain('706200')
    expect(wrapper.get('[data-testid="operation-detail-201"]').text()).toContain('Cours septembre')
  })

  it('renders source data for ignored operations too', async () => {
    mockPrepareGestionRunApi.mockResolvedValueOnce(
      buildImportRun({
        operations: [
          {
            id: 202,
            position: 1,
            operation_type: 'ignored_by_policy',
            title: '2025-0142',
            description: 'Facture déjà présente dans Solde.',
            source_sheet: 'Factures',
            source_row_numbers: [4],
            decision: 'ignore',
            status: 'ignored',
            diagnostics: ['Factures — Ligne 4 : facture déjà existante'],
            error_message: null,
            can_undo: false,
            can_redo: false,
            effects: [],
            source_data: [
              {
                source_row_number: 4,
                invoice_date: '2025-08-01',
                invoice_number: '2025-0142',
                contact_name: 'Christine LOPES',
                amount: '55',
              },
            ],
          },
        ],
      }),
    )

    const wrapper = mountView()
    await selectFile(wrapper, 'Gestion 2025.xlsx')
    await wrapper.get('[data-testid="preview-button"]').trigger('click')
    await flushView()
    await wrapper.get('[data-testid="toggle-operation-202"]').trigger('click')
    await nextTick()

    expect(wrapper.get('[data-testid="operation-detail-202"]').text()).toContain(
      'Données source Excel',
    )
    expect(wrapper.get('[data-testid="operation-detail-202"]').text()).toContain('2025-0142')
    expect(wrapper.get('[data-testid="operation-detail-202"]').text()).toContain('Christine LOPES')
  })

  it('runs a temporary shortcut import without preview', async () => {
    mockListTestImportShortcutsApi.mockResolvedValueOnce([
      {
        alias: 'gestion-2024',
        label: 'Gestion 2024',
        import_type: 'gestion',
        order: 1,
        available: true,
        file_name: 'Gestion 2024.xlsx',
        message: null,
      },
    ])
    mockImportTestShortcutApi.mockResolvedValueOnce(buildImportResult())

    const wrapper = mountView()
    await flushView()
    await flushView()

    await wrapper.get('[data-testid="quick-import-gestion-2024"]').trigger('click')
    await flushView()

    expect(mockImportTestShortcutApi).toHaveBeenCalledWith('gestion-2024')
    expect(wrapper.get('[data-testid="import-result-banner"]').text()).toContain(
      'Import terminé avec succès',
    )
  })

  it('defaults to the details tab and keeps alerts in dedicated tabs', async () => {
    mockPrepareGestionRunApi.mockResolvedValueOnce(
      buildImportRun({
        preview: buildPreviewResult({
          warnings: ['warning'],
          warning_details: [
            {
              severity: 'warning',
              sheet_name: 'Factures',
              kind: 'invoices',
              row_number: 4,
              message: 'warning',
              display_message: 'Factures — Ligne 4 : warning',
            },
          ],
        }),
        operations: [
          {
            id: 501,
            position: 1,
            operation_type: 'client_invoice_row_import',
            title: '2025-0101',
            description: 'Facture test',
            source_sheet: 'Factures',
            source_row_numbers: [4],
            decision: 'apply',
            status: 'prepared',
            diagnostics: [],
            error_message: null,
            can_undo: false,
            can_redo: false,
            effects: [],
          },
        ],
      }),
    )

    const wrapper = mountView()
    await selectFile(wrapper, 'Gestion 2025.xlsx')
    await wrapper.get('[data-testid="preview-button"]').trigger('click')
    await flushView()

    expect(wrapper.find('[data-testid="preview-details-tab"]').exists()).toBe(true)
    expect(wrapper.get('[data-testid="operations-table"]').text()).toContain('2025-0101')
    expect(wrapper.find('[data-testid="preview-warnings-tab"]').exists()).toBe(false)

    await wrapper.get('[data-testid="preview-tab-warnings"]').trigger('click')
    await nextTick()

    expect(wrapper.get('[data-testid="preview-warnings-tab"]').text()).toContain(
      'Factures — Ligne 4 : warning',
    )
  })
})
