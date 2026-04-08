<template>
  <div class="view-container">
    <div class="view-header">
      <h1>{{ t('accounting.ledger.title') }}</h1>
    </div>

    <div class="filters-row">
      <div class="filter-group">
        <label>{{ t('accounting.journal.filter_account') }}</label>
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
      <div class="filter-group">
        <label>{{ t('accounting.journal.filter_from') }}</label>
        <InputText v-model="fromDate" type="date" />
      </div>
      <div class="filter-group">
        <label>{{ t('accounting.journal.filter_to') }}</label>
        <InputText v-model="toDate" type="date" />
      </div>
      <Button icon="pi pi-search" @click="load" :disabled="!accountNumber" />
    </div>

    <template v-if="ledger">
      <div class="ledger-summary">
        <span>{{ t('accounting.ledger.opening_balance') }} : <strong>{{ ledger.opening_balance }}</strong></span>
        <span>{{ t('accounting.ledger.closing_balance') }} : <strong>{{ ledger.closing_balance }}</strong></span>
      </div>

      <DataTable :value="ledger.entries" :loading="loading" striped-rows>
        <Column field="date" :header="t('accounting.journal.date')" sortable />
        <Column field="entry_number" :header="t('accounting.journal.entry_number')" />
        <Column field="label" :header="t('accounting.journal.label')" />
        <Column field="debit" :header="t('accounting.journal.debit')" class="text-right">
          <template #body="{ data }">{{ data.debit !== '0.00' ? data.debit : '' }}</template>
        </Column>
        <Column field="credit" :header="t('accounting.journal.credit')" class="text-right">
          <template #body="{ data }">{{ data.credit !== '0.00' ? data.credit : '' }}</template>
        </Column>
        <Column field="running_balance" :header="t('accounting.balance.solde')" class="text-right" />
        <template #empty>{{ t('accounting.ledger.empty') }}</template>
      </DataTable>
    </template>
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
import { getLedgerApi, listAccountsApi, type LedgerRead } from '../api/accounting'

const { t } = useI18n()

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
    })
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  const accts = await listAccountsApi(undefined, false)
  accounts.value = accts.map((a) => ({
    number: a.number,
    displayLabel: `${a.number} — ${a.label}`,
  }))
})
</script>
