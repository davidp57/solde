<template>
  <AppPanel :title="t('import.result_title')" dense>
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
          <li v-for="(warning, idx) in result.warnings" :key="`result-warning-${idx}`">
            {{ warning }}
          </li>
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
        <article v-for="sheet in result.sheets" :key="sheet.name" class="import-sheet-card">
          <div class="import-sheet-card__header">
            <div>
              <h4 class="import-sheet-card__title">{{ sheet.name }}</h4>
              <p class="import-sheet-card__meta">{{ importSheetKindLabel(sheet.kind) }}</p>
            </div>
            <div class="import-sheet-card__stats">
              <span class="import-sheet-card__stat import-sheet-card__stat--success">
                {{ t('import.sheet_imported_rows', { count: sheet.imported_rows }) }}
              </span>
              <span
                v-if="sheet.ignored_rows"
                class="import-sheet-card__stat import-sheet-card__stat--warning"
              >
                {{ t('import.sheet_ignored_rows', { count: sheet.ignored_rows }) }}
              </span>
              <span
                v-if="sheet.blocked_rows"
                class="import-sheet-card__stat import-sheet-card__stat--danger"
              >
                {{ t('import.sheet_blocked_rows', { count: sheet.blocked_rows }) }}
              </span>
            </div>
          </div>
          <ul v-if="sheet.warnings.length" class="import-warnings">
            <li
              v-for="(warning, idx) in sheet.warnings"
              :key="`${sheet.name}-result-warning-${idx}`"
            >
              {{ warning }}
            </li>
          </ul>
          <ul v-if="sheet.errors.length" class="import-errors">
            <li v-for="(error, idx) in sheet.errors" :key="`${sheet.name}-result-error-${idx}`">
              {{ error }}
            </li>
          </ul>
        </article>
      </div>
    </div>
  </AppPanel>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import AppPanel from '../ui/AppPanel.vue'
import type { ImportResult } from '@/api/accounting'

defineProps<{
  result: ImportResult
}>()

const { t } = useI18n()

function importSheetKindLabel(kind: string) {
  return t(`import.sheet_kind.${kind}`)
}
</script>
