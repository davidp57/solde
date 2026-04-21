<template>
  <AppPage width="wide">
    <AppPageHeader :eyebrow="t('ui.page.accounting_eyebrow')" :title="t('bilan.title')">
      <template #actions>
        <div class="app-page-header__actions">
          <Select
            v-model="fiscalYearId"
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
        <DataTable
          :value="bilan.actif"
          class="app-data-table"
          striped-rows
          paginator
          :rows="20"
          :rows-per-page-options="[20, 50, 100, 500]"
          size="small"
          row-hover
        >
          <Column
            field="account_number"
            :header="t('accounting.accounts.number')"
            style="width: 8rem"
          />
          <Column field="account_label" :header="t('accounting.accounts.label')" />
          <Column
            field="solde"
            :header="t('accounting.balance.solde')"
            style="width: 9rem"
            class="app-money"
          >
            <template #body="{ data }">{{ formatAccountingAmount(data.solde) }}</template>
          </Column>
        </DataTable>
        <div class="mt-3 flex justify-end font-semibold text-base border-t pt-2">
          <span>{{ t('bilan.total_actif') }} : {{ formatAccountingAmount(bilan.total_actif) }} €</span>
        </div>
      </AppPanel>

      <!-- Passif -->
      <AppPanel :title="t('bilan.passif')" dense>
        <DataTable
          :value="bilan.passif"
          class="app-data-table"
          striped-rows
          paginator
          :rows="20"
          :rows-per-page-options="[20, 50, 100, 500]"
          size="small"
          row-hover
        >
          <Column
            field="account_number"
            :header="t('accounting.accounts.number')"
            style="width: 8rem"
          />
          <Column field="account_label" :header="t('accounting.accounts.label')" />
          <Column
            field="solde"
            :header="t('accounting.balance.solde')"
            style="width: 9rem"
            class="app-money"
          >
            <template #body="{ data }">{{ formatAccountingAmount(data.solde) }}</template>
          </Column>
        </DataTable>
        <div class="mt-3 flex flex-col items-end gap-1 border-t pt-2">
          <span class="font-semibold text-base">
            {{ t('bilan.total_passif') }} : {{ formatAccountingAmount(bilan.total_passif) }} €
          </span>
          <span
            :class="['text-sm', Number(bilan.resultat) >= 0 ? 'text-green-600' : 'text-red-600']"
          >
            {{ t('bilan.resultat') }} : {{ formatAccountingAmount(bilan.resultat) }} €
          </span>
        </div>
      </AppPanel>
    </div>

    <div v-else class="app-empty-state">{{ t('bilan.empty') }}</div>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import ProgressSpinner from 'primevue/progressspinner'
import Select from 'primevue/select'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import { getBilanApi, getExportCsvUrl } from '../api/accounting'
import type { BilanRead } from '../api/accounting'
import { useFiscalYearStore } from '../stores/fiscalYear'
import { formatAccountingAmount } from '../utils/format'

const { t } = useI18n()
const fiscalYearStore = useFiscalYearStore()

const bilan = ref<BilanRead | null>(null)
const loading = ref(false)
const fiscalYears = computed(() => fiscalYearStore.fiscalYears)
const fiscalYearId = computed({
  get: () => fiscalYearStore.selectedFiscalYearId,
  set: (value: number | undefined) => fiscalYearStore.setSelectedFiscalYear(value),
})

async function loadBilan() {
  loading.value = true
  try {
    bilan.value = await getBilanApi(fiscalYearId.value)
  } finally {
    loading.value = false
  }
}

function downloadCsv() {
  const url = getExportCsvUrl('bilan', {
    fiscal_year_id: fiscalYearId.value,
  })
  window.open(url, '_blank')
}

watch(
  () => fiscalYearStore.selectedFiscalYearId,
  (newId, oldId) => {
    if (!fiscalYearStore.initialized || newId === oldId) return
    void loadBilan()
  },
)

onMounted(async () => {
  await fiscalYearStore.initialize()
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
