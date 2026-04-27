<template>
  <AppPage width="wide">
    <AppPageHeader
      :eyebrow="t('ui.page.accounting_eyebrow')"
      :title="t('accounting.balance.title')"
    />

    <AppPanel :title="t('accounting.balance.title')" dense>
      <div class="balance-focus-legend">
        <span class="balance-focus-legend__label">{{ t('accounting.balance.focus_label') }}</span>
        <span
          v-for="focusAccount in focusAccounts"
          :key="focusAccount.account_number"
          class="balance-focus-chip"
          :class="`balance-focus-chip--${focusAccount.key}`"
        >
          {{ focusAccount.account_number }} · {{ t(`accounting.balance.focus.${focusAccount.key}`) }}
        </span>
      </div>

      <div class="app-toolbar">
        <div class="app-filter-grid">
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.journal.filter_from') }}</label>
            <AppDateInput v-model="fromDate" @keydown.enter="load" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.journal.filter_to') }}</label>
            <AppDateInput v-model="toDate" @keydown.enter="load" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.journal.filter_fiscal_year') }}</label>
            <Select
              v-model="fiscalYearId"
              :options="fiscalYears"
              option-label="name"
              option-value="id"
              :placeholder="t('common.all')"
              @change="load"
            />
          </div>
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('common.filter_placeholder') }}</label>
            <InputText
              v-model="globalFilter"
              :placeholder="t('common.filter_placeholder')"
              @keydown.enter="load"
            />
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
            <Button :label="t('common.search')" icon="pi pi-search" @click="load" />
          </div>
        </div>
      </div>

      <DataTable
        v-model:filters="tableFilters"
        :value="balanceRows"
        :row-class="rowClass"
        :loading="loading"
        class="app-data-table"
        filter-display="menu"
        striped-rows
        paginator
        :rows="20"
        :rows-per-page-options="[20, 50, 100, 500]"
        :global-filter-fields="[
          'account_number',
          'account_label',
          'account_type_label',
          'total_debit',
          'total_credit',
          'solde',
        ]"
        size="small"
        row-hover
        removable-sort
      >
        <Column field="account_number" :header="t('accounting.balance.account_number')" sortable>
          <template #body="{ data }">
            <span :class="{ 'balance-account-number--focus': data.focus_key }">
              {{ data.account_number }}
            </span>
          </template>
          <template #filter="{ filterModel }">
            <InputText
              v-model="filterModel.value"
              :placeholder="t('accounting.balance.account_number')"
            />
          </template>
        </Column>
        <Column field="account_label" :header="t('accounting.balance.account_label')" sortable>
          <template #filter="{ filterModel }">
            <InputText
              v-model="filterModel.value"
              :placeholder="t('accounting.balance.account_label')"
            />
          </template>
        </Column>
        <Column
          field="account_type_label"
          :header="t('accounting.balance.account_type')"
          sortable
          filter-field="account_type"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{
            t(`accounting.account_types.${data.account_type}`)
          }}</template>
          <template #filter="{ filterModel, filterCallback }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="accountTypeOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
              show-clear
              :filter-callback="filterCallback"
            />
          </template>
        </Column>
        <Column
          field="total_debit_value"
          :header="t('accounting.balance.total_debit')"
          class="app-money"
          sortable
          filter-field="total_debit_value"
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column
          field="total_credit_value"
          :header="t('accounting.balance.total_credit')"
          class="app-money"
          sortable
          filter-field="total_credit_value"
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column
          field="solde_value"
          :header="t('accounting.balance.solde')"
          class="app-money"
          sortable
          filter-field="solde_value"
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            {{ formatAccountingAmount(data.solde_value) }}
          </template>
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
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
import AppDateInput from '../components/ui/AppDateInput.vue'
import AppFilterMultiSelect from '../components/ui/AppFilterMultiSelect.vue'
import AppNumberRangeFilter from '../components/ui/AppNumberRangeFilter.vue'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import { getBalanceApi, type BalanceRow } from '../api/accounting'
import {
  inFilter,
  numericRangeFilter,
  textFilter,
  useDataTableFilters,
} from '../composables/useDataTableFilters'
import { useFiscalYearStore } from '../stores/fiscalYear'
import { focusAccounts, getFocusAccountKey, type FocusAccountKey } from '../utils/focusAccounts'
import { formatAccountingAmount } from '../utils/format'

type BalanceRowView = BalanceRow & {
  account_type_label: string
  total_debit_value: number
  total_credit_value: number
  solde_value: number
  focus_key: FocusAccountKey | null
}

const { t } = useI18n()
const fiscalYearStore = useFiscalYearStore()

const rows = ref<BalanceRow[]>([])
const fiscalYears = computed(() => fiscalYearStore.fiscalYears)
const fiscalYearId = computed({
  get: () => fiscalYearStore.selectedFiscalYearId,
  set: (value: number | undefined) => fiscalYearStore.setSelectedFiscalYear(value),
})
const loading = ref(false)
const fromDate = ref('')
const toDate = ref('')

const balanceRows = computed<BalanceRowView[]>(() =>
  rows.value.map((row) => ({
    ...row,
    account_type_label: t(`accounting.account_types.${row.account_type}`),
    total_debit_value: parseFloat(row.total_debit),
    total_credit_value: parseFloat(row.total_credit),
    solde_value: parseFloat(row.solde),
    focus_key: getFocusAccountKey(row.account_number),
  })),
)

function rowClass(row: BalanceRowView): string[] {
  return row.focus_key ? ['balance-row--focus', `balance-row--focus-${row.focus_key}`] : []
}

const {
  filters: tableFilters,
  globalFilter,
  hasActiveFilters,
  resetFilters,
} = useDataTableFilters(balanceRows, {
  global: textFilter(''),
  account_number: textFilter(),
  account_label: textFilter(),
  account_type: inFilter(),
  total_debit_value: numericRangeFilter(),
  total_credit_value: numericRangeFilter(),
  solde_value: numericRangeFilter(),
})

const accountTypeOptions = [
  { label: t('accounting.account_types.actif'), value: 'actif' },
  { label: t('accounting.account_types.passif'), value: 'passif' },
  { label: t('accounting.account_types.charge'), value: 'charge' },
  { label: t('accounting.account_types.produit'), value: 'produit' },
]

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

<style scoped>
.balance-focus-legend {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.55rem;
  margin-bottom: 1rem;
}

.balance-focus-legend__label {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--p-text-muted-color, #94a3b8);
}

.balance-focus-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.28rem 0.75rem;
  border-radius: 999px;
  border: 1px solid var(--balance-focus-accent);
  background: var(--balance-focus-bg);
  color: var(--balance-focus-fg);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.01em;
}

.balance-account-number--focus {
  font-weight: 700;
}

.balance-focus-chip--member_receivables,
:deep(.balance-row--focus-member_receivables) {
  --balance-focus-bg: rgba(251, 191, 36, 0.14);
  --balance-focus-accent: rgba(251, 191, 36, 0.45);
  --balance-focus-fg: #ffefbf;
}

.balance-focus-chip--supplier_payables,
:deep(.balance-row--focus-supplier_payables) {
  --balance-focus-bg: rgba(56, 189, 248, 0.14);
  --balance-focus-accent: rgba(56, 189, 248, 0.5);
  --balance-focus-fg: #d7f0ff;
}

.balance-focus-chip--cash,
:deep(.balance-row--focus-cash) {
  --balance-focus-bg: rgba(74, 222, 128, 0.14);
  --balance-focus-accent: rgba(74, 222, 128, 0.42);
  --balance-focus-fg: #dbffe4;
}

.balance-focus-chip--current_account,
:deep(.balance-row--focus-current_account) {
  --balance-focus-bg: rgba(248, 113, 113, 0.14);
  --balance-focus-accent: rgba(248, 113, 113, 0.4);
  --balance-focus-fg: #ffe1e1;
}

.balance-focus-chip--cheques_to_deposit,
:deep(.balance-row--focus-cheques_to_deposit) {
  --balance-focus-bg: rgba(129, 140, 248, 0.14);
  --balance-focus-accent: rgba(129, 140, 248, 0.42);
  --balance-focus-fg: #e1e5ff;
}

:deep(.balance-row--focus > td) {
  background: var(--balance-focus-bg) !important;
  box-shadow: inset 4px 0 0 var(--balance-focus-accent);
}

:deep(.balance-row--focus:hover > td) {
  filter: brightness(1.04);
}
</style>
