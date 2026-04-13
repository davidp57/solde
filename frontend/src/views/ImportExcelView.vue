<template>
  <AppPage>
    <AppPageHeader
      :eyebrow="t('ui.page.collection_eyebrow')"
      :title="t('import.title')"
      :subtitle="t('import.subtitle')"
    />

    <AppPanel :title="t('import.type_label')" :subtitle="t('import.preview_subtitle')">
      <div class="import-form">
          <!-- File type selection -->
          <div class="app-field">
            <label class="app-field__label">{{ t('import.type_label') }}</label>
            <div class="import-type-row">
              <div class="import-radio-item">
                <RadioButton v-model="importType" input-id="type-gestion" value="gestion" />
                <label for="type-gestion">{{ t('import.type_gestion') }}</label>
              </div>
              <div class="import-radio-item">
                <RadioButton v-model="importType" input-id="type-compta" value="comptabilite" />
                <label for="type-compta">{{ t('import.type_comptabilite') }}</label>
              </div>
            </div>
          </div>

          <div class="import-guidance">
            <article class="import-guidance-card">
              <h3 class="import-guidance-card__title">{{ t('import.guidance_common_title') }}</h3>
              <ul class="import-guidance-card__list">
                <li>{{ t('import.guidance_common_exercise') }}</li>
                <li>{{ t('import.guidance_common_seed_accounts') }}</li>
                <li>{{ t('import.guidance_common_seed_rules') }}</li>
              </ul>
            </article>
            <article class="import-guidance-card">
              <h3 class="import-guidance-card__title">
                {{ importType === 'gestion' ? t('import.type_gestion') : t('import.type_comptabilite') }}
              </h3>
              <ul v-if="importType === 'gestion'" class="import-guidance-card__list">
                <li>{{ t('import.guidance_gestion_scope') }}</li>
                <li>{{ t('import.guidance_gestion_fiscal_year') }}</li>
                <li>{{ t('import.guidance_gestion_supplier') }}</li>
              </ul>
              <ul v-else class="import-guidance-card__list">
                <li>{{ t('import.guidance_compta_scope') }}</li>
                <li>{{ t('import.guidance_compta_coexistence') }}</li>
                <li>{{ t('import.guidance_compta_chart') }}</li>
              </ul>
            </article>
          </div>

          <!-- File picker -->
          <div class="app-field">
            <label class="app-field__label">{{ t('import.file_label') }}</label>
            <input
              ref="fileInput"
              type="file"
              accept=".xlsx,.xls"
              class="hidden"
              @change="onFileChange"
            />
            <p v-if="selectedFile && preview" class="import-preview-state" :class="previewStateClass">
              {{ previewStateMessage }}
            </p>
            <div class="import-file-row">
              <Button
                :label="t('import.choose_file')"
                icon="pi pi-upload"
                severity="secondary"
                outlined
                @click="fileInput?.click()"
              />
              <span v-if="selectedFile" class="import-file-name">{{ selectedFile.name }}</span>
              <span v-else class="import-file-name import-file-name--empty">—</span>
            </div>
          </div>

          <!-- Submit / Preview buttons -->
          <div class="app-form-actions">
            <Button
              data-testid="preview-button"
              :label="t('import.preview')"
              icon="pi pi-eye"
              severity="secondary"
              outlined
              :loading="previewing"
              :disabled="!selectedFile"
              @click="doPreview"
            />
            <Button
              data-testid="primary-import-button"
              :label="t('import.submit')"
              icon="pi pi-check"
              :loading="importing"
              :disabled="!canConfirmImport"
              @click="doImport"
            />
          </div>
          <p class="import-action-hint">{{ importActionHint }}</p>
          <div
            v-if="result"
            data-testid="import-result-banner"
            class="import-result-banner"
            :class="resultHasIssues ? 'import-result-banner--warning' : 'import-result-banner--success'"
          >
            <strong>{{ resultStateMessage }}</strong>
            <p>{{ resultStateDetail }}</p>
          </div>
       </div>
     </AppPanel>

    <AppPanel
      v-if="testShortcuts.length"
      :title="t('import.test_shortcuts_title')"
      :subtitle="t('import.test_shortcuts_subtitle')"
      dense
    >
      <p class="import-action-hint">{{ t('import.test_shortcuts_hint') }}</p>
      <div class="import-shortcuts-grid">
        <article v-for="shortcut in testShortcuts" :key="shortcut.alias" class="import-shortcut-card">
          <div class="import-shortcut-card__body">
            <div>
              <h3 class="import-shortcut-card__title">{{ shortcut.label }}</h3>
              <p class="import-shortcut-card__meta">{{ shortcut.file_name ?? t('import.test_shortcuts_missing_file') }}</p>
            </div>
            <p v-if="shortcut.message" class="import-shortcut-card__message">{{ shortcut.message }}</p>
          </div>
          <Button
            :data-testid="`quick-import-${shortcut.alias}`"
            :label="t('import.test_shortcuts_run', { label: shortcut.label })"
            icon="pi pi-bolt"
            severity="contrast"
            outlined
            :disabled="!shortcut.available || importing"
            :loading="runningShortcutAlias === shortcut.alias"
            @click="runTestShortcut(shortcut.alias)"
          />
        </article>
      </div>
    </AppPanel>

    <!-- Preview -->
    <AppPanel v-if="preview" :title="t('import.preview_title')" dense>
      <div class="import-summary-grid">
          <div class="import-summary-row">
            <span>{{ t('import.estimated_contacts') }}</span>
            <span class="font-medium">{{ preview.estimated_contacts }}</span>
          </div>
          <div class="import-summary-row">
            <span>{{ t('import.estimated_invoices') }}</span>
            <span class="font-medium">{{ preview.estimated_invoices }}</span>
          </div>
          <div class="import-summary-row">
            <span>{{ t('import.estimated_payments') }}</span>
            <span class="font-medium">{{ preview.estimated_payments }}</span>
          </div>
          <div class="import-summary-row">
            <span>{{ t('import.estimated_salaries') }}</span>
            <span class="font-medium">{{ preview.estimated_salaries }}</span>
          </div>
          <div class="import-summary-row">
            <span>{{ t('import.estimated_entries') }}</span>
            <span class="font-medium">{{ preview.estimated_entries }}</span>
          </div>
        </div>
        <p class="import-preview-state" :class="preview.can_import ? 'import-preview-state--ready' : 'import-preview-state--blocked'">
          {{ preview.can_import ? t('import.preview_ready') : t('import.preview_blocked') }}
        </p>
        <div v-if="preview.warnings.length" class="import-warnings-block">
          <span class="app-field__label">{{ t('import.warnings') }}</span>
          <ul class="import-warnings">
            <li v-for="(warning, idx) in preview.warnings" :key="`warning-${idx}`">{{ warning }}</li>
          </ul>
        </div>
        <div v-if="hasPreviewWarnings && preview.can_import" class="import-confirmation-guard">
          <label class="import-confirmation-guard__checkbox">
            <Checkbox
              v-model="warningsAcknowledged"
              binary
              data-testid="warning-ack-checkbox"
            />
            <span>{{ t('import.warning_ack_label') }}</span>
          </label>
          <p class="import-confirmation-guard__help">{{ t('import.warning_ack_help') }}</p>
        </div>
        <div v-if="preview.errors.length" class="import-errors">
          <span class="app-field__label">{{ t('import.errors') }}</span>
          <ul>
            <li v-for="(err, idx) in preview.errors" :key="idx">{{ err }}</li>
          </ul>
        </div>
        <div v-if="preview.sheets.length" class="import-sheet-list">
          <h3 class="import-sheet-list__title">{{ t('import.sheets_title') }}</h3>
          <article v-for="sheet in preview.sheets" :key="sheet.name" class="import-sheet-card">
            <div class="import-sheet-card__header">
              <div>
                <h4 class="import-sheet-card__title">{{ sheet.name }}</h4>
                <p class="import-sheet-card__meta">
                  {{ previewSheetKindLabel(sheet.kind) }} · {{ previewSheetStatusLabel(sheet.status) }}
                </p>
              </div>
              <div class="import-sheet-card__stats">
                <strong class="import-sheet-card__rows">{{ t('import.sheet_rows', { count: sheet.rows }) }}</strong>
                <span v-if="sheet.ignored_rows" class="import-sheet-card__stat import-sheet-card__stat--warning">
                  {{ t('import.sheet_ignored_rows', { count: sheet.ignored_rows }) }}
                </span>
                <span v-if="sheet.blocked_rows" class="import-sheet-card__stat import-sheet-card__stat--danger">
                  {{ t('import.sheet_blocked_rows', { count: sheet.blocked_rows }) }}
                </span>
              </div>
            </div>

            <div v-if="sheet.detected_columns.length" class="import-sheet-card__section">
              <span class="app-field__label">{{ t('import.detected_columns') }}</span>
              <div class="import-chip-row">
                <span v-for="column in sheet.detected_columns" :key="column" class="import-chip">{{ column }}</span>
              </div>
            </div>

            <div v-if="sheet.missing_columns.length" class="import-sheet-card__section">
              <span class="app-field__label">{{ t('import.missing_columns') }}</span>
              <div class="import-chip-row">
                <span v-for="column in sheet.missing_columns" :key="column" class="import-chip import-chip--danger">{{ column }}</span>
              </div>
            </div>

            <ul v-if="sheet.warnings.length" class="import-warnings">
              <li v-for="(warning, idx) in sheet.warnings" :key="`${sheet.name}-warning-${idx}`">{{ warning }}</li>
            </ul>
            <ul v-if="sheet.errors.length" class="import-errors">
              <li v-for="(error, idx) in sheet.errors" :key="`${sheet.name}-error-${idx}`">{{ error }}</li>
            </ul>
          </article>
        </div>
        <div class="app-form-actions import-confirm">
          <Button
            data-testid="confirm-import-button"
            :label="t('import.confirm_import')"
            icon="pi pi-check"
            :loading="importing"
            :disabled="!canConfirmImport"
            @click="doImport"
          />
        </div>
    </AppPanel>

    <!-- Result -->
    <AppPanel v-if="result" :title="t('import.result_title')" dense>
        <div class="import-result-list">
          <div class="import-summary-row">
            <span>{{ t('import.contacts_created') }}</span>
            <span class="font-medium">{{ result.contacts_created }}</span>
          </div>
          <div class="import-summary-row">
            <span>{{ t('import.invoices_created') }}</span>
            <span class="font-medium">{{ result.invoices_created }}</span>
          </div>
          <div class="import-summary-row">
            <span>{{ t('import.payments_created') }}</span>
            <span class="font-medium">{{ result.payments_created }}</span>
          </div>
          <div class="import-summary-row">
            <span>{{ t('import.salaries_created') }}</span>
            <span class="font-medium">{{ result.salaries_created }}</span>
          </div>
          <div class="import-summary-row">
            <span>{{ t('import.entries_created') }}</span>
            <span class="font-medium">{{ result.entries_created }}</span>
          </div>
          <div class="import-summary-row">
            <span>{{ t('import.cash_created') }}</span>
            <span class="font-medium">{{ result.cash_created }}</span>
          </div>
          <div class="import-summary-row">
            <span>{{ t('import.bank_created') }}</span>
            <span class="font-medium">{{ result.bank_created }}</span>
          </div>
          <div class="import-summary-row">
            <span>{{ t('import.ignored_rows') }}</span>
            <span class="font-medium">{{ result.ignored_rows }}</span>
          </div>
          <div class="import-summary-row">
            <span>{{ t('import.blocked_rows') }}</span>
            <span class="font-medium">{{ result.blocked_rows }}</span>
          </div>

          <div v-if="result.warnings.length" class="import-warnings-block">
            <span class="app-field__label">{{ t('import.warnings') }}</span>
            <ul class="import-warnings">
              <li v-for="(warning, idx) in result.warnings" :key="`result-warning-${idx}`">{{ warning }}</li>
            </ul>
          </div>

          <div class="import-errors-block">
            <span class="app-field__label">{{ t('import.errors') }}</span>
            <div v-if="result.errors.length === 0" class="app-empty-state import-empty-inline">
              {{ t('import.no_errors') }}
            </div>
            <ul v-else class="import-errors">
              <li v-for="(err, idx) in result.errors" :key="idx">{{ err }}</li>
            </ul>
          </div>

          <div v-if="result.sheets.length" class="import-sheet-list">
            <h3 class="import-sheet-list__title">{{ t('import.result_sheets_title') }}</h3>
            <article v-for="sheet in result.sheets" :key="`result-${sheet.name}-${sheet.kind}`" class="import-sheet-card">
              <div class="import-sheet-card__header">
                <div>
                  <h4 class="import-sheet-card__title">{{ sheet.name }}</h4>
                  <p class="import-sheet-card__meta">{{ importSheetKindLabel(sheet.kind) }}</p>
                </div>
                <div class="import-sheet-card__stats">
                  <span class="import-sheet-card__stat import-sheet-card__stat--success">
                    {{ t('import.sheet_imported_rows', { count: sheet.imported_rows }) }}
                  </span>
                  <span v-if="sheet.ignored_rows" class="import-sheet-card__stat import-sheet-card__stat--warning">
                    {{ t('import.sheet_ignored_rows', { count: sheet.ignored_rows }) }}
                  </span>
                  <span v-if="sheet.blocked_rows" class="import-sheet-card__stat import-sheet-card__stat--danger">
                    {{ t('import.sheet_blocked_rows', { count: sheet.blocked_rows }) }}
                  </span>
                </div>
              </div>

              <ul v-if="sheet.warnings.length" class="import-warnings">
                <li v-for="(warning, idx) in sheet.warnings" :key="`${sheet.name}-result-warning-${idx}`">{{ warning }}</li>
              </ul>
              <ul v-if="sheet.errors.length" class="import-errors">
                <li v-for="(error, idx) in sheet.errors" :key="`${sheet.name}-result-error-${idx}`">{{ error }}</li>
              </ul>
            </article>
          </div>
        </div>
    </AppPanel>

    <Toast />
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import RadioButton from 'primevue/radiobutton'
import Toast from 'primevue/toast'
import { useToast } from 'primevue/usetoast'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import {
  importGestionFileApi,
  importTestShortcutApi,
  importComptabiliteFileApi,
  listTestImportShortcutsApi,
  previewGestionFileApi,
  previewComptabiliteFileApi,
  type ImportResult,
  type PreviewSheetResult,
  type PreviewResult,
  type TestImportShortcut,
} from '../api/accounting'

const { t } = useI18n()
const toast = useToast()

const importType = ref<'gestion' | 'comptabilite'>('gestion')
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const importing = ref(false)
const previewing = ref(false)
const result = ref<ImportResult | null>(null)
const preview = ref<PreviewResult | null>(null)
const warningsAcknowledged = ref(false)
const testShortcuts = ref<TestImportShortcut[]>([])
const runningShortcutAlias = ref<string | null>(null)
const resultHasIssues = computed(() => Boolean(
  result.value && (result.value.errors.length > 0 || result.value.warnings.length > 0),
))
const resultCreatedCount = computed(() => {
  if (!result.value) return 0
  return (
    result.value.contacts_created
    + result.value.invoices_created
    + result.value.payments_created
    + result.value.salaries_created
    + result.value.entries_created
    + result.value.cash_created
    + result.value.bank_created
  )
})
const resultStateMessage = computed(() => {
  if (!result.value) return ''
  return resultHasIssues.value ? t('import.completed_with_issues') : t('import.success')
})
const resultStateDetail = computed(() => {
  if (!result.value) return ''
  return t('import.result_persistent_hint', {
    count: resultCreatedCount.value,
    ignored: result.value.ignored_rows,
    blocked: result.value.blocked_rows,
  })
})
const hasPreviewWarnings = computed(() => Boolean(
  preview.value
  && (
    preview.value.warnings.length > 0
    || preview.value.warning_details.length > 0
    || preview.value.sheets.some((sheet) => sheet.warnings.length > 0 || sheet.warning_details.length > 0)
  ),
))
const canConfirmImport = computed(() => Boolean(
  selectedFile.value
  && preview.value?.can_import
  && (!hasPreviewWarnings.value || warningsAcknowledged.value),
))
const previewState = computed<'ready' | 'noop' | 'blocked'>(() => {
  if (!preview.value) return 'blocked'
  if (preview.value.can_import) return 'ready'
  if (preview.value.errors.length === 0) return 'noop'
  return 'blocked'
})
const previewStateClass = computed(() => {
  if (previewState.value === 'ready') return 'import-preview-state--ready'
  if (previewState.value === 'noop') return 'import-preview-state--noop'
  return 'import-preview-state--blocked'
})
const previewStateMessage = computed(() => {
  if (previewState.value === 'ready') return t('import.preview_ready')
  if (previewState.value === 'noop') return t('import.preview_noop')
  return t('import.preview_blocked')
})
const importActionHint = computed(() => {
  if (!selectedFile.value) return t('import.file_required')
  if (!preview.value) return t('import.preview_required')
  if (hasPreviewWarnings.value && !warningsAcknowledged.value) return t('import.warning_ack_required')
  if (!preview.value.can_import) return t('import.preview_blocked')
  return t('import.import_ready')
})

function resetImportFlow() {
  result.value = null
  preview.value = null
  warningsAcknowledged.value = false
}

watch(importType, () => {
  resetImportFlow()
})

onMounted(async () => {
  await loadTestShortcuts()
})

function previewSheetKindLabel(kind: PreviewSheetResult['kind']) {
  return t(`import.sheet_kind.${kind}`)
}

function previewSheetStatusLabel(status: PreviewSheetResult['status']) {
  return t(`import.sheet_status.${status}`)
}

function importSheetKindLabel(kind: string) {
  return t(`import.sheet_kind.${kind}`)
}

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
  resetImportFlow()
}

async function loadTestShortcuts() {
  try {
    testShortcuts.value = (await listTestImportShortcutsApi()).sort((left, right) => left.order - right.order)
  } catch (error: unknown) {
    const status = (error as { response?: { status?: number } }).response?.status
    if (status !== 404) {
      toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
    }
    testShortcuts.value = []
  }
}

async function doPreview() {
  if (!selectedFile.value) return
  previewing.value = true
  warningsAcknowledged.value = false
  preview.value = null
  result.value = null
  try {
    if (importType.value === 'gestion') {
      preview.value = await previewGestionFileApi(selectedFile.value)
    } else {
      preview.value = await previewComptabiliteFileApi(selectedFile.value)
    }
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  } finally {
    previewing.value = false
  }
}

async function doImport() {
  if (!selectedFile.value) {
    toast.add({ severity: 'warn', summary: t('import.file_required'), life: 3000 })
    return
  }
  if (!preview.value) {
    toast.add({ severity: 'warn', summary: t('import.preview_required'), life: 3000 })
    return
  }
  if (hasPreviewWarnings.value && !warningsAcknowledged.value) {
    toast.add({ severity: 'warn', summary: t('import.warning_ack_required'), life: 3500 })
    return
  }
  if (!preview.value.can_import) {
    toast.add({ severity: 'warn', summary: t('import.preview_blocked'), life: 3500 })
    return
  }
  importing.value = true
  result.value = null
  try {
    if (importType.value === 'gestion') {
      result.value = await importGestionFileApi(selectedFile.value)
    } else {
      result.value = await importComptabiliteFileApi(selectedFile.value)
    }
    const hasIssues = result.value.errors.length > 0 || result.value.warnings.length > 0
    toast.add({
      severity: hasIssues ? 'warn' : 'success',
      summary: hasIssues ? t('import.completed_with_issues') : t('import.success'),
      life: 3500,
    })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  } finally {
    importing.value = false
  }
}

async function runTestShortcut(alias: string) {
  importing.value = true
  runningShortcutAlias.value = alias
  selectedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  preview.value = null
  warningsAcknowledged.value = false
  result.value = null
  try {
    const shortcut = testShortcuts.value.find((item) => item.alias === alias)
    if (shortcut) {
      importType.value = shortcut.import_type
    }
    result.value = await importTestShortcutApi(alias)
    const hasIssues = result.value.errors.length > 0 || result.value.warnings.length > 0
    toast.add({
      severity: hasIssues ? 'warn' : 'success',
      summary: hasIssues ? t('import.completed_with_issues') : t('import.success'),
      life: 3500,
    })
    await loadTestShortcuts()
  } catch (error: unknown) {
    const detail = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
    toast.add({ severity: 'error', summary: detail ?? t('common.error.unknown'), life: 4500 })
  } finally {
    importing.value = false
    runningShortcutAlias.value = null
  }
}
</script>

<style scoped>
.import-form {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-5);
}

.import-type-row {
  display: flex;
  gap: var(--app-space-4);
  flex-wrap: wrap;
}

.import-radio-item {
  display: inline-flex;
  align-items: center;
  gap: var(--app-space-2);
}

.import-file-row {
  display: flex;
  align-items: center;
  gap: var(--app-space-3);
  flex-wrap: wrap;
}

.import-file-name {
  color: var(--p-text-color);
  font-size: 0.95rem;
}

.import-file-name--empty {
  color: var(--p-text-muted-color);
}

.import-guidance {
  display: grid;
  gap: var(--app-space-3);
  grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr));
}

.import-guidance-card {
  padding: var(--app-space-4);
  border: 1px solid var(--app-surface-border);
  border-radius: var(--app-radius-md);
  background: linear-gradient(180deg, var(--app-surface-bg), var(--app-surface-muted));
}

.import-guidance-card__title {
  margin: 0 0 var(--app-space-2);
  font-size: 1rem;
}

.import-guidance-card__list {
  margin: 0;
  padding-left: 1rem;
  color: var(--p-text-muted-color);
  font-size: 0.95rem;
}

.import-shortcuts-grid {
  display: grid;
  gap: var(--app-space-3);
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
}

.import-shortcut-card {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
  padding: var(--app-space-4);
  border: 1px solid var(--app-surface-border);
  border-radius: var(--app-radius-md);
  background: linear-gradient(180deg, var(--app-surface-bg), var(--app-surface-muted));
}

.import-shortcut-card__body {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-2);
}

.import-shortcut-card__title,
.import-shortcut-card__meta,
.import-shortcut-card__message {
  margin: 0;
}

.import-shortcut-card__meta,
.import-shortcut-card__message {
  color: var(--p-text-muted-color);
  font-size: 0.92rem;
}

.import-action-hint {
  margin: 0;
  color: var(--p-text-muted-color);
  font-size: 0.95rem;
}

.import-result-banner {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-2);
  padding: var(--app-space-3) var(--app-space-4);
  border-radius: var(--app-radius-md);
}

.import-result-banner strong,
.import-result-banner p {
  margin: 0;
}

.import-result-banner--success {
  background: color-mix(in srgb, var(--p-green-500) 12%, var(--app-surface-bg) 88%);
  color: color-mix(in srgb, var(--p-green-700) 78%, var(--p-text-color) 22%);
}

.import-result-banner--warning {
  background: color-mix(in srgb, var(--p-amber-500) 12%, var(--app-surface-bg) 88%);
  color: color-mix(in srgb, var(--p-amber-700) 78%, var(--p-text-color) 22%);
}

.import-summary-grid,
.import-result-list {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
}

.import-summary-row {
  display: flex;
  justify-content: space-between;
  gap: var(--app-space-3);
  padding-bottom: var(--app-space-2);
  border-bottom: 1px solid var(--app-surface-border);
}

.import-preview-state {
  margin: var(--app-space-4) 0 0;
  padding: var(--app-space-3) var(--app-space-4);
  border-radius: var(--app-radius-md);
  font-size: 0.95rem;
}

.import-preview-state--ready {
  background: color-mix(in srgb, var(--p-green-500) 12%, var(--app-surface-bg) 88%);
  color: color-mix(in srgb, var(--p-green-700) 78%, var(--p-text-color) 22%);
}

.import-preview-state--blocked {
  background: color-mix(in srgb, var(--p-amber-500) 14%, var(--app-surface-bg) 86%);
  color: color-mix(in srgb, var(--p-amber-700) 72%, var(--p-text-color) 28%);
}

.import-preview-state--noop {
  background: color-mix(in srgb, var(--p-surface-400) 16%, var(--app-surface-bg) 84%);
  color: color-mix(in srgb, var(--p-text-muted-color) 88%, var(--p-text-color) 12%);
}

.import-errors,
.import-errors ul {
  margin: 0;
  padding-left: 1rem;
  color: var(--p-red-500);
  font-size: 0.92rem;
}

.import-warnings {
  margin: 0;
  padding-left: 1rem;
  color: var(--p-amber-700);
  font-size: 0.92rem;
}

.import-confirmation-guard {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-2);
  padding: var(--app-space-3) var(--app-space-4);
  border: 1px solid color-mix(in srgb, var(--p-amber-500) 35%, var(--app-surface-border) 65%);
  border-radius: var(--app-radius-md);
  background: color-mix(in srgb, var(--p-amber-500) 10%, var(--app-surface-bg) 90%);
}

.import-confirmation-guard__checkbox {
  display: inline-flex;
  align-items: flex-start;
  gap: var(--app-space-3);
}

.import-confirmation-guard__help {
  margin: 0;
  color: var(--p-text-muted-color);
  font-size: 0.95rem;
}

.import-sheet-list {
  margin-top: var(--app-space-5);
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.import-sheet-list__title {
  margin: 0;
  font-size: 1rem;
}

.import-sheet-card {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
  padding: var(--app-space-4);
  border: 1px solid var(--app-surface-border);
  border-radius: var(--app-radius-md);
  background: linear-gradient(180deg, var(--app-surface-bg), var(--app-surface-muted));
  box-shadow: inset 0 1px 0 color-mix(in srgb, white 18%, transparent 82%);
}

.import-sheet-card__header {
  display: flex;
  justify-content: space-between;
  gap: var(--app-space-3);
  align-items: flex-start;
}

.import-sheet-card__title,
.import-sheet-card__meta {
  margin: 0;
}

.import-sheet-card__meta {
  color: var(--p-text-muted-color);
  font-size: 0.92rem;
}

.import-sheet-card__rows {
  font-size: 0.92rem;
}

.import-sheet-card__stats {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--app-space-1);
}

.import-sheet-card__stat {
  font-size: 0.84rem;
}

.import-sheet-card__stat--success {
  color: color-mix(in srgb, var(--p-green-700) 74%, var(--p-text-color) 26%);
}

.import-sheet-card__stat--warning {
  color: var(--p-amber-700);
}

.import-sheet-card__stat--danger {
  color: var(--p-red-500);
}

.import-sheet-card__section {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-2);
}

.import-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--app-space-2);
}

.import-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.28rem 0.55rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--app-surface-muted) 86%, var(--app-surface-bg) 14%);
  color: var(--p-text-color);
  font-size: 0.84rem;
  border: 1px solid color-mix(in srgb, var(--app-surface-border) 84%, transparent 16%);
}

.import-chip--danger {
  background: color-mix(in srgb, var(--p-red-500) 12%, var(--app-surface-bg) 88%);
  color: color-mix(in srgb, var(--p-red-700) 78%, var(--p-text-color) 22%);
  border-color: color-mix(in srgb, var(--p-red-500) 25%, var(--app-surface-border) 75%);
}

.import-warnings-block,
.import-confirm,
.import-errors-block {
  margin-top: var(--app-space-4);
}

.import-empty-inline {
  padding: var(--app-space-3) 0 0;
  text-align: left;
}

:global(html.dark-mode) .import-preview-state--ready {
  color: var(--p-green-100);
}

:global(html.dark-mode) .import-preview-state--blocked {
  color: var(--p-amber-100);
}

:global(html.dark-mode) .import-preview-state--noop {
  color: color-mix(in srgb, var(--p-surface-100) 72%, white 28%);
}

:global(html.dark-mode) .import-warnings {
  color: var(--p-amber-200);
}

:global(html.dark-mode) .import-errors,
:global(html.dark-mode) .import-errors ul {
  color: var(--p-red-200);
}

:global(html.dark-mode) .import-chip--danger {
  color: var(--p-red-100);
}
</style>
