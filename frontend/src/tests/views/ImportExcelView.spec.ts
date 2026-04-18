/// <reference types="vitest/globals" />

import { mount } from '@vue/test-utils'
import { nextTick, defineComponent } from 'vue'
import ToastService from 'primevue/toastservice'
import i18n from '../../i18n'
import * as accountingApi from '../../api/accounting'
import * as settingsApi from '../../api/settings'
import ImportExcelView from '../../views/ImportExcelView.vue'

const mockImportGestionFileApi = vi.spyOn(accountingApi, 'importGestionFileApi')
const mockImportTestShortcutApi = vi.spyOn(accountingApi, 'importTestShortcutApi')
const mockListTestImportShortcutsApi = vi.spyOn(accountingApi, 'listTestImportShortcutsApi')
const mockPreviewGestionFileApi = vi.spyOn(accountingApi, 'previewGestionFileApi')
const mockPreviewComptabiliteFileApi = vi.spyOn(accountingApi, 'previewComptabiliteFileApi')
const mockGetSettingsApi = vi.spyOn(settingsApi, 'getSettingsApi')

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
  }
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
    ...overrides,
  }
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
  })

  it('keeps import disabled until preview succeeds', async () => {
    mockPreviewGestionFileApi.mockResolvedValueOnce(buildPreviewResult())

    const wrapper = mountView()
    await selectFile(wrapper, 'Gestion 2025.xlsx')

    expect(
      (wrapper.get('[data-testid="primary-import-button"]').element as HTMLButtonElement).disabled,
    ).toBe(true)

    await wrapper.get('[data-testid="preview-button"]').trigger('click')
    await flushView()

    expect(mockPreviewGestionFileApi).toHaveBeenCalledTimes(1)
    expect(mockPreviewGestionFileApi).toHaveBeenCalledWith(expect.any(File), {
      comparison_start_date: '2025-08-01',
      comparison_end_date: '2026-07-31',
    })
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
    mockPreviewGestionFileApi.mockResolvedValueOnce(
      buildPreviewResult({
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
    )

    const wrapper = mountView()
    await selectFile(wrapper)
    await wrapper.get('[data-testid="preview-button"]').trigger('click')
    await flushView()

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
    mockPreviewGestionFileApi.mockResolvedValueOnce(
      buildPreviewResult({
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
    )

    const wrapper = mountView()
    await selectFile(wrapper)
    await wrapper.get('[data-testid="preview-button"]').trigger('click')
    await flushView()

    expect(wrapper.text()).toContain('3 en trop dans Solde')
    expect(wrapper.text()).toContain('2025-0199 · 2025-08-02')
    expect(wrapper.text()).toContain('Numéro: 2025-0199')
    expect(wrapper.text()).toContain('Comparaison de convergence')
    expect(wrapper.text()).toContain("Diagnostic d'import")
  })

  it('hides the convergence comparison for a file that has never been imported', async () => {
    mockPreviewGestionFileApi.mockResolvedValueOnce(
      buildPreviewResult({
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
    )

    const wrapper = mountView()
    await selectFile(wrapper)
    await wrapper.get('[data-testid="preview-button"]').trigger('click')
    await flushView()

    expect(wrapper.text()).not.toContain('Comparaison de convergence')
    expect(wrapper.text()).not.toContain('3 en trop dans Solde')
    expect(wrapper.text()).toContain("Diagnostic d'import")
    expect(wrapper.text()).toContain('Factures — Ligne 4 : warning')
  })

  it('shows the global convergence title for comptabilite comparisons', async () => {
    mockPreviewComptabiliteFileApi.mockResolvedValueOnce(
      buildPreviewResult({
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
    )

    const wrapper = mountView()
    await wrapper.get('#type-compta').trigger('change')
    await nextTick()
    await selectFile(wrapper, 'Comptabilite 2025.xlsx')
    await wrapper.get('[data-testid="preview-button"]').trigger('click')
    await flushView()

    expect(wrapper.text()).toContain('Convergence globale Excel et Solde')
  })

  it('clears a previous preview when the import type changes', async () => {
    mockPreviewGestionFileApi.mockResolvedValueOnce(buildPreviewResult())

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
    mockPreviewGestionFileApi.mockResolvedValueOnce(buildPreviewResult())
    mockImportGestionFileApi.mockResolvedValueOnce(buildImportResult())

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
})
