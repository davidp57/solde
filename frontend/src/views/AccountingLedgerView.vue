<template>
  <AppPage width="wide">
    <AppPageHeader
      :eyebrow="t('ui.page.accounting_eyebrow')"
      :title="t('accounting.ledger.title')"
    />

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
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('common.filter_placeholder') }}</label>
            <InputText v-model="globalFilter" :placeholder="t('common.filter_placeholder')" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('common.reset_filters') }}</label>
            <Button
              icon="pi pi-filter-slash"
              severity="secondary"
              outlined
              :disabled="!hasActiveFilters"
              @click="resetFilters"
            />
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
          <AppStatCard
            :label="t('accounting.ledger.opening_balance')"
            :value="ledger.opening_balance"
          />
          <AppStatCard
            :label="t('accounting.ledger.closing_balance')"
            :value="ledger.closing_balance"
          />
          <AppStatCard :label="t('accounting.journal.title')" :value="ledger.entries.length" />
        </section>

        <DataTable
          v-model:filters="tableFilters"
          :value="ledgerRows"
          :loading="loading"
          class="app-data-table"
          filter-display="menu"
          striped-rows
          paginator
          :rows="20"
          :rows-per-page-options="[20, 50, 100, 500]"
          :global-filter-fields="[
            'date',
            'entry_number',
            'label',
            'debit',
            'credit',
            'running_balance',
          ]"
          size="small"
          row-hover
          removable-sort
        >
          <Column
            field="date"
            :header="t('accounting.journal.date')"
            sortable
            :show-filter-match-modes="false"
            :show-add-button="false"
          >
            <template #body="{ data }">{{ formatDisplayDate(data.date) }}</template>
            <template #filter="{ filterModel }">
              <AppDateRangeFilter v-model="filterModel.value" />
            </template>
          </Column>
          <Column
            field="entry_number"
            :header="t('accounting.journal.entry_number')"
            sortable
            :show-filter-match-modes="false"
            :show-add-button="false"
          >
            <template #filter="{ filterModel }">
              <InputText
                v-model="filterModel.value"
                :placeholder="t('accounting.journal.entry_number')"
              />
            </template>
          </Column>
          <Column
            field="label"
            :header="t('accounting.journal.label')"
            sortable
            :show-filter-match-modes="false"
            :show-add-button="false"
          >
            <template #filter="{ filterModel }">
              <InputText v-model="filterModel.value" :placeholder="t('accounting.journal.label')" />
            </template>
          </Column>
          <Column
            field="debit_value"
            :header="t('accounting.journal.debit')"
            class="app-money"
            sortable
            filter-field="debit_value"
            data-type="numeric"
            :show-filter-match-modes="false"
            :show-add-button="false"
          >
            <template #body="{ data }">{{ data.debit !== '0.00' ? data.debit : '' }}</template>
            <template #filter="{ filterModel }">
              <AppNumberRangeFilter v-model="filterModel.value" />
            </template>
          </Column>
          <Column
            field="credit_value"
            :header="t('accounting.journal.credit')"
            class="app-money"
            sortable
            filter-field="credit_value"
            data-type="numeric"
            :show-filter-match-modes="false"
            :show-add-button="false"
          >
            <template #body="{ data }">{{ data.credit !== '0.00' ? data.credit : '' }}</template>
            <template #filter="{ filterModel }">
              <AppNumberRangeFilter v-model="filterModel.value" />
            </template>
          </Column>
          <Column
            field="running_balance_value"
            :header="t('accounting.balance.solde')"
            class="app-money"
            sortable
            filter-field="running_balance_value"
            data-type="numeric"
            :show-filter-match-modes="false"
            :show-add-button="false"
          >
            <template #filter="{ filterModel }">
              <AppNumberRangeFilter v-model="filterModel.value" />
            </template>
          </Column>
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
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import AppDateRangeFilter from '../components/ui/AppDateRangeFilter.vue'
import AppNumberRangeFilter from '../components/ui/AppNumberRangeFilter.vue'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import AppStatCard from '../components/ui/AppStatCard.vue'
import { getLedgerApi, listAccountsApi, type LedgerRead } from '../api/accounting'
import {
  dateRangeFilter,
  numericRangeFilter,
  textFilter,
  useDataTableFilters,
} from '../composables/useDataTableFilters'
import { useFiscalYearStore } from '../stores/fiscalYear'
import { formatDisplayDate } from '@/utils/format'

const { t } = useI18n()
const fiscalYearStore = useFiscalYearStore()

const ledger = ref<LedgerRead | null>(null)
const accounts = ref<Array<{ number: string; displayLabel: string }>>([])
const fiscalYears = computed(() => fiscalYearStore.fiscalYears)
const fiscalYearId = computed({
  get: () => fiscalYearStore.selectedFiscalYearId,
  set: (value: number | undefined) => fiscalYearStore.setSelectedFiscalYear(value),
})
const accountNumber = ref('')
const fromDate = ref('')
const toDate = ref('')
const loading = ref(false)
const initializing = ref(true)

const ledgerRows = computed(() =>
  (ledger.value?.entries ?? []).map((entry) => ({
    ...entry,
    debit_value: parseFloat(entry.debit),
    credit_value: parseFloat(entry.credit),
    running_balance_value: parseFloat(entry.running_balance),
  })),
)

const {
  filters: tableFilters,
  globalFilter,
  hasActiveFilters,
  resetFilters,
} = useDataTableFilters(ledgerRows, {
  global: textFilter(''),
  date: dateRangeFilter(),
  entry_number: textFilter(),
  label: textFilter(),
  debit_value: numericRangeFilter(),
  credit_value: numericRangeFilter(),
  running_balance_value: numericRangeFilter(),
})

const emptyStateMessage = computed(() => {
  if (initializing.value) {
    return t('common.loading')
  }
  if (fiscalYearStore.fiscalYears.length === 0) {
    return t('accounting.ledger.no_fiscal_year')
  }
  if (!fiscalYearStore.selectedFiscalYearId) {
    return t('accounting.ledger.select_fiscal_year')
  }
  return t('accounting.ledger.select_account')
})

async function load() {
  if (!accountNumber.value || !fiscalYearStore.selectedFiscalYearId) return
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

watch(
  () => fiscalYearStore.selectedFiscalYearId,
  (newId, oldId) => {
    if (!fiscalYearStore.initialized || newId === oldId || !accountNumber.value) return
    void load()
  },
)

onMounted(async () => {
  try {
    await fiscalYearStore.initialize()
    const accts = await listAccountsApi(undefined, false)
    accounts.value = accts.map((a) => ({
      number: a.number,
      displayLabel: `${a.number} — ${a.label}`,
    }))
  } finally {
    initializing.value = false
  }
})
</script>
