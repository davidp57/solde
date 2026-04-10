<template>
  <AppPage width="wide">
    <AppPageHeader :eyebrow="t('ui.page.accounting_eyebrow')" :title="t('bilan.title')">
      <template #actions>
        <div class="app-page-header__actions">
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
      </template>
    </AppPageHeader>

    <div v-if="loading" class="bilan-loading">
      <ProgressSpinner />
    </div>

    <div v-else-if="bilan" class="bilan-grid">
      <!-- Actif -->
      <AppPanel :title="t('bilan.actif')" dense>
          <DataTable :value="bilan.actif" class="app-data-table" striped-rows size="small" row-hover>
            <Column field="account_number" :header="t('accounting.accounts.number')" style="width:8rem" />
            <Column field="account_label" :header="t('accounting.accounts.label')" />
            <Column field="solde" :header="t('accounting.balance.solde')" style="width:9rem" class="app-money">
              <template #body="{ data }">{{ formatAmount(data.solde) }}</template>
            </Column>
          </DataTable>
          <div class="mt-3 flex justify-end font-semibold text-base border-t pt-2">
            <span>{{ t('bilan.total_actif') }} : {{ formatAmount(bilan.total_actif) }} €</span>
          </div>
      </AppPanel>

      <!-- Passif -->
      <AppPanel :title="t('bilan.passif')" dense>
          <DataTable :value="bilan.passif" class="app-data-table" striped-rows size="small" row-hover>
            <Column field="account_number" :header="t('accounting.accounts.number')" style="width:8rem" />
            <Column field="account_label" :header="t('accounting.accounts.label')" />
            <Column field="solde" :header="t('accounting.balance.solde')" style="width:9rem" class="app-money">
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
      </AppPanel>
    </div>

    <div v-else class="app-empty-state">{{ t('bilan.empty') }}</div>
  </AppPage>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import ProgressSpinner from 'primevue/progressspinner'
import Select from 'primevue/select'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
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

<style scoped>
.bilan-loading {
  display: flex;
  justify-content: center;
  padding: 4rem 0;
}

.bilan-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--app-space-5);
}

@media (max-width: 900px) {
  .bilan-grid {
    grid-template-columns: 1fr;
  }
}
</style>
