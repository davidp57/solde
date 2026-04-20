<template>
  <AppPage>
    <AppPageHeader
      :eyebrow="t('ui.page.collection_eyebrow')"
      :title="t('import.history_page_title')"
      :subtitle="t('import.history_page_subtitle')"
    >
      <template #actions>
        <Button
          :label="t('import.back_to_import')"
          icon="pi pi-arrow-left"
          severity="secondary"
          outlined
          @click="router.push('/import/excel')"
        />
      </template>
    </AppPageHeader>

    <AppPanel :title="t('import.history_title')" :subtitle="t('import.history_subtitle')" dense>
      <div v-if="loading" class="app-empty-state import-empty-inline">
        {{ t('common.loading') }}
      </div>
      <div
        v-else-if="importHistory.length === 0"
        data-testid="import-history"
        class="app-empty-state import-empty-inline"
      >
        {{ t('import.no_history') }}
      </div>
      <div v-else data-testid="import-history" class="import-sheet-list">
        <article
          v-for="historyItem in importHistory"
          :key="`${historyItem.kind}-${historyItem.id}`"
          class="import-sheet-card"
        >
          <div class="import-sheet-card__header">
            <div>
              <h4 class="import-sheet-card__title">
                {{ historyItem.file_name ?? t('import.unknown_file') }}
              </h4>
              <p class="import-sheet-card__meta">
                {{ historyStatusLabel(historyItem.status) }} · {{ historyItem.import_type }}
              </p>
            </div>
            <div class="import-sheet-card__stats">
              <span class="import-sheet-card__stat">{{
                historyItem.created_at ? formatDateTime(historyItem.created_at) : '—'
              }}</span>
            </div>
          </div>

          <div v-if="historyItem.summary" class="import-summary-grid import-summary-grid--compact">
            <div class="import-summary-row">
              <span>{{ t('import.invoices_created') }}</span>
              <strong>{{ historyItem.summary.invoices_created }}</strong>
            </div>
            <div class="import-summary-row">
              <span>{{ t('import.payments_created') }}</span>
              <strong>{{ historyItem.summary.payments_created }}</strong>
            </div>
            <div class="import-summary-row">
              <span>{{ t('import.entries_created') }}</span>
              <strong>{{ historyItem.summary.entries_created }}</strong>
            </div>
            <div class="import-summary-row">
              <span>{{ t('import.ignored_rows') }}</span>
              <strong>{{ historyItem.summary.ignored_rows }}</strong>
            </div>
            <div class="import-summary-row">
              <span>{{ t('import.blocked_rows') }}</span>
              <strong>{{ historyItem.summary.blocked_rows }}</strong>
            </div>
          </div>

          <div v-if="historyItem.summary?.errors?.length" class="import-sheet-card__section">
            <div class="import-section-header">
              <span class="app-field__label">
                {{ t('import.history_errors_title', { count: historyItem.summary.errors.length }) }}
              </span>
              <button
                v-if="historyItem.summary.errors.length > HISTORY_SECTION_PREVIEW_LIMIT"
                type="button"
                class="import-inline-toggle"
                :data-testid="`history-errors-toggle-${historyItem.id}`"
                @click="toggleExpandedSection(historySectionKey(historyItem.id, 'errors'))"
              >
                {{
                  historySectionToggleLabel(
                    historyItem.id,
                    'errors',
                    historyItem.summary.errors.length,
                  )
                }}
              </button>
            </div>
            <ul class="import-errors">
              <li
                v-for="(error, index) in visibleHistoryItems(
                  historyItem.summary.errors,
                  historyItem.id,
                  'errors',
                )"
                :key="`${historyItem.id}-history-error-${index}`"
              >
                {{ error }}
              </li>
            </ul>
          </div>

          <div
            v-if="historyItem.summary?.created_objects?.length"
            class="import-sheet-card__section"
          >
            <div class="import-section-header">
              <span class="app-field__label">
                {{
                  t('import.history_created_objects_title', {
                    count: historyItem.summary.created_objects.length,
                  })
                }}
              </span>
              <button
                v-if="historyItem.summary.created_objects.length > HISTORY_SECTION_PREVIEW_LIMIT"
                type="button"
                class="import-inline-toggle"
                :data-testid="`history-created-toggle-${historyItem.id}`"
                @click="toggleExpandedSection(historySectionKey(historyItem.id, 'created'))"
              >
                {{
                  historySectionToggleLabel(
                    historyItem.id,
                    'created',
                    historyItem.summary.created_objects.length,
                  )
                }}
              </button>
            </div>
            <ul class="import-warnings">
              <li
                v-for="(createdObject, index) in visibleHistoryItems(
                  historyItem.summary.created_objects,
                  historyItem.id,
                  'created',
                )"
                :key="`${historyItem.id}-history-object-${index}`"
              >
                {{ createdObject.reference ?? createdObject.object_type }}
              </li>
            </ul>
          </div>

          <div
            v-if="historyItem.kind === 'run' && historyItem.operations.length"
            class="import-sheet-card__section"
          >
            <div class="import-section-header">
              <span class="app-field__label">
                {{ t('import.history_operations_title', { count: historyItem.operations.length }) }}
              </span>
              <button
                v-if="historyItem.operations.length > HISTORY_SECTION_PREVIEW_LIMIT"
                type="button"
                class="import-inline-toggle"
                :data-testid="`history-operations-toggle-${historyItem.id}`"
                @click="toggleExpandedSection(historySectionKey(historyItem.id, 'operations'))"
              >
                {{
                  historySectionToggleLabel(
                    historyItem.id,
                    'operations',
                    historyItem.operations.length,
                  )
                }}
              </button>
            </div>
            <ul class="import-comparison-detail-list">
              <li
                v-for="operation in visibleHistoryItems(
                  historyItem.operations,
                  historyItem.id,
                  'operations',
                )"
                :key="`${historyItem.id}-history-operation-${operation.id}`"
                class="import-comparison-detail-item"
              >
                <strong>{{ operation.title }}</strong>
                <span class="import-comparison-detail-field">
                  {{ t(`import.operation_status.${operation.status}`) }}
                </span>
              </li>
            </ul>
          </div>

          <div
            v-if="historyItem.kind === 'run' && (historyItem.can_undo || historyItem.can_redo)"
            class="app-form-actions import-inline-actions"
          >
            <Button
              v-if="historyItem.can_undo"
              :label="t('import.undo_run')"
              severity="secondary"
              outlined
              :loading="busyRunId === historyItem.id"
              @click="undoRun(historyItem.id)"
            />
            <Button
              v-if="historyItem.can_redo"
              :label="t('import.redo_run')"
              severity="secondary"
              outlined
              :loading="busyRunId === historyItem.id"
              @click="redoRun(historyItem.id)"
            />
          </div>
        </article>
      </div>
    </AppPanel>

    <Toast />
  </AppPage>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Toast from 'primevue/toast'
import { useToast } from 'primevue/usetoast'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import {
  listImportHistoryApi,
  redoImportRunApi,
  type ImportHistoryItem,
  undoImportRunApi,
} from '../api/accounting'

const { t } = useI18n()
const toast = useToast()
const router = useRouter()

const importHistory = ref<ImportHistoryItem[]>([])
const busyRunId = ref<number | null>(null)
const loading = ref(false)
const expandedSections = ref<string[]>([])

const HISTORY_SECTION_PREVIEW_LIMIT = 8

function historySectionKey(historyItemId: number, section: string) {
  return `${historyItemId}:${section}`
}

function isSectionExpanded(sectionKey: string) {
  return expandedSections.value.includes(sectionKey)
}

function toggleExpandedSection(sectionKey: string) {
  if (isSectionExpanded(sectionKey)) {
    expandedSections.value = expandedSections.value.filter((key) => key !== sectionKey)
    return
  }
  expandedSections.value = [...expandedSections.value, sectionKey]
}

function visibleHistoryItems<T>(items: T[], historyItemId: number, section: string) {
  const sectionKey = historySectionKey(historyItemId, section)
  if (isSectionExpanded(sectionKey)) {
    return items
  }
  return items.slice(0, HISTORY_SECTION_PREVIEW_LIMIT)
}

function historySectionToggleLabel(historyItemId: number, section: string, totalCount: number) {
  const sectionKey = historySectionKey(historyItemId, section)
  if (isSectionExpanded(sectionKey)) {
    return t('import.history_show_less')
  }
  return t('import.history_show_more', {
    shown: Math.min(HISTORY_SECTION_PREVIEW_LIMIT, totalCount),
    total: totalCount,
  })
}

function normalizeHistoryStatus(status: string) {
  if (status === 'success') {
    return 'completed'
  }
  return status
}

function historyStatusLabel(status: string) {
  const normalizedStatus = normalizeHistoryStatus(status)
  const translated = t(`import.run_status.${normalizedStatus}`)
  return translated === `import.run_status.${normalizedStatus}` ? normalizedStatus : translated
}

function formatDateTime(value: string) {
  try {
    return new Intl.DateTimeFormat('fr-FR', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(new Date(value))
  } catch {
    return value
  }
}

function getImportErrorSummary(error: unknown): string {
  const responseData = (error as { response?: { data?: unknown } }).response?.data
  const detail =
    responseData && typeof responseData === 'object'
      ? (responseData as { detail?: unknown }).detail
      : undefined

  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }

  const message = (error as { message?: unknown }).message
  if (typeof message === 'string' && message.trim()) {
    return message
  }

  return t('common.error.unknown')
}

async function loadImportHistory() {
  loading.value = true
  try {
    importHistory.value = await listImportHistoryApi()
  } catch (error: unknown) {
    importHistory.value = []
    toast.add({ severity: 'error', summary: getImportErrorSummary(error), life: 5000 })
  } finally {
    loading.value = false
  }
}

async function undoRun(runId: number) {
  busyRunId.value = runId
  try {
    await undoImportRunApi(runId)
    await loadImportHistory()
  } catch (error: unknown) {
    toast.add({ severity: 'error', summary: getImportErrorSummary(error), life: 5000 })
  } finally {
    busyRunId.value = null
  }
}

async function redoRun(runId: number) {
  busyRunId.value = runId
  try {
    await redoImportRunApi(runId)
    await loadImportHistory()
  } catch (error: unknown) {
    toast.add({ severity: 'error', summary: getImportErrorSummary(error), life: 5000 })
  } finally {
    busyRunId.value = null
  }
}

onMounted(async () => {
  await loadImportHistory()
})
</script>

<style scoped>
.import-empty-inline {
  min-height: 12rem;
}

.import-inline-actions {
  justify-content: flex-start;
}

.import-sheet-list {
  display: grid;
  gap: var(--app-space-4);
}

.import-summary-grid {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
}

.import-summary-grid--compact {
  gap: var(--app-space-2);
}

.import-summary-row {
  display: flex;
  justify-content: space-between;
  gap: var(--app-space-3);
}

.import-sheet-card {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
  padding: var(--app-space-4);
  border: 1px solid var(--app-surface-border);
  border-radius: var(--app-radius-md);
  background: linear-gradient(180deg, var(--app-surface-bg), var(--app-surface-muted));
}

.import-sheet-card__header {
  display: flex;
  justify-content: space-between;
  gap: var(--app-space-3);
  align-items: flex-start;
}

.import-sheet-card__title {
  margin: 0;
}

.import-sheet-card__meta {
  margin: 0.2rem 0 0;
  color: var(--p-text-muted-color);
}

.import-sheet-card__stats {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--app-space-2);
}

.import-sheet-card__stat {
  display: inline-flex;
  align-items: center;
  padding: 0.3rem 0.6rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--app-surface-border) 18%, var(--app-surface-bg) 82%);
}

.import-sheet-card__section {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-2);
}

.import-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-3);
}

.import-inline-toggle {
  border: none;
  background: transparent;
  color: var(--p-primary-color);
  cursor: pointer;
  font: inherit;
  padding: 0;
}

.import-errors,
.import-warnings,
.import-comparison-detail-list {
  margin: 0;
  padding-left: 1rem;
}

.import-comparison-detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.import-comparison-detail-field {
  color: var(--p-text-muted-color);
}

@media (max-width: 720px) {
  .import-sheet-card__header {
    flex-direction: column;
  }

  .import-sheet-card__stats {
    justify-content: flex-start;
  }
}
</style>
