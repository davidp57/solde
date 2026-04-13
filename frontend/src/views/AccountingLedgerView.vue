<template>
  <AppPage width="wide">
    <AppPageHeader :eyebrow="t('ui.page.accounting_eyebrow')" :title="t('accounting.ledger.title')" />

    <AppPanel :title="t('accounting.ledger.title')" dense>
      <div class="app-toolbar">
        <div class="app-filter-grid">
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('accounting.journal.filter_account') }}</label>
            <Select
              v-model="accountNumber"
              :options="accounts"
              option-label="displayLabel"
              option-value="number"
              :placeholder="t('accounting.ledger.select_account')"
              filter
              editable
            />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.journal.filter_fiscal_year') }}</label>
            <Select
              v-model="fiscalYearId"
              :options="fiscalYears"
              option-label="name"
              option-value="id"
            />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.journal.filter_from') }}</label>
            <InputText v-model="fromDate" type="date" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.journal.filter_to') }}</label>
            <InputText v-model="toDate" type="date" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('common.search') }}</label>
            <Button
              :label="t('common.search')"
              icon="pi pi-search"
              @click="load"
              :disabled="!accountNumber || !fiscalYearId"
            />
          </div>
        </div>
      </div>

      <template v-if="ledger">
        <section class="app-stat-grid ledger-summary-grid">
          <AppStatCard :label="t('accounting.ledger.opening_balance')" :value="ledger.opening_balance" />
          <AppStatCard :label="t('accounting.ledger.closing_balance')" :value="ledger.closing_balance" />
          <AppStatCard :label="t('accounting.journal.title')" :value="ledger.entries.length" />
        </section>

        <DataTable :value="ledger.entries" :loading="loading" class="app-data-table" striped-rows size="small" row-hover>
        <Column field="date" :header="t('accounting.journal.date')" sortable />
        <Column field="entry_number" :header="t('accounting.journal.entry_number')" />
        <Column field="label" :header="t('accounting.journal.label')" />
        <Column field="debit" :header="t('accounting.journal.debit')" class="app-money">
          <template #body="{ data }">{{ data.debit !== '0.00' ? data.debit : '' }}</template>
        </Column>
        <Column field="credit" :header="t('accounting.journal.credit')" class="app-money">
          <template #body="{ data }">{{ data.credit !== '0.00' ? data.credit : '' }}</template>
        </Column>
        <Column field="running_balance" :header="t('accounting.balance.solde')" class="app-money" />
          <template #empty>
            <div class="app-empty-state">{{ t('accounting.ledger.empty') }}</div>
          </template>
        </DataTable>
      </template>
      <div v-else class="app-empty-state">{{ emptyStateMessage }}</div>
    </AppPanel>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import AppStatCard from '../components/ui/AppStatCard.vue'
import {
  getCurrentFiscalYearApi,
  getLedgerApi,
  listAccountsApi,
  listFiscalYearsApi,
  type FiscalYearRead,
  type LedgerRead,
} from '../api/accounting'

const { t } = useI18n()

const ledger = ref<LedgerRead | null>(null)
const accounts = ref<Array<{ number: string; displayLabel: string }>>([])
const fiscalYears = ref<FiscalYearRead[]>([])
const accountNumber = ref('')
const fromDate = ref('')
const toDate = ref('')
const fiscalYearId = ref<number | undefined>()
const loading = ref(false)
const initializing = ref(true)

const emptyStateMessage = computed(() => {
  if (initializing.value) {
    return t('common.loading')
  }
  if (fiscalYears.value.length === 0) {
    return t('accounting.ledger.no_fiscal_year')
  }
  if (!fiscalYearId.value) {
    return t('accounting.ledger.select_fiscal_year')
  }
  return t('accounting.ledger.select_account')
})

async function load() {
  if (!accountNumber.value || !fiscalYearId.value) return
  loading.value = true
  try {
    ledger.value = await getLedgerApi(accountNumber.value, {
      from_date: fromDate.value || undefined,
      to_date: toDate.value || undefined,
      fiscal_year_id: fiscalYearId.value,
    })
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const [accts, fiscalYearList, currentFiscalYear] = await Promise.all([
      listAccountsApi(undefined, false),
      listFiscalYearsApi(),
      getCurrentFiscalYearApi(),
    ])
    accounts.value = accts.map((a) => ({
      number: a.number,
      displayLabel: `${a.number} — ${a.label}`,
    }))
    fiscalYears.value = fiscalYearList
    fiscalYearId.value = currentFiscalYear?.id ?? fiscalYearList[0]?.id
  } finally {
    initializing.value = false
  }
})
</script>
