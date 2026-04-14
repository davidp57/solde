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
      <AppStatCard :label="t('bank.balance')" :value="formatAmount(balance)" />
      <AppStatCard
        :label="t('bank.transactions_title')"
        :value="filteredTransactions.length"
        :caption="`${transactions.length} total`"
      />
      <AppStatCard
        :label="t('bank.deposits_title')"
        :value="filteredDeposits.length"
        :caption="`${undepositedPayments.length} paiements en attente`"
        tone="warn"
      />
    </section>

    <AppPanel :title="t('bank.title')" dense>
      <div class="app-toolbar">
        <div class="app-filter-grid">
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('common.filter_placeholder') }}</label>
            <InputText v-model="filterText" :placeholder="t('common.filter_placeholder')" />
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
              :value="filteredTransactions"
              :loading="loadingTx"
              class="app-data-table"
              striped-rows
              paginator
              :rows="20"
              :rows-per-page-options="[20, 50, 100, 500]"
              data-key="id"
              size="small"
              row-hover
            >
              <Column field="date" :header="t('bank.tx_date')" sortable>
                <template #body="{ data }">{{ formatDisplayDate(data.date) }}</template>
              </Column>
              <Column field="amount" :header="t('bank.tx_amount')" class="app-money">
                <template #body="{ data }">
                  <span :class="parseFloat(data.amount) >= 0 ? 'bank-positive' : 'bank-negative'">
                    {{ formatAmount(data.amount) }}
                  </span>
                </template>
              </Column>
              <Column field="description" :header="t('bank.tx_description')" />
              <Column field="reference" :header="t('bank.tx_reference')" />
              <Column field="balance_after" :header="t('bank.tx_balance')">
                <template #body="{ data }">{{ formatAmount(data.balance_after) }}</template>
              </Column>
              <Column field="reconciled" :header="t('bank.tx_reconciled')">
                <template #body="{ data }">
                  <i
                    :class="
                      data.reconciled
                        ? 'pi pi-check-circle text-green-500'
                        : 'pi pi-circle text-surface-400'
                    "
                  />
                </template>
              </Column>
              <Column field="source" :header="t('bank.tx_source')">
                <template #body="{ data }">
                  <Tag :value="t(`bank.sources.${data.source}`)" severity="secondary" />
                </template>
              </Column>
              <Column :header="t('common.actions')" style="width: 6rem">
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
                <div class="app-empty-state">{{ t('accounting.balance.empty') }}</div>
              </template>
            </DataTable>
          </TabPanel>

          <TabPanel value="deposits">
            <DataTable
              :value="filteredDeposits"
              :loading="loadingDeposits"
              class="app-data-table"
              striped-rows
              paginator
              :rows="20"
              :rows-per-page-options="[20, 50, 100, 500]"
              data-key="id"
              size="small"
              row-hover
            >
              <Column field="date" :header="t('bank.deposit_date')" sortable>
                <template #body="{ data }">{{ formatDisplayDate(data.date) }}</template>
              </Column>
              <Column field="type" :header="t('bank.deposit_type')">
                <template #body="{ data }">
                  <Tag :value="t(`bank.deposit_types.${data.type}`)" />
                </template>
              </Column>
              <Column field="total_amount" :header="t('bank.deposit_total')" class="app-money">
                <template #body="{ data }">{{ formatAmount(data.total_amount) }}</template>
              </Column>
              <Column field="bank_reference" :header="t('bank.deposit_bank_ref')" />
              <Column field="payment_ids" :header="t('bank.deposit_payments')">
                <template #body="{ data }">
                  {{ data.payment_ids?.length || 0 }} paiements
                </template>
              </Column>
              <template #empty>
                <div class="app-empty-state">{{ t('accounting.balance.empty') }}</div>
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
import { useTableFilter, applyFilter } from '../composables/useTableFilter'

const { t } = useI18n()
const toast = useToast()
const fiscalYearStore = useFiscalYearStore()

const balance = ref('0')
const transactions = ref<BankTransaction[]>([])
const { filterText, filtered: filteredTransactions } = useTableFilter(transactions)
const deposits = ref<Deposit[]>([])
const filteredDeposits = computed(() => applyFilter(deposits.value, filterText.value))
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
