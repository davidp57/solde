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
              :label="t('import.preview')"
              icon="pi pi-eye"
              severity="secondary"
              outlined
              :loading="previewing"
              :disabled="!selectedFile"
              @click="doPreview"
            />
            <Button
              :label="t('import.submit')"
              icon="pi pi-check"
              :loading="importing"
              :disabled="!selectedFile"
              @click="doImport"
            />
          </div>
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
              <strong class="import-sheet-card__rows">{{ t('import.sheet_rows', { count: sheet.rows }) }}</strong>
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
            <span>{{ t('import.skipped') }}</span>
            <span class="font-medium">{{ result.skipped }}</span>
          </div>

          <!-- Errors -->
          <div class="import-errors-block">
            <span class="app-field__label">{{ t('import.errors') }}</span>
            <div v-if="result.errors.length === 0" class="app-empty-state import-empty-inline">
              {{ t('import.no_errors') }}
            </div>
            <ul v-else class="import-errors">
              <li v-for="(err, idx) in result.errors" :key="idx">{{ err }}</li>
            </ul>
          </div>
        </div>
    </AppPanel>

    <Toast />
  </AppPage>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import RadioButton from 'primevue/radiobutton'
import Toast from 'primevue/toast'
import { useToast } from 'primevue/usetoast'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import {
  importGestionFileApi,
  importComptabiliteFileApi,
  previewGestionFileApi,
  previewComptabiliteFileApi,
  type ImportResult,
  type PreviewSheetResult,
  type PreviewResult,
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
const canConfirmImport = computed(() => Boolean(selectedFile.value && preview.value?.can_import))

function previewSheetKindLabel(kind: PreviewSheetResult['kind']) {
  return t(`import.sheet_kind.${kind}`)
}

function previewSheetStatusLabel(status: PreviewSheetResult['status']) {
  return t(`import.sheet_status.${status}`)
}

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
  result.value = null
  preview.value = null
}

async function doPreview() {
  if (!selectedFile.value) return
  previewing.value = true
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
  importing.value = true
  result.value = null
  preview.value = null
  try {
    if (importType.value === 'gestion') {
      result.value = await importGestionFileApi(selectedFile.value)
    } else {
      result.value = await importComptabiliteFileApi(selectedFile.value)
    }
    toast.add({ severity: 'success', summary: t('import.success'), life: 3000 })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  } finally {
    importing.value = false
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
