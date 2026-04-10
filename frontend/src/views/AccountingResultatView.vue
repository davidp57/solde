<template>
  <AppPage width="wide">
    <AppPageHeader :eyebrow="t('ui.page.accounting_eyebrow')" :title="t('accounting.resultat.title')" />

    <AppPanel :title="t('accounting.resultat.title')" dense>
      <div class="app-toolbar">
        <div class="app-filter-grid">
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.journal.filter_fiscal_year') }}</label>
            <Select
              v-model="fiscalYearId"
              :options="fiscalYears"
              option-label="name"
              option-value="id"
              :placeholder="t('common.all')"
              show-clear
            />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('common.search') }}</label>
            <Button :label="t('common.search')" icon="pi pi-refresh" @click="load" />
          </div>
        </div>
      </div>

      <div v-if="resultat" class="resultat-grid">
      <!-- Charges -->
      <AppPanel :title="t('accounting.resultat.charges')" dense>
        <DataTable :value="resultat.charges" :loading="loading" class="app-data-table" size="small">
          <Column field="account_number" :header="t('accounting.balance.account_number')" />
          <Column field="account_label" :header="t('accounting.balance.account_label')" />
          <Column field="solde" :header="t('accounting.resultat.total_charges')" class="app-money" />
          <template #empty><div class="app-empty-state">{{ t('accounting.resultat.empty_charges') }}</div></template>
        </DataTable>
        <div class="resultat-total">
          {{ t('accounting.resultat.total_charges') }} : <strong>{{ resultat.total_charges }}</strong>
        </div>
      </AppPanel>

      <!-- Produits -->
      <AppPanel :title="t('accounting.resultat.produits')" dense>
        <DataTable :value="resultat.produits" :loading="loading" class="app-data-table" size="small">
          <Column field="account_number" :header="t('accounting.balance.account_number')" />
          <Column field="account_label" :header="t('accounting.balance.account_label')" />
          <Column field="solde" :header="t('accounting.resultat.total_produits')" class="app-money" />
          <template #empty><div class="app-empty-state">{{ t('accounting.resultat.empty_produits') }}</div></template>
        </DataTable>
        <div class="resultat-total">
          {{ t('accounting.resultat.total_produits') }} : <strong>{{ resultat.total_produits }}</strong>
        </div>
      </AppPanel>
      </div>

      <div v-if="resultat" class="resultat-bottom">
      <span
        :class="[
          'resultat-net',
          parseFloat(resultat.resultat) >= 0 ? 'resultat-excedent' : 'resultat-deficit',
        ]"
      >
        {{ parseFloat(resultat.resultat) >= 0 ? t('accounting.resultat.excedent') : t('accounting.resultat.deficit') }} :
        <strong>{{ resultat.resultat }}</strong>
      </span>
      </div>
    </AppPanel>
  </AppPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Select from 'primevue/select'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import { getResultatApi, listFiscalYearsApi, type ResultatRead, type FiscalYearRead } from '../api/accounting'

const { t } = useI18n()

const resultat = ref<ResultatRead | null>(null)
const fiscalYears = ref<FiscalYearRead[]>([])
const fiscalYearId = ref<number | undefined>()
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    resultat.value = await getResultatApi(fiscalYearId.value)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  fiscalYears.value = await listFiscalYearsApi()
  await load()
})
</script>

<style scoped>
.resultat-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--app-space-5);
}

.resultat-total {
  margin-top: 0.5rem;
  font-size: 0.95rem;
  text-align: right;
}

.resultat-bottom {
  margin-top: var(--app-space-6);
  text-align: right;
  font-size: 1.1rem;
}

.resultat-excedent {
  color: var(--p-green-600);
}

.resultat-deficit {
  color: var(--p-red-600);
}

@media (max-width: 900px) {
  .resultat-grid {
    grid-template-columns: 1fr;
  }
}
</style>
