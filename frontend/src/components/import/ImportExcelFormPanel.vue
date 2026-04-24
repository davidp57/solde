<template>
  <AppPanel :title="t('import.type_label')" :subtitle="t('import.preview_subtitle')">
    <div class="import-form">
      <!-- File type selection -->
      <div class="app-field">
        <label class="app-field__label">{{ t('import.type_label') }}</label>
        <div class="import-type-row">
          <div class="import-radio-item">
            <RadioButton
              :model-value="importType"
              input-id="type-gestion"
              value="gestion"
              @update:model-value="emit('update:importType', $event)"
            />
            <label for="type-gestion">{{ t('import.type_gestion') }}</label>
          </div>
          <div class="import-radio-item">
            <RadioButton
              :model-value="importType"
              input-id="type-compta"
              value="comptabilite"
              @update:model-value="emit('update:importType', $event)"
            />
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
        <input ref="fileInput" type="file" accept=".xlsx,.xls" hidden @change="onFileChange" />
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

      <div v-if="selectedFile" class="import-comparison-window-card">
        <div>
          <p class="import-section-eyebrow">{{ t('import.comparison_window_label') }}</p>
          <h3 class="import-guidance-card__title">{{ t('import.comparison_window_title') }}</h3>
          <p class="import-action-hint">{{ t('import.comparison_window_subtitle') }}</p>
        </div>
        <div class="import-comparison-window-grid">
          <div class="app-field">
            <label for="comparison-start-date" class="app-field__label">
              {{ t('import.comparison_window_start') }}
            </label>
            <input
              id="comparison-start-date"
              data-testid="comparison-start-date"
              :value="comparisonStartDate"
              type="date"
              class="app-input"
              @input="emit('update:comparisonStartDate', ($event.target as HTMLInputElement).value)"
            />
          </div>
          <div class="app-field">
            <label for="comparison-end-date" class="app-field__label">
              {{ t('import.comparison_window_end') }}
            </label>
            <input
              id="comparison-end-date"
              data-testid="comparison-end-date"
              :value="comparisonEndDate"
              type="date"
              class="app-input"
              @input="emit('update:comparisonEndDate', ($event.target as HTMLInputElement).value)"
            />
          </div>
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
          @click="emit('preview-click')"
        />
        <Button
          data-testid="primary-import-button"
          :label="t('import.submit')"
          icon="pi pi-check"
          :loading="importing"
          :disabled="!canConfirmImport || !activeRun?.can_execute"
          @click="emit('import-click')"
        />
      </div>
      <p
        class="import-action-hint"
        :class="{ 'import-action-hint--warning': hasPreviewWarnings && preview?.can_import }"
      >
        {{ importActionHint }}
      </p>
      <div
        v-if="result"
        data-testid="import-result-banner"
        class="import-result-banner"
        :class="resultHasIssues ? 'import-result-banner--warning' : 'import-result-banner--success'"
      >
        <strong>{{ resultStateMessage }}</strong>
        <p>{{ resultStateDetail }}</p>
        <div
          v-if="activeRun?.status === 'failed' && result.errors.length"
          data-testid="import-result-banner-errors"
          class="import-result-banner-errors"
        >
          <ul class="import-errors">
            <li v-for="(err, idx) in result.errors" :key="`banner-error-${idx}`">{{ err }}</li>
          </ul>
        </div>
      </div>
    </div>
  </AppPanel>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import RadioButton from 'primevue/radiobutton'
import AppPanel from '../ui/AppPanel.vue'
import type { ImportResult, ImportRunRead, PreviewResult } from '@/api/accounting'

interface Props {
  importType: 'gestion' | 'comptabilite'
  comparisonStartDate: string
  comparisonEndDate: string
  selectedFile: File | null
  preview: PreviewResult | null
  result: ImportResult | null
  activeRun: ImportRunRead | null
  importing: boolean
  previewing: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:importType': [value: 'gestion' | 'comptabilite']
  'update:comparisonStartDate': [value: string]
  'update:comparisonEndDate': [value: string]
  'file-selected': [file: File | null]
  'preview-click': []
  'import-click': []
}>()

const { t } = useI18n()
const fileInput = ref<HTMLInputElement | null>(null)

const previewState = computed<'ready' | 'noop' | 'blocked'>(() => {
  if (!props.preview) return 'blocked'
  if (props.preview.can_import) return 'ready'
  if (props.preview.errors.length === 0) return 'noop'
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

const hasPreviewWarnings = computed(() =>
  Boolean(
    props.preview &&
    (props.preview.warnings.length > 0 ||
      props.preview.warning_details.length > 0 ||
      props.preview.sheets.some(
        (sheet) => sheet.warnings.length > 0 || sheet.warning_details.length > 0,
      )),
  ),
)

const canConfirmImport = computed(() =>
  Boolean(props.selectedFile && props.preview?.can_import && props.activeRun?.can_execute !== false),
)

const importActionHint = computed(() => {
  if (!props.selectedFile) return t('import.file_required')
  if (!props.preview) return t('import.preview_required')
  if (!props.preview.can_import) return t('import.preview_blocked')
  if (hasPreviewWarnings.value) return t('import.warning_review_hint')
  return t('import.import_ready')
})

const resultCreatedCount = computed(() => {
  if (!props.result) return 0
  return (
    props.result.contacts_created +
    props.result.invoices_created +
    props.result.payments_created +
    props.result.salaries_created +
    props.result.entries_created +
    props.result.cash_created +
    props.result.bank_created
  )
})

const resultHasIssues = computed(() =>
  Boolean(
    props.result &&
    (props.activeRun?.status === 'failed' ||
      props.result.errors.length > 0 ||
      props.result.warnings.length > 0),
  ),
)

const resultStateMessage = computed(() => {
  if (!props.result) return ''
  if (props.activeRun?.status === 'failed') return t('import.failed')
  return resultHasIssues.value ? t('import.completed_with_issues') : t('import.success')
})

const resultStateDetail = computed(() => {
  if (!props.result) return ''
  if (props.activeRun?.status === 'failed') {
    return t('import.result_failed_hint', {
      count: resultCreatedCount.value,
      errors: props.result.errors.length,
    })
  }
  return t('import.result_persistent_hint', {
    count: resultCreatedCount.value,
    ignored: props.result.ignored_rows,
    blocked: props.result.blocked_rows,
  })
})

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  emit('file-selected', input.files?.[0] ?? null)
  input.value = ''
}

function resetFile() {
  if (fileInput.value) fileInput.value.value = ''
}

defineExpose({ resetFile })
</script>
