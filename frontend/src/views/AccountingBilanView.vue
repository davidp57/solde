<template>
  <div class="accounting-bilan-view p-4">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-2xl font-semibold">{{ t('bilan.title') }}</h2>
      <div class="flex gap-2 items-center">
        <Select
          v-model="selectedFiscalYear"
          :options="fiscalYears"
          option-label="name"
          option-value="id"
          :placeholder="t('accounting.fiscalYear.name')"
          class="w-48"
          @change="loadBilan"
        />
        <Button
          :label="t('bilan.export_csv')"
          icon="pi pi-download"
          severity="secondary"
          outlined
          @click="downloadCsv"
        />
      </div>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <ProgressSpinner />
    </div>

    <div v-else-if="bilan" class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Actif -->
      <Card>
        <template #header>
          <div class="px-4 pt-4 font-semibold text-lg">{{ t('bilan.actif') }}</div>
        </template>
        <template #content>
          <DataTable :value="bilan.actif" class="text-sm" striped-rows>
            <Column field="account_number" :header="t('accounting.accounts.number')" style="width:8rem" />
            <Column field="account_label" :header="t('accounting.accounts.label')" />
            <Column field="solde" :header="t('accounting.balance.solde')" style="width:9rem" class="text-right font-mono">
              <template #body="{ data }">{{ formatAmount(data.solde) }}</template>
            </Column>
          </DataTable>
          <div class="mt-3 flex justify-end font-semibold text-base border-t pt-2">
            <span>{{ t('bilan.total_actif') }} : {{ formatAmount(bilan.total_actif) }} €</span>
          </div>
        </template>
      </Card>

      <!-- Passif -->
      <Card>
        <template #header>
          <div class="px-4 pt-4 font-semibold text-lg">{{ t('bilan.passif') }}</div>
        </template>
        <template #content>
          <DataTable :value="bilan.passif" class="text-sm" striped-rows>
            <Column field="account_number" :header="t('accounting.accounts.number')" style="width:8rem" />
            <Column field="account_label" :header="t('accounting.accounts.label')" />
            <Column field="solde" :header="t('accounting.balance.solde')" style="width:9rem" class="text-right font-mono">
              <template #body="{ data }">{{ formatAmount(data.solde) }}</template>
            </Column>
          </DataTable>
          <div class="mt-3 flex flex-col items-end gap-1 border-t pt-2">
            <span class="font-semibold text-base">
              {{ t('bilan.total_passif') }} : {{ formatAmount(bilan.total_passif) }} €
            </span>
            <span :class="['text-sm', Number(bilan.resultat) >= 0 ? 'text-green-600' : 'text-red-600']">
              {{ t('bilan.resultat') }} : {{ formatAmount(bilan.resultat) }} €
            </span>
          </div>
        </template>
      </Card>
    </div>

    <div v-else class="text-gray-400 mt-8 text-center">{{ t('bilan.empty') }}</div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { getBilanApi, getExportCsvUrl, listFiscalYearsApi } from '../api/accounting'
import type { BilanRead, FiscalYearRead } from '../api/accounting'

const { t } = useI18n()

const bilan = ref<BilanRead | null>(null)
const loading = ref(false)
const fiscalYears = ref<FiscalYearRead[]>([])
const selectedFiscalYear = ref<number | undefined>(undefined)

function formatAmount(val: string | number): string {
  return Number(val).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function loadBilan() {
  loading.value = true
  try {
    bilan.value = await getBilanApi(selectedFiscalYear.value)
  } finally {
    loading.value = false
  }
}

function downloadCsv() {
  const url = getExportCsvUrl('bilan', {
    fiscal_year_id: selectedFiscalYear.value,
  })
  window.open(url, '_blank')
}

onMounted(async () => {
  fiscalYears.value = await listFiscalYearsApi()
  await loadBilan()
})
</script>
