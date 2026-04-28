<template>
  <AppPage width="wide">
    <AppPageHeader :eyebrow="t('ui.page.collection_eyebrow')" :title="t('bank.title')">
      <template #actions>
        <Button
          :label="t('bank.import_statement')"
          icon="pi pi-upload"
          severity="secondary"
          @click="importDialogVisible = true"
        />
        <Button
          :label="t('bank.new_deposit')"
          icon="pi pi-inbox"
          severity="secondary"
          @click="openDepositDialog"
        />
        <Button
          :label="t('bank.new_transaction')"
          icon="pi pi-plus"
          @click="txDialogVisible = true"
        />
      </template>
    </AppPageHeader>

    <section class="app-stat-grid">
      <AppStatCard
        :label="t('bank.current_balance')"
        :value="displayBalanceValue"
        :caption="currentBalanceCaption"
      />
      <AppStatCard
        :label="t('bank.period_variation')"
        :value="formatSignedAmount(displayedPeriodVariation)"
        :caption="periodVariationCaption"
        :tone="displayedPeriodVariationTone"
      />
      <AppStatCard
        :label="t('bank.transactions_title')"
        :value="displayedTransactions.length"
        :caption="t('bank.metrics.transactions_total', { count: transactions.length })"
      />
      <AppStatCard
        :label="t('bank.deposits_title')"
        :value="displayedDeposits.length"
        :caption="t('bank.metrics.pending_payments', { count: pendingDeposits.length })"
        tone="warn"
      />
    </section>

    <AppPanel :title="t('bank.funds_chart_title')" dense>
      <p class="bank-chart-panel__intro">{{ t('bank.funds_chart_intro') }}</p>
      <TrendLineChart
        :data="fundsChartData"
        :series="fundsChartSeries"
        :empty-label="t('bank.funds_chart_empty')"
        :ariaLabel="t('bank.funds_chart_title')"
      />
    </AppPanel>

    <AppPanel
      v-if="pendingDeposits.length > 0"
      :title="t('bank.pending_deposits_title')"
      :subtitle="t('bank.pending_deposits_subtitle')"
    >
      <div class="bank-pending-deposits">
        <div
          v-for="deposit in pendingDeposits"
          :key="deposit.id"
          class="bank-pending-deposit-row"
        >
          <Tag
            :value="t(`bank.deposit_types.${deposit.type}`)"
            :severity="deposit.type === 'cheques' ? 'info' : 'warn'"
            class="bank-pending-deposit-row__tag"
          />
          <span class="bank-pending-deposit-row__date">{{ formatDisplayDate(deposit.date) }}</span>
          <span class="bank-pending-deposit-row__summary">
            <template v-if="deposit.type === 'cheques'">
              {{ t('bank.deposit_cheques_summary', { count: deposit.payment_ids.length }) }}
            </template>
            <template v-else>
              {{ formatEspecesSummary(deposit.denomination_details) }}
            </template>
          </span>
          <span class="bank-pending-deposit-row__amount app-money">
            {{ formatAmount(deposit.total_amount) }}
          </span>
          <Button
            :label="t('bank.deposit_confirm')"
            icon="pi pi-check"
            severity="success"
            size="small"
            :loading="confirmingDepositId === deposit.id"
            @click="confirmDeposit(deposit)"
          />
        </div>
      </div>
    </AppPanel>

    <AppPanel :title="t('bank.title')" dense>
      <div class="app-toolbar">
        <div class="app-filter-grid">
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('common.filter_placeholder') }}</label>
            <InputText v-model="activeGlobalFilter" :placeholder="t('common.filter_placeholder')" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('common.reset_filters') }}</label>
            <Button
              icon="pi pi-filter-slash"
              severity="secondary"
              outlined
              :disabled="!activeHasFilters"
              @click="resetActiveFilters"
            />
          </div>
        </div>
      </div>

      <Tabs v-model:value="activeTab">
        <TabList>
          <Tab value="transactions">{{ t('bank.transactions_title') }}</Tab>
          <Tab value="deposits">{{ t('bank.deposits_title') }}</Tab>
        </TabList>

        <TabPanels>
          <TabPanel value="transactions">
            <div class="bank-panel-toolbar">
              <ToggleButton
                v-model="unreconciledOnly"
                :on-label="t('bank.tx_reconciled')"
                :off-label="t('bank.tx_reconciled')"
                @change="loadTransactions"
              />
            </div>
            <DataTable
              v-model:filters="transactionTableFilters"
              :value="transactionRows"
              :loading="loadingTx"
              class="app-data-table"
              filter-display="menu"
              striped-rows
              paginator
              :rows="20"
              :rows-per-page-options="[20, 50, 100, 500]"
              :global-filter-fields="[
                'date',
                'amount',
                'description',
                'reference',
                'balance_after',
                'reconciled_label',
                'detected_category_label',
                'source_label',
              ]"
              data-key="id"
              size="small"
              row-hover
              sort-field="date"
              :sort-order="-1"
              removable-sort
              @value-change="syncDisplayedTransactions"
            >
              <Column
                field="date"
                :header="t('bank.tx_date')"
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
                field="amount_value"
                :header="t('bank.tx_amount')"
                class="app-money bank-table__amount"
                sortable
                filter-field="amount_value"
                data-type="numeric"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">
                  <span :class="parseFloat(data.amount) >= 0 ? 'bank-positive' : 'bank-negative'">
                    {{ formatAmount(data.amount) }}
                  </span>
                </template>
                <template #filter="{ filterModel }">
                  <AppNumberRangeFilter v-model="filterModel.value" />
                </template>
              </Column>
              <Column
                field="description"
                :header="t('bank.tx_description')"
                class="bank-table__description"
                sortable
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #filter="{ filterModel }">
                  <InputText v-model="filterModel.value" :placeholder="t('bank.tx_description')" />
                </template>
              </Column>
              <Column
                field="reference"
                :header="t('bank.tx_reference')"
                class="bank-table__reference"
                sortable
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #filter="{ filterModel }">
                  <InputText v-model="filterModel.value" :placeholder="t('bank.tx_reference')" />
                </template>
              </Column>
              <Column
                field="balance_after_value"
                :header="t('bank.tx_balance_short')"
                class="bank-table__balance"
                sortable
                filter-field="balance_after_value"
                data-type="numeric"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">{{ formatAmount(data.balance_after) }}</template>
                <template #filter="{ filterModel }">
                  <AppNumberRangeFilter v-model="filterModel.value" />
                </template>
              </Column>
              <Column
                field="reconciled_label"
                :header="t('bank.tx_reconciled_short')"
                class="bank-table__reconciled"
                sortable
                filter-field="reconciled"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">
                  <i
                    :class="
                      data.reconciled
                        ? 'pi pi-check-circle text-green-500'
                        : 'pi pi-circle text-surface-400'
                    "
                  />
                </template>
                <template #filter="{ filterModel, filterCallback }">
                  <AppFilterMultiSelect
                    v-model="filterModel.value"
                    :options="yesNoOptions"
                    option-label="label"
                    option-value="value"
                    :placeholder="t('common.all')"
                    display="chip"
                    show-clear
                    :filter-callback="filterCallback"
                  />
                </template>
              </Column>
              <Column
                field="detected_category_label"
                :header="t('bank.tx_category_short')"
                class="bank-table__category"
                sortable
                filter-field="detected_category"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">
                  <Tag
                    class="bank-detected-category-tag"
                    :value="t(`bank.categories.${data.detected_category}`)"
                  />
                </template>
                <template #filter="{ filterModel, filterCallback }">
                  <AppFilterMultiSelect
                    v-model="filterModel.value"
                    :options="categoryOptions"
                    option-label="label"
                    option-value="value"
                    :placeholder="t('common.all')"
                    display="chip"
                    show-clear
                    :filter-callback="filterCallback"
                  />
                </template>
              </Column>
              <Column
                field="source_label"
                :header="t('bank.tx_source_short')"
                class="bank-table__source"
                sortable
                filter-field="source"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">
                  <Tag
                    :value="t(`bank.sources.${data.source}`)"
                    :severity="data.source === 'system_opening' ? 'info' : 'secondary'"
                  />
                </template>
                <template #filter="{ filterModel, filterCallback }">
                  <AppFilterMultiSelect
                    v-model="filterModel.value"
                    :options="sourceOptions"
                    option-label="label"
                    option-value="value"
                    :placeholder="t('common.all')"
                    display="chip"
                    show-clear
                    :filter-callback="filterCallback"
                  />
                </template>
              </Column>
              <Column :header="t('common.actions')" style="width: 7.25rem">
                <template #body="{ data }">
                  <Button
                    v-if="canLinkExistingSupplierPayment(data)"
                    icon="pi pi-link"
                    size="small"
                    severity="secondary"
                    text
                    :title="t('bank.link_supplier_payment')"
                    @click="openExistingSupplierPaymentDialog(data)"
                  />
                  <Button
                    v-if="canCreateSupplierPayment(data)"
                    icon="pi pi-arrow-up-right"
                    size="small"
                    severity="secondary"
                    text
                    :title="t('bank.create_supplier_payment')"
                    @click="openSupplierPaymentDialog(data)"
                  />
                  <Button
                    v-if="canLinkExistingClientPayment(data)"
                    icon="pi pi-link"
                    size="small"
                    severity="secondary"
                    text
                    :title="t('bank.link_client_payment')"
                    @click="openExistingClientPaymentDialog(data)"
                  />
                  <Button
                    v-if="canCreateClientPayment(data)"
                    icon="pi pi-wallet"
                    size="small"
                    severity="secondary"
                    text
                    :title="t('bank.create_client_payment')"
                    @click="openClientPaymentDialog(data)"
                  />
                  <Button
                    v-if="!data.reconciled"
                    icon="pi pi-check"
                    size="small"
                    severity="success"
                    text
                    :title="t('bank.reconcile')"
                    @click="reconcile(data)"
                  />
                </template>
              </Column>
              <template #empty>
                <div class="app-empty-state">{{ t('bank.transactions_empty') }}</div>
              </template>
            </DataTable>
          </TabPanel>

          <TabPanel value="deposits">
            <DataTable
              v-model:filters="depositTableFilters"
              :value="depositRows"
              :loading="loadingDeposits"
              class="app-data-table"
              filter-display="menu"
              striped-rows
              paginator
              :rows="20"
              :rows-per-page-options="[20, 50, 100, 500]"
              :global-filter-fields="[
                'date',
                'type_label',
                'total_amount',
                'bank_reference',
                'payment_count_label',
              ]"
              data-key="id"
              size="small"
              row-hover
              removable-sort
              @value-change="syncDisplayedDeposits"
            >
              <Column
                field="date"
                :header="t('bank.deposit_date')"
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
                field="type_label"
                :header="t('bank.deposit_type')"
                sortable
                filter-field="type"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">
                  <Tag :value="t(`bank.deposit_types.${data.type}`)" />
                </template>
                <template #filter="{ filterModel, filterCallback }">
                  <AppFilterMultiSelect
                    v-model="filterModel.value"
                    :options="depositTypeOptions"
                    option-label="label"
                    option-value="value"
                    :placeholder="t('common.all')"
                    display="chip"
                    show-clear
                    :filter-callback="filterCallback"
                  />
                </template>
              </Column>
              <Column
                field="total_amount_value"
                :header="t('bank.deposit_total')"
                class="app-money"
                sortable
                filter-field="total_amount_value"
                data-type="numeric"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">{{ formatAmount(data.total_amount) }}</template>
                <template #filter="{ filterModel }">
                  <AppNumberRangeFilter v-model="filterModel.value" />
                </template>
              </Column>
              <Column
                field="bank_reference"
                :header="t('bank.deposit_bank_ref')"
                sortable
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #filter="{ filterModel }">
                  <InputText
                    v-model="filterModel.value"
                    :placeholder="t('bank.deposit_bank_ref')"
                  />
                </template>
              </Column>
              <Column
                field="payment_count"
                :header="t('bank.deposit_payments')"
                sortable
                filter-field="payment_count"
                data-type="numeric"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">
                  {{
                    t('bank.metrics.deposit_payment_count', {
                      count: data.payment_ids?.length || 0,
                    })
                  }}
                </template>
                <template #filter="{ filterModel }">
                  <AppNumberRangeFilter v-model="filterModel.value" />
                </template>
              </Column>
              <Column
                field="confirmed_label"
                :header="t('bank.deposit_status_col')"
                sortable
                filter-field="confirmed"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">
                  <Tag
                    :value="data.confirmed ? t('bank.deposit_status.confirmed') : t('bank.deposit_status.pending')"
                    :severity="data.confirmed ? 'success' : 'warn'"
                  />
                </template>
                <template #filter="{ filterModel, filterCallback }">
                  <AppFilterMultiSelect
                    v-model="filterModel.value"
                    :options="yesNoOptions"
                    option-label="label"
                    option-value="value"
                    :placeholder="t('common.all')"
                    display="chip"
                    show-clear
                    :filter-callback="filterCallback"
                  />
                </template>
              </Column>
              <template #empty>
                <div class="app-empty-state">{{ t('bank.deposits_empty') }}</div>
              </template>
            </DataTable>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </AppPanel>

    <!-- Dialogs -->
    <BankNewTransactionDialog
      v-model:visible="txDialogVisible"
      @saved="loadAll"
    />
    <BankImportStatementDialog
      v-model:visible="importDialogVisible"
      @saved="loadAll"
    />

    <BankClientPaymentDialog
      v-model:visible="clientPaymentDialogVisible"
      :transaction="clientPaymentTransaction"
      @saved="loadAll"
    />
    <BankLinkClientPaymentDialog
      v-model:visible="existingClientPaymentDialogVisible"
      :transaction="existingClientPaymentTransaction"
      @saved="loadAll"
    />
    <BankSupplierPaymentDialog
      v-model:visible="supplierPaymentDialogVisible"
      :transaction="supplierPaymentTransaction"
      @saved="loadAll"
    />
    <BankLinkSupplierPaymentDialog
      v-model:visible="existingSupplierPaymentDialogVisible"
      :transaction="existingSupplierPaymentTransaction"
      @saved="loadAll"
    />
    <BankNewDepositDialog
      v-model:visible="depositDialogVisible"
      :payments="undepositedPayments"
      @saved="loadAll"
    />
  </AppPage>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import InputText from 'primevue/inputtext'
import Tab from 'primevue/tab'
import TabList from 'primevue/tablist'
import TabPanel from 'primevue/tabpanel'
import TabPanels from 'primevue/tabpanels'
import Tabs from 'primevue/tabs'
import Tag from 'primevue/tag'
import ToggleButton from 'primevue/togglebutton'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import TrendLineChart, { type TrendLineChartSeries } from '../components/charts/TrendLineChart.vue'
import AppPage from '../components/ui/AppPage.vue'
import AppDateRangeFilter from '../components/ui/AppDateRangeFilter.vue'
import AppFilterMultiSelect from '../components/ui/AppFilterMultiSelect.vue'
import AppNumberRangeFilter from '../components/ui/AppNumberRangeFilter.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import AppStatCard from '../components/ui/AppStatCard.vue'
import BankNewTransactionDialog from '../components/bank/BankNewTransactionDialog.vue'
import BankImportStatementDialog from '../components/bank/BankImportStatementDialog.vue'
import BankClientPaymentDialog from '../components/bank/BankClientPaymentDialog.vue'
import BankLinkClientPaymentDialog from '../components/bank/BankLinkClientPaymentDialog.vue'
import BankSupplierPaymentDialog from '../components/bank/BankSupplierPaymentDialog.vue'
import BankLinkSupplierPaymentDialog from '../components/bank/BankLinkSupplierPaymentDialog.vue'
import BankNewDepositDialog from '../components/bank/BankNewDepositDialog.vue'
import {
  getBankBalance,
  getBankFundsChart,
  listDeposits,
  listTransactions,
  updateTransaction,
  confirmDeposit as confirmDepositApi,
  type BankTransaction,
  type Deposit,
  type FundsChartRow as BankFundsChartRow,
} from '@/api/bank'
import { listPayments, type Payment } from '@/api/payments'
import { useFiscalYearStore } from '@/stores/fiscalYear'
import { formatDisplayDate } from '@/utils/format'
import {
  dateRangeFilter,
  inFilter,
  numericRangeFilter,
  textFilter,
  useDataTableFilters,
} from '../composables/useDataTableFilters'

const { t } = useI18n()
const toast = useToast()
const fiscalYearStore = useFiscalYearStore()

// Core bank data
const balance = ref('0')
const fundsChartData = ref<BankFundsChartRow[]>([])
const transactions = ref<BankTransaction[]>([])
const deposits = ref<Deposit[]>([])
const pendingDeposits = ref<Deposit[]>([])
const undepositedPayments = ref<Payment[]>([])
const loadingTx = ref(false)
const loadingDeposits = ref(false)
const confirmingDepositId = ref<number | null>(null)
const activeTab = ref('transactions')
const unreconciledOnly = ref(false)

// Dialog visibility
const txDialogVisible = ref(false)
const importDialogVisible = ref(false)
const depositDialogVisible = ref(false)
const clientPaymentDialogVisible = ref(false)
const existingClientPaymentDialogVisible = ref(false)
const supplierPaymentDialogVisible = ref(false)
const existingSupplierPaymentDialogVisible = ref(false)

// Selected transactions for dialogs
const clientPaymentTransaction = ref<BankTransaction | null>(null)
const existingClientPaymentTransaction = ref<BankTransaction | null>(null)
const supplierPaymentTransaction = ref<BankTransaction | null>(null)
const existingSupplierPaymentTransaction = ref<BankTransaction | null>(null)

const sourceOptions = [
  { label: t('bank.sources.manual'), value: 'manual' },
  { label: t('bank.sources.import'), value: 'import' },
  { label: t('bank.sources.system_opening'), value: 'system_opening' },
]

const categoryOptions = [
  { label: t('bank.categories.customer_payment'), value: 'customer_payment' },
  { label: t('bank.categories.cheque_deposit'), value: 'cheque_deposit' },
  { label: t('bank.categories.cash_deposit'), value: 'cash_deposit' },
  { label: t('bank.categories.supplier_payment'), value: 'supplier_payment' },
  { label: t('bank.categories.salary'), value: 'salary' },
  { label: t('bank.categories.social_charge'), value: 'social_charge' },
  { label: t('bank.categories.bank_fee'), value: 'bank_fee' },
  { label: t('bank.categories.internal_transfer'), value: 'internal_transfer' },
  { label: t('bank.categories.grant'), value: 'grant' },
  { label: t('bank.categories.sepa_debit'), value: 'sepa_debit' },
  { label: t('bank.categories.other_credit'), value: 'other_credit' },
  { label: t('bank.categories.other_debit'), value: 'other_debit' },
  { label: t('bank.categories.uncategorized'), value: 'uncategorized' },
]

const yesNoOptions = [
  { label: t('common.yes'), value: true },
  { label: t('common.no'), value: false },
]

const transactionRows = computed(() =>
  transactions.value.map((tx) => ({
    ...tx,
    amount_value: parseFloat(tx.amount),
    balance_after_value: parseFloat(tx.balance_after),
    reconciled_label: tx.reconciled ? t('common.yes') : t('common.no'),
    detected_category_label: t(`bank.categories.${tx.detected_category}`),
    source_label: t(`bank.sources.${tx.source}`),
  })),
)

const depositRows = computed(() =>
  deposits.value.map((deposit) => ({
    ...deposit,
    type_label: t(`bank.deposit_types.${deposit.type}`),
    total_amount_value: parseFloat(deposit.total_amount),
    payment_count: deposit.payment_ids?.length || 0,
    payment_count_label: `${deposit.payment_ids?.length || 0}`,
    confirmed_label: deposit.confirmed
      ? t('bank.deposit_status.confirmed')
      : t('bank.deposit_status.pending'),
  })),
)

const {
  filters: transactionTableFilters,
  globalFilter: transactionGlobalFilter,
  displayedRows: displayedTransactions,
  hasActiveFilters: transactionHasActiveFilters,
  resetFilters: resetTransactionFilters,
  syncDisplayedRows: syncDisplayedTransactions,
} = useDataTableFilters(transactionRows, {
  global: textFilter(''),
  date: dateRangeFilter(),
  amount_value: numericRangeFilter(),
  description: textFilter(),
  reference: textFilter(),
  balance_after_value: numericRangeFilter(),
  reconciled: inFilter(),
  detected_category: inFilter(),
  source: inFilter(),
})

const {
  filters: depositTableFilters,
  globalFilter: depositGlobalFilter,
  displayedRows: displayedDeposits,
  hasActiveFilters: depositHasActiveFilters,
  resetFilters: resetDepositFilters,
  syncDisplayedRows: syncDisplayedDeposits,
} = useDataTableFilters(depositRows, {
  global: textFilter(''),
  date: dateRangeFilter(),
  type: inFilter(),
  total_amount_value: numericRangeFilter(),
  bank_reference: textFilter(),
  payment_count: numericRangeFilter(),
  confirmed: inFilter(),
})

const activeGlobalFilter = computed({
  get: () =>
    activeTab.value === 'transactions' ? transactionGlobalFilter.value : depositGlobalFilter.value,
  set: (value: string) => {
    if (activeTab.value === 'transactions') {
      transactionGlobalFilter.value = value
    } else {
      depositGlobalFilter.value = value
    }
  },
})

const activeHasFilters = computed(() =>
  activeTab.value === 'transactions'
    ? transactionHasActiveFilters.value
    : depositHasActiveFilters.value,
)

function pickLatestVisibleBalanceAfter(
  rows: Array<{ id: number; date: string; balance_after: string }>,
): string | null {
  if (rows.length === 0) return null
  const latestRow = rows.reduce((latest, current) => {
    if (current.date > latest.date) return current
    if (current.date === latest.date && current.id > latest.id) return current
    return latest
  })
  return latestRow.balance_after
}

const scopedBalance = computed(() => pickLatestVisibleBalanceAfter(displayedTransactions.value))
const displayBalanceValue = computed(() => formatAmount(scopedBalance.value ?? balance.value))
const selectedPeriodLabel = computed(
  () => fiscalYearStore.selectedFiscalYear?.name ?? t('app.all_fiscal_years'),
)
const currentBalanceCaption = computed(() =>
  transactionHasActiveFilters.value || fiscalYearStore.selectedFiscalYear
    ? t('bank.metrics.visible_scope_caption')
    : t('bank.metrics.current_balance_caption'),
)
const displayedPeriodVariation = computed(() =>
  displayedTransactions.value.reduce(
    (total, tx) => total + parseFloat(tx.amount),
    0,
  ),
)
const displayedPeriodVariationTone = computed(() => {
  if (displayedPeriodVariation.value > 0) return 'success'
  if (displayedPeriodVariation.value < 0) return 'danger'
  return 'warn'
})
const periodVariationCaption = computed(() =>
  transactionHasActiveFilters.value
    ? t('bank.metrics.visible_scope_caption')
    : t('bank.metrics.period_variation_caption', { period: selectedPeriodLabel.value }),
)
const fundsChartSeries = computed<TrendLineChartSeries[]>(() => [
  { key: 'total', label: t('bank.funds_chart_total'), color: '#0f766e', fill: true },
  { key: 'current_account', label: t('bank.funds_chart_current_account'), color: '#2563eb' },
  { key: 'savings_account', label: t('bank.funds_chart_savings_account'), color: '#ea580c', dashed: true },
])

function formatAmount(value: string | number): string {
  return `${parseFloat(String(value)).toFixed(2)} €`
}

function formatEspecesSummary(denominationDetails: string | null): string {
  if (!denominationDetails) return t('bank.deposit_especes_summary_no_denom')
  try {
    const lines: { value: number; count: number }[] = JSON.parse(denominationDetails)
    if (!lines.length) return t('bank.deposit_especes_summary_no_denom')
    return lines
      .filter((l) => l.count > 0)
      .map((l) => `${l.count}×${l.value % 1 === 0 ? l.value : l.value.toFixed(2)} €`)
      .join(' + ')
  } catch {
    return t('bank.deposit_especes_summary_no_denom')
  }
}

function formatSignedAmount(value: number): string {
  return value > 0 ? `+${formatAmount(value)}` : formatAmount(value)
}

function resetActiveFilters() {
  if (activeTab.value === 'transactions') {
    resetTransactionFilters()
  } else {
    resetDepositFilters()
  }
}

function canCreateClientPayment(tx: BankTransaction): boolean {
  return (
    !tx.reconciled &&
    parseFloat(tx.amount) > 0 &&
    ['customer_payment', 'other_credit'].includes(tx.detected_category)
  )
}

function canLinkExistingClientPayment(tx: BankTransaction): boolean {
  return canCreateClientPayment(tx)
}

function canCreateSupplierPayment(tx: BankTransaction): boolean {
  return (
    !tx.reconciled &&
    parseFloat(tx.amount) < 0 &&
    ['supplier_payment', 'other_debit'].includes(tx.detected_category)
  )
}

function canLinkExistingSupplierPayment(tx: BankTransaction): boolean {
  return canCreateSupplierPayment(tx)
}

async function reconcile(tx: BankTransaction): Promise<void> {
  await updateTransaction(tx.id, { reconciled: true })
  await loadTransactions()
}

function openClientPaymentDialog(tx: BankTransaction): void {
  clientPaymentTransaction.value = tx
  clientPaymentDialogVisible.value = true
}

function openExistingClientPaymentDialog(tx: BankTransaction): void {
  existingClientPaymentTransaction.value = tx
  existingClientPaymentDialogVisible.value = true
}

function openSupplierPaymentDialog(tx: BankTransaction): void {
  supplierPaymentTransaction.value = tx
  supplierPaymentDialogVisible.value = true
}

function openExistingSupplierPaymentDialog(tx: BankTransaction): void {
  existingSupplierPaymentTransaction.value = tx
  existingSupplierPaymentDialogVisible.value = true
}

async function openDepositDialog(): Promise<void> {
  undepositedPayments.value = await listPayments({
    invoice_type: 'client',
    undeposited_only: true,
    from_date: fiscalYearStore.selectedFiscalYear?.start_date,
    to_date: fiscalYearStore.selectedFiscalYear?.end_date,
  })
  depositDialogVisible.value = true
}

async function loadTransactions(): Promise<void> {
  loadingTx.value = true
  try {
    transactions.value = await listTransactions({
      from_date: fiscalYearStore.selectedFiscalYear?.start_date,
      to_date: fiscalYearStore.selectedFiscalYear?.end_date,
      unreconciled_only: unreconciledOnly.value,
    })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    loadingTx.value = false
  }
}

async function confirmDeposit(deposit: Deposit): Promise<void> {
  confirmingDepositId.value = deposit.id
  try {
    await confirmDepositApi(deposit.id)
    toast.add({ severity: 'success', summary: t('bank.deposit_confirmed_success'), life: 3000 })
    await loadDeposits()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    confirmingDepositId.value = null
  }
}

async function loadDeposits(): Promise<void> {
  loadingDeposits.value = true
  try {
    const [all, pending] = await Promise.all([
      listDeposits({
        from_date: fiscalYearStore.selectedFiscalYear?.start_date,
        to_date: fiscalYearStore.selectedFiscalYear?.end_date,
      }),
      listDeposits({ confirmed: false }),
    ])
    deposits.value = all
    pendingDeposits.value = pending
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    loadingDeposits.value = false
  }
}

async function loadFundsChart(): Promise<void> {
  try {
    fundsChartData.value = await getBankFundsChart(6)
  } catch {
    fundsChartData.value = []
  }
}

async function loadAll(): Promise<void> {
  const [b] = await Promise.all([
    getBankBalance(),
    loadTransactions(),
    loadDeposits(),
    loadFundsChart(),
  ])
  balance.value = b.balance
}

watch(
  () => fiscalYearStore.selectedFiscalYearId,
  (newId, oldId) => {
    if (!fiscalYearStore.initialized || newId === oldId) return
    void loadAll()
  },
)

onMounted(async () => {
  await fiscalYearStore.initialize()
  await loadAll()
})
</script>

<style scoped>
.bank-chart-panel__intro {
  margin: 0 0 var(--app-space-4);
  color: var(--p-text-muted-color);
}

.bank-panel-toolbar {
  margin-bottom: var(--app-space-4);
}

:deep(.bank-table__description) {
  min-width: 20rem;
}

:deep(.bank-table__reference) {
  min-width: 12rem;
}

:deep(.bank-table__amount) {
  width: 8rem;
}

:deep(.bank-table__balance) {
  width: 6.5rem;
}

:deep(.bank-table__reconciled) {
  width: 5.5rem;
}

:deep(.bank-table__category) {
  width: 7.5rem;
}

:deep(.bank-table__source) {
  width: 5.25rem;
}

:deep(.bank-detected-category-tag) {
  border: 1px solid color-mix(in srgb, var(--app-surface-border) 82%, transparent 18%);
  background: color-mix(in srgb, var(--app-surface-muted) 84%, var(--app-surface-bg) 16%);
  color: color-mix(in srgb, var(--p-text-muted-color) 78%, var(--p-text-color) 22%);
}

:deep(.bank-detected-category-tag .p-tag-label) {
  white-space: nowrap;
  font-size: 0.78rem;
  line-height: 1;
}

:global(html.dark-mode) .bank-detected-category-tag {
  color: color-mix(in srgb, var(--p-surface-100) 82%, var(--p-text-color) 18%);
  border-color: color-mix(in srgb, var(--app-surface-border) 70%, transparent 30%);
  background: color-mix(in srgb, var(--app-surface-muted) 70%, var(--app-surface-bg) 30%);
}

.bank-positive {
  color: var(--p-green-600);
}

.bank-negative {
  color: var(--p-red-500);
}

:deep(.p-tabpanels) {
  padding-inline: 0;
  padding-bottom: 0;
}

.bank-pending-deposits {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
}

.bank-pending-deposit-row {
  display: flex;
  align-items: center;
  gap: var(--app-space-3);
  padding: var(--app-space-3) var(--app-space-4);
  background: var(--app-surface-muted);
  border: 1px solid var(--app-surface-border);
  border-radius: var(--app-radius);
}

.bank-pending-deposit-row__tag {
  flex-shrink: 0;
}

.bank-pending-deposit-row__date {
  font-variant-numeric: tabular-nums;
  min-width: 6rem;
}

.bank-pending-deposit-row__summary {
  flex: 1;
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
}

.bank-pending-deposit-row__amount {
  font-weight: 600;
  min-width: 7rem;
  text-align: right;
}
</style>
