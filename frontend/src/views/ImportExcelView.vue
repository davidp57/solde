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

          <!-- Submit -->
          <Button
            :label="t('import.submit')"
            icon="pi pi-check"
            :loading="importing"
            :disabled="!selectedFile"
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
import { useToast } from 'primevue/usetoast'
import {
  importGestionFileApi,
  importComptabiliteFileApi,
  type ImportResult,
} from '../api/accounting'

const { t } = useI18n()
const toast = useToast()

const importType = ref<'gestion' | 'comptabilite'>('gestion')
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const importing = ref(false)
const result = ref<ImportResult | null>(null)

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
  result.value = null
}

async function doImport() {
  if (!selectedFile.value) {
    toast.add({ severity: 'warn', summary: t('import.file_required'), life: 3000 })
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
    toast.add({ severity: 'success', summary: t('import.success'), life: 3000 })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  } finally {
    importing.value = false
  }
}
</script>
