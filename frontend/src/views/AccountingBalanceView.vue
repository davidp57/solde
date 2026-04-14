<template>
  <AppPage width="wide">
    <AppPageHeader
      :eyebrow="t('ui.page.accounting_eyebrow')"
      :title="t('accounting.balance.title')"
    />

    <AppPanel :title="t('accounting.balance.title')" dense>
      <div class="app-toolbar">
        <div class="app-filter-grid">
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.journal.filter_from') }}</label>
            <InputText v-model="fromDate" type="date" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.journal.filter_to') }}</label>
            <InputText v-model="toDate" type="date" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.journal.filter_fiscal_year') }}</label>
            <Select
              v-model="fiscalYearId"
              :options="fiscalYears"
              option-label="name"
              option-value="id"
              :placeholder="t('common.all')"
            />
          </div>
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('common.filter_placeholder') }}</label>
            <InputText v-model="filterText" :placeholder="t('common.filter_placeholder')" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('common.search') }}</label>
            <Button :label="t('common.search')" icon="pi pi-search" @click="load" />
          </div>
        </div>
      </div>

      <DataTable
        :value="filtered"
        :loading="loading"
        class="app-data-table"
        striped-rows
        paginator
        :rows="20"
        :rows-per-page-options="[20, 50, 100, 500]"
        size="small"
        row-hover
      >
        <Column field="account_number" :header="t('accounting.balance.account_number')" sortable />
        <Column field="account_label" :header="t('accounting.balance.account_label')" />
        <Column field="account_type" :header="t('accounting.balance.account_type')">
          <template #body="{ data }">{{
            t(`accounting.account_types.${data.account_type}`)
          }}</template>
        </Column>
        <Column
          field="total_debit"
          :header="t('accounting.balance.total_debit')"
          class="app-money"
        />
        <Column
          field="total_credit"
          :header="t('accounting.balance.total_credit')"
          class="app-money"
        />
        <Column field="solde" :header="t('accounting.balance.solde')" class="app-money" />
        <template #empty>
          <div class="app-empty-state">{{ t('accounting.balance.empty') }}</div>
        </template>
      </DataTable>
    </AppPanel>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import { getBalanceApi, type BalanceRow } from '../api/accounting'
import { useTableFilter } from '../composables/useTableFilter'
import { useFiscalYearStore } from '../stores/fiscalYear'

const { t } = useI18n()
const fiscalYearStore = useFiscalYearStore()

const rows = ref<BalanceRow[]>([])
const { filterText, filtered } = useTableFilter(rows)
const fiscalYears = computed(() => fiscalYearStore.fiscalYears)
const fiscalYearId = computed({
  get: () => fiscalYearStore.selectedFiscalYearId,
  set: (value: number | undefined) => fiscalYearStore.setSelectedFiscalYear(value),
})
const loading = ref(false)
const fromDate = ref('')
const toDate = ref('')

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

watch(
  () => fiscalYearStore.selectedFiscalYearId,
  (newId, oldId) => {
    if (!fiscalYearStore.initialized || newId === oldId) return
    void load()
  },
)

onMounted(async () => {
  await fiscalYearStore.initialize()
  await load()
})
</script>
