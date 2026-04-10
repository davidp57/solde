<template>
  <div class="import-excel-view p-4">
    <h2 class="text-2xl font-semibold mb-2">{{ t('import.title') }}</h2>
    <p class="text-gray-500 mb-6">{{ t('import.subtitle') }}</p>

    <Card class="max-w-xl">
      <template #content>
        <div class="flex flex-col gap-5">
          <!-- File type selection -->
          <div class="flex flex-col gap-1">
            <label class="font-medium text-sm">{{ t('import.type_label') }}</label>
            <div class="flex gap-4 mt-1">
              <div class="flex items-center gap-2">
                <RadioButton v-model="importType" input-id="type-gestion" value="gestion" />
                <label for="type-gestion">{{ t('import.type_gestion') }}</label>
              </div>
              <div class="flex items-center gap-2">
                <RadioButton v-model="importType" input-id="type-compta" value="comptabilite" />
                <label for="type-compta">{{ t('import.type_comptabilite') }}</label>
              </div>
            </div>
          </div>

          <!-- File picker -->
          <div class="flex flex-col gap-1">
            <label class="font-medium text-sm">{{ t('import.file_label') }}</label>
            <input
              ref="fileInput"
              type="file"
              accept=".xlsx,.xls"
              class="hidden"
              @change="onFileChange"
            />
            <div class="flex items-center gap-3">
              <Button
                :label="t('import.choose_file')"
                icon="pi pi-upload"
                severity="secondary"
                outlined
                @click="fileInput?.click()"
              />
              <span v-if="selectedFile" class="text-sm text-gray-600">{{ selectedFile.name }}</span>
              <span v-else class="text-sm text-gray-400">—</span>
            </div>
          </div>

          <!-- Submit / Preview buttons -->
          <div class="flex gap-3">
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
      </template>
    </Card>

    <!-- Preview -->
    <Card v-if="preview" class="max-w-xl mt-6">
      <template #title>{{ t('import.preview_title') }}</template>
      <template #content>
        <p class="text-sm text-gray-500 mb-3">{{ t('import.preview_subtitle') }}</p>
        <div class="grid grid-cols-2 gap-2 text-sm">
          <div class="flex justify-between border-b border-surface-200 pb-1 col-span-2 md:col-span-1">
            <span>{{ t('import.estimated_contacts') }}</span>
            <span class="font-medium">{{ preview.estimated_contacts }}</span>
          </div>
          <div class="flex justify-between border-b border-surface-200 pb-1 col-span-2 md:col-span-1">
            <span>{{ t('import.estimated_invoices') }}</span>
            <span class="font-medium">{{ preview.estimated_invoices }}</span>
          </div>
          <div class="flex justify-between border-b border-surface-200 pb-1 col-span-2 md:col-span-1">
            <span>{{ t('import.estimated_payments') }}</span>
            <span class="font-medium">{{ preview.estimated_payments }}</span>
          </div>
          <div class="flex justify-between border-b border-surface-200 pb-1 col-span-2 md:col-span-1">
            <span>{{ t('import.estimated_entries') }}</span>
            <span class="font-medium">{{ preview.estimated_entries }}</span>
          </div>
        </div>
        <div v-if="preview.errors.length" class="mt-3">
          <ul class="list-disc list-inside text-sm text-red-600 space-y-1">
            <li v-for="(err, idx) in preview.errors" :key="idx">{{ err }}</li>
          </ul>
        </div>
        <div class="mt-4">
          <Button
            :label="t('import.confirm_import')"
            icon="pi pi-check"
            :loading="importing"
            @click="doImport"
          />
        </div>
      </template>
    </Card>

    <!-- Result -->
    <Card v-if="result" class="max-w-xl mt-6">
      <template #title>{{ t('import.result_title') }}</template>
      <template #content>
        <div class="flex flex-col gap-2">
          <div class="flex justify-between border-b border-surface-200 pb-1">
            <span>{{ t('import.contacts_created') }}</span>
            <span class="font-medium">{{ result.contacts_created }}</span>
          </div>
          <div class="flex justify-between border-b border-surface-200 pb-1">
            <span>{{ t('import.invoices_created') }}</span>
            <span class="font-medium">{{ result.invoices_created }}</span>
          </div>
          <div class="flex justify-between border-b border-surface-200 pb-1">
            <span>{{ t('import.payments_created') }}</span>
            <span class="font-medium">{{ result.payments_created }}</span>
          </div>
          <div class="flex justify-between border-b border-surface-200 pb-1">
            <span>{{ t('import.entries_created') }}</span>
            <span class="font-medium">{{ result.entries_created }}</span>
          </div>
          <div class="flex justify-between border-b border-surface-200 pb-1">
            <span>{{ t('import.cash_created') }}</span>
            <span class="font-medium">{{ result.cash_created }}</span>
          </div>
          <div class="flex justify-between border-b border-surface-200 pb-1">
            <span>{{ t('import.bank_created') }}</span>
            <span class="font-medium">{{ result.bank_created }}</span>
          </div>
          <div class="flex justify-between border-b border-surface-200 pb-1">
            <span>{{ t('import.skipped') }}</span>
            <span class="font-medium">{{ result.skipped }}</span>
          </div>

          <!-- Errors -->
          <div class="mt-2">
            <span class="font-medium text-sm">{{ t('import.errors') }}</span>
            <div v-if="result.errors.length === 0" class="text-gray-400 text-sm mt-1">
              {{ t('import.no_errors') }}
            </div>
            <ul v-else class="mt-1 list-disc list-inside text-sm text-red-600 space-y-1">
              <li v-for="(err, idx) in result.errors" :key="idx">{{ err }}</li>
            </ul>
          </div>
        </div>
      </template>
    </Card>

    <Toast />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Card from 'primevue/card'
import RadioButton from 'primevue/radiobutton'
import Toast from 'primevue/toast'
import { useToast } from 'primevue/usetoast'
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
