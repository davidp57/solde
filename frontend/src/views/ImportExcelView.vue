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
        <div v-if="preview.errors.length" class="import-errors">
          <ul>
            <li v-for="(err, idx) in preview.errors" :key="idx">{{ err }}</li>
          </ul>
        </div>
        <div class="app-form-actions import-confirm">
          <Button
            :label="t('import.confirm_import')"
            icon="pi pi-check"
            :loading="importing"
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
import { ref } from 'vue'
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

.import-errors,
.import-errors ul {
  margin: 0;
  padding-left: 1rem;
  color: var(--p-red-500);
  font-size: 0.92rem;
}

.import-confirm,
.import-errors-block {
  margin-top: var(--app-space-4);
}

.import-empty-inline {
  padding: var(--app-space-3) 0 0;
  text-align: left;
}
</style>
