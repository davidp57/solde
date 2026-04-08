<template>
  <div class="view-container">
    <div class="view-header">
      <h1>{{ t('accounting.resultat.title') }}</h1>
    </div>

    <div class="filters-row">
      <div class="filter-group">
        <label>{{ t('accounting.journal.filter_fiscal_year') }}</label>
        <Select
          v-model="fiscalYearId"
          :options="fiscalYears"
          option-label="name"
          option-value="id"
          :placeholder="t('common.all')"
          show-clear
        />
      </div>
      <Button icon="pi pi-refresh" @click="load" />
    </div>

    <div v-if="resultat" class="resultat-grid">
      <!-- Charges -->
      <div class="resultat-col">
        <h2>{{ t('accounting.resultat.charges') }}</h2>
        <DataTable :value="resultat.charges" :loading="loading" size="small">
          <Column field="account_number" :header="t('accounting.balance.account_number')" />
          <Column field="account_label" :header="t('accounting.balance.account_label')" />
          <Column field="solde" :header="t('accounting.resultat.total_charges')" class="text-right" />
          <template #empty>{{ t('accounting.resultat.empty_charges') }}</template>
        </DataTable>
        <div class="resultat-total">
          {{ t('accounting.resultat.total_charges') }} : <strong>{{ resultat.total_charges }}</strong>
        </div>
      </div>

      <!-- Produits -->
      <div class="resultat-col">
        <h2>{{ t('accounting.resultat.produits') }}</h2>
        <DataTable :value="resultat.produits" :loading="loading" size="small">
          <Column field="account_number" :header="t('accounting.balance.account_number')" />
          <Column field="account_label" :header="t('accounting.balance.account_label')" />
          <Column field="solde" :header="t('accounting.resultat.total_produits')" class="text-right" />
          <template #empty>{{ t('accounting.resultat.empty_produits') }}</template>
        </DataTable>
        <div class="resultat-total">
          {{ t('accounting.resultat.total_produits') }} : <strong>{{ resultat.total_produits }}</strong>
        </div>
      </div>
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Select from 'primevue/select'
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
  gap: 2rem;
  margin-top: 1rem;
}

.resultat-total {
  margin-top: 0.5rem;
  font-size: 0.95rem;
  text-align: right;
}

.resultat-bottom {
  margin-top: 2rem;
  text-align: right;
  font-size: 1.1rem;
}

.resultat-excedent {
  color: var(--p-green-600);
}

.resultat-deficit {
  color: var(--p-red-600);
}
</style>
