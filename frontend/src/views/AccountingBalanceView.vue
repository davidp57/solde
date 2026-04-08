<template>
  <div class="view-container">
    <div class="view-header">
      <h1>{{ t('accounting.balance.title') }}</h1>
    </div>

    <div class="filters-row">
      <div class="filter-group">
        <label>{{ t('accounting.journal.filter_from') }}</label>
        <InputText v-model="fromDate" type="date" />
      </div>
      <div class="filter-group">
        <label>{{ t('accounting.journal.filter_to') }}</label>
        <InputText v-model="toDate" type="date" />
      </div>
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
      <Button icon="pi pi-search" @click="load" />
    </div>

    <DataTable :value="rows" :loading="loading" striped-rows>
      <Column field="account_number" :header="t('accounting.balance.account_number')" sortable />
      <Column field="account_label" :header="t('accounting.balance.account_label')" />
      <Column field="account_type" :header="t('accounting.balance.account_type')">
        <template #body="{ data }">{{ t(`accounting.account_types.${data.account_type}`) }}</template>
      </Column>
      <Column field="total_debit" :header="t('accounting.balance.total_debit')" class="text-right" />
      <Column field="total_credit" :header="t('accounting.balance.total_credit')" class="text-right" />
      <Column field="solde" :header="t('accounting.balance.solde')" class="text-right" />
      <template #empty>{{ t('accounting.balance.empty') }}</template>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import { getBalanceApi, listFiscalYearsApi, type BalanceRow, type FiscalYearRead } from '../api/accounting'

const { t } = useI18n()

const rows = ref<BalanceRow[]>([])
const fiscalYears = ref<FiscalYearRead[]>([])
const loading = ref(false)
const fromDate = ref('')
const toDate = ref('')
const fiscalYearId = ref<number | undefined>()

async function load() {
  loading.value = true
  try {
    rows.value = await getBalanceApi({
      from_date: fromDate.value || undefined,
      to_date: toDate.value || undefined,
      fiscal_year_id: fiscalYearId.value,
    })
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  fiscalYears.value = await listFiscalYearsApi()
  await load()
})
</script>
