<template>
  <AppPage width="wide">
    <AppPageHeader :eyebrow="t('ui.page.collection_eyebrow')" :title="t('bank.title')">
      <template #actions>
        <Button
          :label="t('bank.import_csv')"
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
        :value="formatAmount(balance)"
        :caption="t('bank.metrics.current_balance_caption')"
      />
      <AppStatCard
        :label="t('bank.period_variation')"
        :value="formatSignedAmount(periodVariation)"
        :caption="t('bank.metrics.period_variation_caption', { period: selectedPeriodLabel })"
        :tone="periodVariationTone"
      />
      <AppStatCard
        :label="t('bank.transactions_title')"
        :value="displayedTransactions.length"
        :caption="t('bank.metrics.transactions_total', { count: transactions.length })"
      />
      <AppStatCard
        :label="t('bank.deposits_title')"
        :value="displayedDeposits.length"
        :caption="t('bank.metrics.pending_payments', { count: undepositedPayments.length })"
        tone="warn"
      />
    </section>

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
                'source_label',
              ]"
              data-key="id"
              size="small"
              row-hover
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
                class="app-money"
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
                :header="t('bank.tx_balance')"
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
                :header="t('bank.tx_reconciled')"
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
                <template #filter="{ filterModel }">
                  <AppFilterMultiSelect
                    v-model="filterModel.value"
                    :options="yesNoOptions"
                    option-label="label"
                    option-value="value"
                    :placeholder="t('common.all')"
                    display="chip"
                    show-clear
                  />
                </template>
              </Column>
              <Column
                field="source_label"
                :header="t('bank.tx_source')"
                class="bank-table__source"
                sortable
                filter-field="source"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">
                  <Tag :value="t(`bank.sources.${data.source}`)" severity="secondary" />
                </template>
                <template #filter="{ filterModel }">
                  <AppFilterMultiSelect
                    v-model="filterModel.value"
                    :options="sourceOptions"
                    option-label="label"
                    option-value="value"
                    :placeholder="t('common.all')"
                    display="chip"
                    show-clear
                  />
                </template>
              </Column>
              <Column :header="t('common.actions')" style="width: 4.5rem">
                <template #body="{ data }">
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
                <template #filter="{ filterModel }">
                  <AppFilterMultiSelect
                    v-model="filterModel.value"
                    :options="depositTypeOptions"
                    option-label="label"
                    option-value="value"
                    :placeholder="t('common.all')"
                    display="chip"
                    show-clear
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
              <template #empty>
                <div class="app-empty-state">{{ t('bank.deposits_empty') }}</div>
              </template>
            </DataTable>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </AppPanel>

    <!-- Add transaction dialog -->
    <Dialog
      v-model:visible="txDialogVisible"
      :header="t('bank.new_transaction')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <form class="app-dialog-form bank-form" @submit.prevent="submitTransaction">
        <section class="app-dialog-intro">
          <p class="app-dialog-intro__eyebrow">{{ t('bank.transactions_title') }}</p>
          <p class="app-dialog-intro__text">{{ t('bank.transaction_intro') }}</p>
        </section>
        <section class="app-dialog-section">
          <div class="app-form-grid">
            <div class="app-field">
              <label class="app-field__label">{{ t('bank.tx_date') }}</label>
              <DatePicker v-model="txForm.date" date-format="yy-mm-dd" show-icon />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('bank.tx_amount') }}</label>
              <InputNumber
                v-model="txForm.amount"
                mode="decimal"
                :min-fraction-digits="2"
                :max-fraction-digits="2"
              />
            </div>
            <div class="app-field app-field--full">
              <label class="app-field__label">{{ t('bank.tx_description') }}</label>
              <InputText v-model="txForm.description" />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('bank.tx_reference') }}</label>
              <InputText v-model="txForm.reference" />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('bank.tx_balance') }}</label>
              <InputNumber
                v-model="txForm.balance_after"
                mode="decimal"
                :min-fraction-digits="2"
                :max-fraction-digits="2"
              />
            </div>
          </div>
        </section>
        <div class="app-form-actions">
          <Button
            :label="t('common.cancel')"
            severity="secondary"
            text
            @click="txDialogVisible = false"
          />
          <Button type="submit" :label="t('common.save')" :loading="saving" />
        </div>
      </form>
    </Dialog>

    <!-- CSV import dialog -->
    <Dialog
      v-model:visible="importDialogVisible"
      :header="t('bank.import_dialog_title')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div class="app-dialog-form bank-form">
        <section class="app-dialog-intro">
          <p class="app-dialog-intro__eyebrow">{{ t('bank.import_csv') }}</p>
          <p class="app-dialog-intro__text">{{ t('bank.import_intro') }}</p>
        </section>
        <section class="app-dialog-section">
          <div class="app-field">
            <label class="app-field__label">{{ t('bank.import_paste_label') }}</label>
            <Textarea v-model="csvContent" rows="8" class="font-mono text-sm" />
          </div>
        </section>
        <div class="app-form-actions">
          <Button
            :label="t('common.cancel')"
            severity="secondary"
            text
            @click="importDialogVisible = false"
          />
          <Button
            :label="t('bank.import_csv')"
            icon="pi pi-upload"
            :loading="saving"
            @click="submitImport"
          />
        </div>
      </div>
    </Dialog>

    <!-- Create deposit dialog -->
    <Dialog
      v-model:visible="depositDialogVisible"
      :header="t('bank.new_deposit')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div class="app-dialog-form bank-form">
        <section class="app-dialog-intro">
          <p class="app-dialog-intro__eyebrow">{{ t('bank.deposits_title') }}</p>
          <p class="app-dialog-intro__text">{{ t('bank.deposit_intro') }}</p>
        </section>
        <section class="app-dialog-section">
          <div class="app-form-grid">
            <div class="app-field">
              <label class="app-field__label">{{ t('bank.deposit_date') }}</label>
              <DatePicker v-model="depositForm.date" date-format="yy-mm-dd" show-icon />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('bank.deposit_type') }}</label>
              <Select
                v-model="depositForm.type"
                :options="depositTypeOptions"
                option-label="label"
                option-value="value"
              />
            </div>
            <div class="app-field app-field--full">
              <label class="app-field__label">{{ t('bank.deposit_bank_ref') }}</label>
              <InputText v-model="depositForm.bank_reference" />
            </div>
          </div>
        </section>
        <section class="app-dialog-section">
          <div class="app-dialog-section__header">
            <h3 class="app-dialog-section__title">{{ t('bank.deposit_selection_title') }}</h3>
            <p class="app-dialog-section__copy">{{ t('bank.deposit_selection_subtitle') }}</p>
          </div>
          <Message v-if="undepositedPayments.length === 0" severity="warn">
            {{ t('bank.deposit_empty') }}
          </Message>
          <p v-if="undepositedPayments.length === 0" class="app-dialog-note">
            {{ t('bank.deposit_empty_hint') }}
          </p>
          <div v-else class="app-dialog-list">
            <label
              v-for="p in undepositedPayments"
              :key="p.id"
              class="app-dialog-list__item bank-payment-option"
            >
              <Checkbox v-model="depositForm.payment_ids" :value="p.id" />
              <span class="app-dialog-list__meta">
                <span class="app-dialog-list__title"
                  >{{ formatDisplayDate(p.date) }} — {{ formatAmount(p.amount) }}</span
                >
                <span class="app-dialog-list__caption">{{
                  t(`payments.methods.${p.method}`)
                }}</span>
              </span>
            </label>
          </div>
        </section>
        <div class="app-form-actions">
          <Button
            :label="t('common.cancel')"
            severity="secondary"
            text
            @click="depositDialogVisible = false"
          />
          <Button
            :label="t('common.save')"
            :loading="saving"
            :disabled="depositForm.payment_ids.length === 0"
            @click="submitDeposit"
          />
        </div>
      </div>
    </Dialog>
  </AppPage>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import DatePicker from 'primevue/datepicker'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Select from 'primevue/select'
import Tab from 'primevue/tab'
import TabList from 'primevue/tablist'
import TabPanel from 'primevue/tabpanel'
import TabPanels from 'primevue/tabpanels'
import Tabs from 'primevue/tabs'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'
import ToggleButton from 'primevue/togglebutton'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import AppPage from '../components/ui/AppPage.vue'
import AppDateRangeFilter from '../components/ui/AppDateRangeFilter.vue'
import AppFilterMultiSelect from '../components/ui/AppFilterMultiSelect.vue'
import AppNumberRangeFilter from '../components/ui/AppNumberRangeFilter.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import AppStatCard from '../components/ui/AppStatCard.vue'
import {
  addTransaction,
  createDeposit,
  getBankBalance,
  importCsv,
  listDeposits,
  listTransactions,
  updateTransaction,
  type BankTransaction,
  type Deposit,
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

const balance = ref('0')
const transactions = ref<BankTransaction[]>([])
const deposits = ref<Deposit[]>([])
const undepositedPayments = ref<Payment[]>([])
const loadingTx = ref(false)
const loadingDeposits = ref(false)
const activeTab = ref('transactions')
const unreconciledOnly = ref(false)
const txDialogVisible = ref(false)
const importDialogVisible = ref(false)
const depositDialogVisible = ref(false)
const saving = ref(false)
const csvContent = ref('')

const depositTypeOptions = [
  { label: t('bank.deposit_types.cheques'), value: 'cheques' },
  { label: t('bank.deposit_types.especes'), value: 'especes' },
]

const sourceOptions = [
  { label: t('bank.sources.manual'), value: 'manual' },
  { label: t('bank.sources.import'), value: 'import' },
]

const yesNoOptions = [
  { label: t('common.yes'), value: true },
  { label: t('common.no'), value: false },
]

const transactionRows = computed(() =>
  transactions.value.map((transaction) => ({
    ...transaction,
    amount_value: parseFloat(transaction.amount),
    balance_after_value: parseFloat(transaction.balance_after),
    reconciled_label: transaction.reconciled ? t('common.yes') : t('common.no'),
    source_label: t(`bank.sources.${transaction.source}`),
  })),
)

const depositRows = computed(() =>
  deposits.value.map((deposit) => ({
    ...deposit,
    type_label: t(`bank.deposit_types.${deposit.type}`),
    total_amount_value: parseFloat(deposit.total_amount),
    payment_count: deposit.payment_ids?.length || 0,
    payment_count_label: `${deposit.payment_ids?.length || 0}`,
  })),
)

const periodVariation = computed(() =>
  transactions.value.reduce((total, transaction) => total + parseFloat(transaction.amount), 0),
)

const selectedPeriodLabel = computed(
  () => fiscalYearStore.selectedFiscalYear?.name ?? t('app.all_fiscal_years'),
)

const periodVariationTone = computed(() => {
  if (periodVariation.value > 0) return 'success'
  if (periodVariation.value < 0) return 'danger'
  return 'warn'
})

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

function resetActiveFilters() {
  if (activeTab.value === 'transactions') {
    resetTransactionFilters()
    return
  }

  resetDepositFilters()
}

const txForm = ref({
  date: new Date(),
  amount: 0,
  description: '',
  reference: '',
  balance_after: 0,
})
const depositForm = ref({
  date: new Date(),
  type: 'cheques' as 'cheques' | 'especes',
  bank_reference: '',
  payment_ids: [] as number[],
})

function formatAmount(value: string | number): string {
  return `${parseFloat(String(value)).toFixed(2)} €`
}

function formatSignedAmount(value: number): string {
  if (value > 0) {
    return `+${formatAmount(value)}`
  }
  return formatAmount(value)
}

function toIsoDate(d: Date | string): string {
  if (typeof d === 'string') return d
  return d.toISOString().slice(0, 10)
}

async function loadTransactions() {
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

async function loadDeposits() {
  loadingDeposits.value = true
  try {
    deposits.value = await listDeposits({
      from_date: fiscalYearStore.selectedFiscalYear?.start_date,
      to_date: fiscalYearStore.selectedFiscalYear?.end_date,
    })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    loadingDeposits.value = false
  }
}

async function loadAll() {
  const [b] = await Promise.all([getBankBalance(), loadTransactions(), loadDeposits()])
  balance.value = b.balance
}

async function reconcile(tx: BankTransaction) {
  await updateTransaction(tx.id, { reconciled: true })
  await loadTransactions()
}

async function submitTransaction() {
  saving.value = true
  try {
    await addTransaction({
      date: toIsoDate(txForm.value.date),
      amount: String(txForm.value.amount),
      description: txForm.value.description,
      reference: txForm.value.reference || null,
      balance_after: String(txForm.value.balance_after),
    })
    txDialogVisible.value = false
    await Promise.all([
      getBankBalance().then((b) => (balance.value = b.balance)),
      loadTransactions(),
    ])
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    saving.value = false
  }
}

async function submitImport() {
  saving.value = true
  try {
    const imported = await importCsv(csvContent.value)
    importDialogVisible.value = false
    csvContent.value = ''
    toast.add({
      severity: 'success',
      summary: t('bank.import_success', { n: imported.length }),
      life: 3000,
    })
    await Promise.all([
      getBankBalance().then((b) => (balance.value = b.balance)),
      loadTransactions(),
    ])
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    saving.value = false
  }
}

async function openDepositDialog() {
  undepositedPayments.value = await listPayments({
    invoice_type: 'client',
    undeposited_only: true,
    from_date: fiscalYearStore.selectedFiscalYear?.start_date,
    to_date: fiscalYearStore.selectedFiscalYear?.end_date,
  })
  depositForm.value.payment_ids = []
  depositDialogVisible.value = true
}

async function submitDeposit() {
  saving.value = true
  try {
    await createDeposit({
      date: toIsoDate(depositForm.value.date),
      type: depositForm.value.type,
      payment_ids: depositForm.value.payment_ids,
      bank_reference: depositForm.value.bank_reference || null,
    })
    depositDialogVisible.value = false
    await loadDeposits()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    saving.value = false
  }
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
.bank-panel-toolbar {
  margin-bottom: var(--app-space-4);
}

:deep(.bank-table__description) {
  min-width: 18rem;
}

:deep(.bank-table__reconciled) {
  width: 7rem;
}

:deep(.bank-table__source) {
  width: 6.5rem;
}

.bank-form {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.bank-positive {
  color: var(--p-green-600);
}

.bank-negative {
  color: var(--p-red-500);
}

.bank-payment-option {
  cursor: pointer;
}

.bank-payment-option :deep(.p-checkbox) {
  margin-top: 0.15rem;
}

:deep(.p-tabpanels) {
  padding-inline: 0;
  padding-bottom: 0;
}
</style>
