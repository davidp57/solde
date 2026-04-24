<template>
  <AppPage>
    <AppPageHeader
      :eyebrow="t('ui.page.collection_eyebrow')"
      :title="t('import.title')"
      :subtitle="t('import.subtitle')"
    >
      <template #actions>
        <Button
          :label="t('import.open_history')"
          icon="pi pi-history"
          severity="secondary"
          outlined
          @click="router.push('/import/history')"
        />
      </template>
    </AppPageHeader>

    <ImportExcelFormPanel
      ref="formPanelRef"
      v-model:import-type="importType"
      v-model:comparison-start-date="comparisonStartDate"
      v-model:comparison-end-date="comparisonEndDate"
      :selected-file="selectedFile"
      :preview="preview"
      :result="result"
      :active-run="activeRun"
      :importing="importing"
      :previewing="previewing"
      @file-selected="onFileSelected"
      @preview-click="doPreview"
      @import-click="doImport"
    />

    <ImportExcelShortcutsPanel
      v-if="testShortcuts.length"
      :test-shortcuts="testShortcuts"
      :importing="importing"
      :running-shortcut-alias="runningShortcutAlias"
      :running-all="runningAllShortcuts"
      @run-shortcut="runTestShortcut"
      @run-all-shortcuts="runAllTestShortcuts"
    />

    <div v-if="preview || result" class="import-surface-shell">
      <div v-if="preview" ref="previewPanel">
        <ImportExcelPreviewPanel
          :preview="preview"
          :active-run="activeRun"
          :importing="importing"
          :busy-run-id="busyRunId"
          :busy-operation-id="busyOperationId"
          :can-confirm-import="canConfirmImport"
          @undo-operation="undoOperation"
          @redo-operation="redoOperation"
          @undo-run="undoRun"
          @redo-run="redoRun"
          @do-import="doImport"
        />
      </div>
      <ImportExcelResultPanel v-if="result" :result="result" />
    </div>

    <Toast />
  </AppPage>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Toast from 'primevue/toast'
import { useToast } from 'primevue/usetoast'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import ImportExcelFormPanel from '../components/import/ImportExcelFormPanel.vue'
import ImportExcelShortcutsPanel from '../components/import/ImportExcelShortcutsPanel.vue'
import ImportExcelPreviewPanel from '../components/import/ImportExcelPreviewPanel.vue'
import ImportExcelResultPanel from '../components/import/ImportExcelResultPanel.vue'
import { getSettingsApi } from '../api/settings'
import {
  importTestShortcutApi,
  executeImportRunApi,
  getImportRunApi,
  listTestImportShortcutsApi,
  prepareComptabiliteRunApi,
  prepareGestionRunApi,
  redoImportOperationApi,
  redoImportRunApi,
  undoImportOperationApi,
  undoImportRunApi,
  type ImportResult,
  type ImportRunRead,
  type PreviewResult,
  type TestImportShortcut,
} from '../api/accounting'

const { t } = useI18n()
const toast = useToast()
const router = useRouter()

const formPanelRef = ref<{ resetFile: () => void } | null>(null)
const importType = ref<'gestion' | 'comptabilite'>('gestion')
const selectedFile = ref<File | null>(null)
const importing = ref(false)
const previewing = ref(false)
const fiscalYearStartMonth = ref(8)
const result = ref<ImportResult | null>(null)
const preview = ref<PreviewResult | null>(null)
const previewPanel = ref<HTMLElement | null>(null)
const activeRun = ref<ImportRunRead | null>(null)
const busyRunId = ref<number | null>(null)
const busyOperationId = ref<number | null>(null)
const comparisonStartDate = ref('')
const comparisonEndDate = ref('')
const testShortcuts = ref<TestImportShortcut[]>([])
const runningShortcutAlias = ref<string | null>(null)
const runningAllShortcuts = ref(false)

const canConfirmImport = computed(() =>
  Boolean(selectedFile.value && preview.value?.can_import && activeRun.value?.can_execute !== false),
)

function resetImportFlow() {
  result.value = null
  preview.value = null
  activeRun.value = null
}

function shouldDisplayRunSummary(run: ImportRunRead) {
  return run.status !== 'prepared' && run.status !== 'blocked'
}

function syncRunState(run: ImportRunRead) {
  activeRun.value = run
  preview.value = run.preview
  result.value = shouldDisplayRunSummary(run) ? run.summary : null
}

function padMonth(value: number) {
  return String(value).padStart(2, '0')
}

function formatIsoDate(value: Date) {
  return `${value.getFullYear()}-${padMonth(value.getMonth() + 1)}-${padMonth(value.getDate())}`
}

function buildDefaultComparisonRange(fileName: string | undefined) {
  if (!fileName) return { start: '', end: '' }
  const yearMatch = fileName.match(/(20\d{2})/)
  if (!yearMatch || !yearMatch[1]) return { start: '', end: '' }
  const startYear = Number.parseInt(yearMatch[1], 10)
  const startMonth = Math.min(Math.max(fiscalYearStartMonth.value, 1), 12)
  const startDate = new Date(startYear, startMonth - 1, 1)
  const nextFiscalYearStart = new Date(startYear + 1, startMonth - 1, 1)
  const endDate = new Date(nextFiscalYearStart.getTime() - 24 * 60 * 60 * 1000)
  return { start: formatIsoDate(startDate), end: formatIsoDate(endDate) }
}

function applyDefaultComparisonRange(fileName: string | undefined = selectedFile.value?.name) {
  const defaults = buildDefaultComparisonRange(fileName)
  comparisonStartDate.value = defaults.start
  comparisonEndDate.value = defaults.end
}

function getImportErrorSummary(error: unknown): string {
  const responseData = (error as { response?: { data?: unknown } }).response?.data
  const detail = responseData && typeof responseData === 'object'
    ? (responseData as { detail?: unknown }).detail
    : undefined
  if (typeof detail === 'string' && detail.trim()) return detail
  if ((error as { code?: string }).code === 'ECONNABORTED') return t('import.request_timeout')
  const message = (error as { message?: unknown }).message
  if (typeof message === 'string' && message.trim()) return message
  return t('common.error.unknown')
}

function isRequestTimeout(error: unknown): boolean {
  return (error as { code?: string }).code === 'ECONNABORTED'
}

async function refreshRunAfterTimeout(runId: number) {
  try {
    const refreshedRun = await getImportRunApi(runId)
    syncRunState(refreshedRun)
    toast.add({ severity: 'info', summary: t('import.request_timeout_refreshed'), life: 5000 })
  } catch {
    toast.add({ severity: 'warn', summary: t('import.request_timeout'), life: 5000 })
  }
}

async function scrollToPreviewPanel() {
  await nextTick()
  previewPanel.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function loadTestShortcuts() {
  try {
    testShortcuts.value = (await listTestImportShortcutsApi()).sort(
      (left, right) => left.order - right.order,
    )
  } catch (error: unknown) {
    const status = (error as { response?: { status?: number } }).response?.status
    if (status !== 404) toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
    testShortcuts.value = []
  }
}

async function loadSettings() {
  try {
    const data = await getSettingsApi()
    fiscalYearStartMonth.value = data.fiscal_year_start_month
    applyDefaultComparisonRange()
  } catch {
    fiscalYearStartMonth.value = 8
  }
}

function onFileSelected(file: File | null) {
  selectedFile.value = file
  resetImportFlow()
  applyDefaultComparisonRange(file?.name)
}

async function doPreview() {
  if (!selectedFile.value) return
  previewing.value = true
  preview.value = null
  result.value = null
  activeRun.value = null
  try {
    const comparisonWindow = {
      comparison_start_date: comparisonStartDate.value || undefined,
      comparison_end_date: comparisonEndDate.value || undefined,
    }
    if (importType.value === 'gestion') {
      syncRunState(await prepareGestionRunApi(selectedFile.value, comparisonWindow))
    } else {
      syncRunState(await prepareComptabiliteRunApi(selectedFile.value, comparisonWindow))
    }
    await scrollToPreviewPanel()
  } catch (error: unknown) {
    toast.add({ severity: 'error', summary: getImportErrorSummary(error), life: 5000 })
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
  if (!preview.value.can_import) {
    toast.add({ severity: 'warn', summary: t('import.preview_blocked'), life: 3500 })
    return
  }
  if (!activeRun.value?.can_execute) {
    toast.add({ severity: 'warn', summary: t('import.run_not_executable'), life: 3500 })
    return
  }
  importing.value = true
  result.value = null
  try {
    const run = await executeImportRunApi(activeRun.value.id)
    syncRunState(run)
    const runResult = run.summary
    const hasFailed = run.status === 'failed'
    const hasIssues = Boolean(hasFailed || (runResult && (runResult.errors.length > 0 || runResult.warnings.length > 0)))
    toast.add({
      severity: hasFailed ? 'error' : hasIssues ? 'warn' : 'success',
      summary: hasFailed ? t('import.failed') : hasIssues ? t('import.completed_with_issues') : t('import.success'),
      detail: hasFailed ? getImportErrorSummary(runResult) : undefined,
      life: hasFailed ? 5000 : 3500,
    })
  } catch (error: unknown) {
    if (isRequestTimeout(error) && activeRun.value?.id != null) {
      await refreshRunAfterTimeout(activeRun.value.id)
      return
    }
    toast.add({ severity: 'error', summary: getImportErrorSummary(error), life: 5000 })
  } finally {
    importing.value = false
  }
}

async function undoRun(runId: number) {
  busyRunId.value = runId
  try {
    const run = await undoImportRunApi(runId)
    if (activeRun.value?.id === runId) syncRunState(run)
  } catch (error: unknown) {
    if (isRequestTimeout(error)) { await refreshRunAfterTimeout(runId); return }
    toast.add({ severity: 'error', summary: getImportErrorSummary(error), life: 5000 })
  } finally {
    busyRunId.value = null
  }
}

async function redoRun(runId: number) {
  busyRunId.value = runId
  try {
    const run = await redoImportRunApi(runId)
    if (activeRun.value?.id === runId) syncRunState(run)
  } catch (error: unknown) {
    if (isRequestTimeout(error)) { await refreshRunAfterTimeout(runId); return }
    toast.add({ severity: 'error', summary: getImportErrorSummary(error), life: 5000 })
  } finally {
    busyRunId.value = null
  }
}

async function undoOperation(operationId: number) {
  busyOperationId.value = operationId
  try {
    const run = await undoImportOperationApi(operationId)
    syncRunState(run)
  } catch (error: unknown) {
    if (isRequestTimeout(error) && activeRun.value?.id != null) {
      await refreshRunAfterTimeout(activeRun.value.id)
      return
    }
    toast.add({ severity: 'error', summary: getImportErrorSummary(error), life: 5000 })
  } finally {
    busyOperationId.value = null
  }
}

async function redoOperation(operationId: number) {
  busyOperationId.value = operationId
  try {
    const run = await redoImportOperationApi(operationId)
    syncRunState(run)
  } catch (error: unknown) {
    if (isRequestTimeout(error) && activeRun.value?.id != null) {
      await refreshRunAfterTimeout(activeRun.value.id)
      return
    }
    toast.add({ severity: 'error', summary: getImportErrorSummary(error), life: 5000 })
  } finally {
    busyOperationId.value = null
  }
}

async function runTestShortcut(alias: string) {
  importing.value = true
  runningShortcutAlias.value = alias
  selectedFile.value = null
  formPanelRef.value?.resetFile()
  preview.value = null
  result.value = null
  try {
    const shortcut = testShortcuts.value.find((item) => item.alias === alias)
    if (shortcut) {
      importType.value = shortcut.import_type
      applyDefaultComparisonRange(shortcut.file_name ?? undefined)
    }
    const comparisonWindow = {
      comparison_start_date: comparisonStartDate.value || undefined,
      comparison_end_date: comparisonEndDate.value || undefined,
    }
    const run = await importTestShortcutApi(alias, comparisonWindow)
    syncRunState(run)
    if (run.summary) {
      const hasFailed = run.status === 'failed'
      const hasIssues = Boolean(hasFailed || run.summary.errors.length > 0 || run.summary.warnings.length > 0)
      toast.add({
        severity: hasFailed ? 'error' : hasIssues ? 'warn' : 'success',
        summary: hasFailed ? t('import.failed') : hasIssues ? t('import.completed_with_issues') : t('import.success'),
        detail: hasFailed ? getImportErrorSummary(run.summary) : undefined,
        life: hasFailed ? 5000 : 3500,
      })
    } else {
      toast.add({
        severity: 'warn',
        summary: run.preview?.can_import ? t('import.run_not_executable') : t('import.preview_blocked'),
        life: 4000,
      })
    }
    await scrollToPreviewPanel()
    await loadTestShortcuts()
  } catch (error: unknown) {
    toast.add({ severity: 'error', summary: getImportErrorSummary(error), life: 4500 })
  } finally {
    importing.value = false
    runningShortcutAlias.value = null
  }
}

const ALL_SHORTCUTS_ORDER = ['gestion-2024', 'comptabilite-2024', 'gestion-2025', 'comptabilite-2025']

async function runAllTestShortcuts() {
  runningAllShortcuts.value = true
  importing.value = true
  selectedFile.value = null
  formPanelRef.value?.resetFile()
  preview.value = null
  result.value = null

  for (const alias of ALL_SHORTCUTS_ORDER) {
    const shortcut = testShortcuts.value.find((item) => item.alias === alias)
    if (!shortcut?.available) continue
    runningShortcutAlias.value = alias
    if (shortcut) {
      importType.value = shortcut.import_type as 'gestion' | 'comptabilite'
      applyDefaultComparisonRange(shortcut.file_name ?? undefined)
    }
    const comparisonWindow = {
      comparison_start_date: comparisonStartDate.value || undefined,
      comparison_end_date: comparisonEndDate.value || undefined,
    }
    try {
      const run = await importTestShortcutApi(alias, comparisonWindow)
      syncRunState(run)
      const hasFailed = run.status === 'failed'
      const hasIssues = Boolean(hasFailed || (run.summary && (run.summary.errors.length > 0 || run.summary.warnings.length > 0)))
      toast.add({
        severity: hasFailed ? 'error' : hasIssues ? 'warn' : 'success',
        summary: `${shortcut.label} : ${hasFailed ? t('import.failed') : hasIssues ? t('import.completed_with_issues') : t('import.success')}`,
        life: hasFailed ? 6000 : 3500,
      })
      if (hasFailed) break
    } catch (error: unknown) {
      toast.add({ severity: 'error', summary: `${shortcut.label} : ${getImportErrorSummary(error)}`, life: 6000 })
      break
    }
  }

  runningShortcutAlias.value = null
  runningAllShortcuts.value = false
  importing.value = false
  await loadTestShortcuts()
}

watch(importType, () => {
  resetImportFlow()
  applyDefaultComparisonRange()
})

watch([comparisonStartDate, comparisonEndDate], () => {
  if (preview.value !== null) resetImportFlow()
})

onMounted(async () => {
  await loadSettings()
  await loadTestShortcuts()
})
</script>

<style>
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

.import-comparison-window-card {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
  padding: var(--app-space-4);
  border: 1px solid var(--app-surface-border);
  border-radius: var(--app-radius-md);
  background: linear-gradient(180deg, var(--app-surface-bg), var(--app-surface-muted));
}

.import-comparison-window-grid {
  display: grid;
  gap: var(--app-space-3);
  grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
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

.import-action-hint--warning {
  color: color-mix(in srgb, var(--p-amber-700) 78%, var(--p-text-color) 22%);
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

.import-result-banner-errors {
  padding-top: var(--app-space-1);
  border-top: 1px solid currentColor;
}

.import-result-banner-errors .import-errors {
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

.import-surface-shell {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.import-preview-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr));
  gap: var(--app-space-3);
  margin-bottom: var(--app-space-3);
}

.import-preview-overview-card {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: var(--app-space-3);
  border: 1px solid var(--app-surface-border);
  border-radius: var(--app-radius-md);
  background: linear-gradient(180deg, var(--app-surface-bg), var(--app-surface-muted));
}

.import-preview-overview-card__label {
  color: var(--p-text-muted-color);
  font-size: 0.85rem;
}

.import-preview-overview-card__value {
  font-size: 1.3rem;
}

.import-preview-overview-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--app-space-3);
  margin-bottom: var(--app-space-3);
}

.import-preview-overview-meta .import-preview-state {
  margin: 0;
}

.import-preview-inline-alert {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--app-space-3);
  margin-bottom: var(--app-space-4);
  padding: var(--app-space-3) var(--app-space-4);
  border: 1px solid color-mix(in srgb, var(--p-amber-500) 35%, var(--app-surface-border) 65%);
  border-radius: var(--app-radius-md);
  background: color-mix(in srgb, var(--p-amber-500) 10%, var(--app-surface-bg) 90%);
}

.import-preview-tabs {
  display: inline-flex;
  gap: var(--app-space-2);
  margin-bottom: var(--app-space-4);
  padding: 0.25rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--app-surface-muted) 86%, var(--app-surface-bg) 14%);
}

.import-preview-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.55rem 0.95rem;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: var(--p-text-muted-color);
  cursor: pointer;
  font: inherit;
}

.import-preview-tab--active {
  background: var(--app-surface-bg);
  color: var(--p-text-color);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}

.import-preview-tab__count {
  min-width: 1.4rem;
  padding: 0.1rem 0.35rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--app-surface-border) 28%, transparent 72%);
  text-align: center;
  font-size: 0.8rem;
}

.import-summary-grid,
.import-result-list {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
}

.import-inline-actions {
  justify-content: flex-start;
}

.import-summary-grid--compact {
  gap: var(--app-space-2);
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

.import-operation-metrics--inline {
  flex-wrap: wrap;
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

.import-sheet-list {
  margin-top: var(--app-space-5);
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.import-section-eyebrow {
  margin: 0 0 var(--app-space-1);
  color: var(--p-text-muted-color);
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.import-comparison-block {
  margin-top: var(--app-space-5);
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.import-diagnostic-block {
  margin-top: var(--app-space-5);
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
}

.import-blocked-guidance {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
  margin-top: var(--app-space-4);
  padding: var(--app-space-4);
  border: 1px solid color-mix(in srgb, var(--p-red-500) 22%, var(--app-surface-border) 78%);
  border-radius: var(--app-radius-md);
  background: color-mix(in srgb, var(--p-red-500) 7%, var(--app-surface-bg) 93%);
}

.import-blocked-guidance__steps {
  margin: 0;
  padding-left: 1rem;
  color: var(--p-text-color);
}

.import-operation-block {
  margin-top: var(--app-space-5);
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.import-operation-metrics {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--app-space-2);
}

.import-operation-metric {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.65rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--app-surface-muted) 88%, var(--app-surface-bg) 12%);
  color: var(--p-text-muted-color);
  font-size: 0.84rem;
}

.import-operation-metric--success {
  color: color-mix(in srgb, var(--p-green-700) 74%, var(--p-text-color) 26%);
}

.import-operation-metric--muted {
  color: var(--p-text-muted-color);
}

.import-operation-metric--danger {
  color: var(--p-red-500);
}

.import-operation-toolbar {
  display: grid;
  gap: var(--app-space-3);
  grid-template-columns: minmax(18rem, 2fr) repeat(2, minmax(12rem, 1fr));
}

.import-operation-toolbar__search {
  min-width: 0;
}

.import-operation-table-wrap {
  overflow-x: auto;
  border: 1px solid var(--app-surface-border);
  border-radius: var(--app-radius-md);
  background: linear-gradient(180deg, var(--app-surface-bg), var(--app-surface-muted));
}

.import-operation-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 48rem;
}

.import-operation-table th,
.import-operation-table td {
  padding: 0.9rem 1rem;
  text-align: left;
  border-bottom: 1px solid var(--app-surface-border);
  vertical-align: top;
}

.import-operation-table thead th {
  background: color-mix(in srgb, var(--app-surface-muted) 72%, var(--app-surface-bg) 28%);
  font-size: 0.84rem;
}

.import-operation-table tbody:last-child tr:last-child td {
  border-bottom: none;
}

.import-operation-table__expander-column {
  width: 6.5rem;
}

.import-operation-sort {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0;
  border: none;
  background: transparent;
  color: inherit;
  font: inherit;
  cursor: pointer;
}

.import-operation-sort__indicator {
  min-width: 0.75rem;
  color: var(--p-text-muted-color);
}

.import-operation-group-row th {
  padding-block: 0.7rem;
  background: color-mix(in srgb, var(--app-surface-border) 24%, var(--app-surface-bg) 76%);
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.import-operation-group-row__content {
  display: flex;
  justify-content: space-between;
  gap: var(--app-space-3);
  align-items: center;
}

.import-operation-group-row__count {
  color: var(--p-text-muted-color);
  text-transform: none;
  letter-spacing: normal;
}

.import-operation-row:hover td {
  background: color-mix(in srgb, var(--app-surface-muted) 70%, transparent 30%);
}

.import-operation-toggle {
  padding: 0.32rem 0.6rem;
  border: 1px solid var(--app-surface-border);
  border-radius: 999px;
  background: transparent;
  color: var(--p-text-color);
  cursor: pointer;
  font-size: 0.82rem;
}

.import-operation-summary-cell {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.import-operation-summary-cell__meta,
.import-operation-status-stack__meta {
  color: var(--p-text-muted-color);
  font-size: 0.82rem;
}

.import-operation-status-stack {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.import-operation-badge {
  display: inline-flex;
  width: fit-content;
  align-items: center;
  padding: 0.25rem 0.55rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;
}

.import-operation-badge--default {
  background: color-mix(in srgb, var(--app-surface-border) 24%, var(--app-surface-bg) 76%);
  color: var(--p-text-color);
}

.import-operation-badge--success {
  background: color-mix(in srgb, var(--p-green-500) 12%, var(--app-surface-bg) 88%);
  color: color-mix(in srgb, var(--p-green-700) 78%, var(--p-text-color) 22%);
}

.import-operation-badge--warning {
  background: color-mix(in srgb, var(--p-amber-500) 14%, var(--app-surface-bg) 86%);
  color: var(--p-amber-700);
}

.import-operation-badge--danger {
  background: color-mix(in srgb, var(--p-red-500) 12%, var(--app-surface-bg) 88%);
  color: var(--p-red-500);
}

.import-operation-badge--muted {
  background: color-mix(in srgb, var(--app-surface-border) 18%, var(--app-surface-bg) 82%);
  color: var(--p-text-muted-color);
}

.import-operation-detail-row td {
  padding-top: 0;
  background: color-mix(in srgb, var(--app-surface-muted) 64%, transparent 36%);
}

.import-operation-detail-card {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
  padding: var(--app-space-3) 0 var(--app-space-2);
}

.import-operation-detail-card__title {
  margin: 0;
  font-size: 1rem;
}

.import-operation-detail-grid {
  display: grid;
  gap: var(--app-space-3);
  grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
}

.import-operation-detail-card__error {
  color: var(--p-red-500);
}

.import-diagnostic-block__header {
  display: flex;
  justify-content: space-between;
  gap: var(--app-space-4);
  align-items: flex-start;
}

.import-comparison-block__header {
  display: flex;
  justify-content: space-between;
  gap: var(--app-space-4);
  align-items: flex-start;
}

.import-comparison-grid {
  display: grid;
  gap: var(--app-space-3);
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
}

.import-comparison-card {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
  padding: var(--app-space-4);
  border: 1px solid var(--app-surface-border);
  border-radius: var(--app-radius-md);
  background: linear-gradient(180deg, var(--app-surface-bg), var(--app-surface-muted));
}

.import-comparison-detail-block {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-2);
}

.import-comparison-detail-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--app-space-2);
}

.import-comparison-detail-item {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-2);
  padding: var(--app-space-3);
  border-radius: var(--app-radius-md);
  background: rgba(148, 163, 184, 0.08);
}

.import-comparison-detail-fields {
  display: flex;
  flex-wrap: wrap;
  gap: var(--app-space-2);
}

.import-comparison-detail-field {
  font-size: 0.82rem;
  color: var(--app-text-muted);
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

@media (max-width: 720px) {
  .import-preview-inline-alert {
    flex-direction: column;
    align-items: stretch;
  }

  .import-comparison-block__header,
  .import-sheet-card__header,
  .import-diagnostic-block__header {
    flex-direction: column;
  }

  .import-sheet-card__stats {
    align-items: flex-start;
  }

  .import-operation-toolbar {
    grid-template-columns: 1fr;
  }

  .import-operation-metrics {
    justify-content: flex-start;
  }
}

:global(html.dark-mode) .import-chip--danger {
  color: var(--p-red-100);
}
</style>

