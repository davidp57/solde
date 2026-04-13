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
            <label class="app-field__label">{{ t('accounting.journal.filter_from') }}</label>
            <InputText v-model="fromDate" type="date" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.journal.filter_to') }}</label>
            <InputText v-model="toDate" type="date" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('common.search') }}</label>
            <Button :label="t('common.search')" icon="pi pi-search" @click="load" :disabled="!accountNumber" />
          </div>
        </div>
      </div>

      <template v-if="ledger">
        <section class="app-stat-grid ledger-summary-grid">
          <AppStatCard :label="t('accounting.ledger.opening_balance')" :value="ledger.opening_balance" />
          <AppStatCard :label="t('accounting.ledger.closing_balance')" :value="ledger.closing_balance" />
          <AppStatCard :label="t('accounting.journal.title')" :value="ledger.entries.length" />
        </section>

        <DataTable :value="ledger.entries" :loading="loading" class="app-data-table" striped-rows paginator :rows="20" :rows-per-page-options="[20, 50, 100, 500]" size="small" row-hover>
        <Column field="date" :header="t('accounting.journal.date')" sortable>
          <template #body="{ data }">{{ formatDisplayDate(data.date) }}</template>
        </Column>
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
      <div v-else class="app-empty-state">{{ t('accounting.ledger.select_account') }}</div>
    </AppPanel>
  </AppPage>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
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
import { getLedgerApi, listAccountsApi, type LedgerRead } from '../api/accounting'
import { useFiscalYearStore } from '../stores/fiscalYear'
import { formatDisplayDate } from '@/utils/format'

const { t } = useI18n()
const fiscalYearStore = useFiscalYearStore()

const ledger = ref<LedgerRead | null>(null)
const accounts = ref<Array<{ number: string; displayLabel: string }>>([])
const accountNumber = ref('')
const fromDate = ref('')
const toDate = ref('')
const loading = ref(false)

async function load() {
  if (!accountNumber.value) return
  loading.value = true
  try {
    ledger.value = await getLedgerApi(accountNumber.value, {
      from_date: fromDate.value || undefined,
      to_date: toDate.value || undefined,
      fiscal_year_id: fiscalYearStore.selectedFiscalYearId,
    })
  } finally {
    loading.value = false
  }
}

watch(
  () => fiscalYearStore.selectedFiscalYearId,
  (newId, oldId) => {
    if (!fiscalYearStore.initialized || newId === oldId || !accountNumber.value) return
    void load()
  },
)

onMounted(async () => {
  await fiscalYearStore.initialize()
  const accts = await listAccountsApi(undefined, false)
  accounts.value = accts.map((a) => ({
    number: a.number,
    displayLabel: `${a.number} — ${a.label}`,
  }))
})
</script>
