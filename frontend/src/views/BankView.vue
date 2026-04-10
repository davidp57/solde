<template>
  <div class="bank-view p-4">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-2xl font-semibold">{{ t('bank.title') }}</h2>
      <div class="flex gap-2">
        <Button :label="t('bank.import_csv')" icon="pi pi-upload" severity="secondary" @click="importDialogVisible = true" />
        <Button :label="t('bank.new_deposit')" icon="pi pi-inbox" severity="secondary" @click="depositDialogVisible = true" />
        <Button :label="t('bank.new_transaction')" icon="pi pi-plus" @click="txDialogVisible = true" />
      </div>
    </div>

    <!-- Balance card -->
    <div class="balance-card mb-6">
      <span class="label">{{ t('bank.balance') }}</span>
      <span class="amount">{{ formatAmount(balance) }}</span>
    </div>

    <!-- Generic filter -->
    <div class="mb-3">
      <InputText v-model="filterText" :placeholder="t('common.filter_placeholder')" class="w-64" />
    </div>

    <!-- Tabs -->
    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab value="transactions">{{ t('bank.transactions_title') }}</Tab>
        <Tab value="deposits">{{ t('bank.deposits_title') }}</Tab>
      </TabList>

      <TabPanels>
        <TabPanel value="transactions">
          <div class="flex gap-2 mb-3">
            <ToggleButton
              v-model="unreconciledOnly"
              :on-label="t('bank.tx_reconciled')"
              :off-label="t('bank.tx_reconciled')"
              @change="loadTransactions"
            />
          </div>
          <DataTable :value="filteredTransactions" :loading="loadingTx" striped-rows paginator :rows="20" data-key="id">
            <Column field="date" :header="t('bank.tx_date')" sortable />
            <Column field="amount" :header="t('bank.tx_amount')">
              <template #body="{ data }">
                <span :class="parseFloat(data.amount) >= 0 ? 'text-green-600' : 'text-red-500'">
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
                <i :class="data.reconciled ? 'pi pi-check-circle text-green-500' : 'pi pi-circle text-surface-400'" />
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
          </DataTable>
        </TabPanel>

        <TabPanel value="deposits">
          <DataTable :value="filteredDeposits" :loading="loadingDeposits" striped-rows paginator :rows="20" data-key="id">
            <Column field="date" :header="t('bank.deposit_date')" sortable />
            <Column field="type" :header="t('bank.deposit_type')">
              <template #body="{ data }">
                <Tag :value="t(`bank.deposit_types.${data.type}`)" />
              </template>
            </Column>
            <Column field="total_amount" :header="t('bank.deposit_total')">
              <template #body="{ data }">{{ formatAmount(data.total_amount) }}</template>
            </Column>
            <Column field="bank_reference" :header="t('bank.deposit_bank_ref')" />
            <Column field="payment_ids" :header="t('bank.deposit_payments')">
              <template #body="{ data }">
                {{ data.payment_ids?.length || 0 }} paiements
              </template>
            </Column>
          </DataTable>
        </TabPanel>
      </TabPanels>
    </Tabs>

    <!-- Add transaction dialog -->
    <Dialog v-model:visible="txDialogVisible" :header="t('bank.new_transaction')" modal :style="{ width: '420px' }">
      <form class="flex flex-col gap-3" @submit.prevent="submitTransaction">
        <div class="flex flex-col gap-1">
          <label>{{ t('bank.tx_date') }}</label>
          <DatePicker v-model="txForm.date" date-format="yy-mm-dd" show-icon />
        </div>
        <div class="flex flex-col gap-1">
          <label>{{ t('bank.tx_amount') }}</label>
          <InputNumber v-model="txForm.amount" mode="decimal" :min-fraction-digits="2" :max-fraction-digits="2" />
        </div>
        <div class="flex flex-col gap-1">
          <label>{{ t('bank.tx_description') }}</label>
          <InputText v-model="txForm.description" />
        </div>
        <div class="flex flex-col gap-1">
          <label>{{ t('bank.tx_reference') }}</label>
          <InputText v-model="txForm.reference" />
        </div>
        <div class="flex flex-col gap-1">
          <label>{{ t('bank.tx_balance') }}</label>
          <InputNumber v-model="txForm.balance_after" mode="decimal" :min-fraction-digits="2" :max-fraction-digits="2" />
        </div>
        <div class="flex justify-end gap-2 mt-2">
          <Button :label="t('common.cancel')" severity="secondary" text @click="txDialogVisible = false" />
          <Button type="submit" :label="t('common.save')" :loading="saving" />
        </div>
      </form>
    </Dialog>

    <!-- CSV import dialog -->
    <Dialog v-model:visible="importDialogVisible" :header="t('bank.import_dialog_title')" modal :style="{ width: '560px' }">
      <div class="flex flex-col gap-3">
        <div class="flex flex-col gap-1">
          <label>{{ t('bank.import_paste_label') }}</label>
          <Textarea v-model="csvContent" rows="8" class="font-mono text-sm" />
        </div>
        <div class="flex justify-end gap-2">
          <Button :label="t('common.cancel')" severity="secondary" text @click="importDialogVisible = false" />
          <Button :label="t('bank.import_csv')" icon="pi pi-upload" :loading="saving" @click="submitImport" />
        </div>
      </div>
    </Dialog>

    <!-- Create deposit dialog -->
    <Dialog v-model:visible="depositDialogVisible" :header="t('bank.new_deposit')" modal :style="{ width: '480px' }">
      <div class="flex flex-col gap-3">
        <div class="flex flex-col gap-1">
          <label>{{ t('bank.deposit_date') }}</label>
          <DatePicker v-model="depositForm.date" date-format="yy-mm-dd" show-icon />
        </div>
        <div class="flex flex-col gap-1">
          <label>{{ t('bank.deposit_type') }}</label>
          <Select v-model="depositForm.type" :options="depositTypeOptions" option-label="label" option-value="value" />
        </div>
        <div class="flex flex-col gap-1">
          <label>{{ t('bank.deposit_bank_ref') }}</label>
          <InputText v-model="depositForm.bank_reference" />
        </div>
        <Message v-if="undepositedPayments.length === 0" severity="warn">
          Aucun paiement en attente de remise en banque.
        </Message>
        <div v-else class="flex flex-col gap-1">
          <label>{{ t('bank.deposit_payments') }}</label>
          <div v-for="p in undepositedPayments" :key="p.id" class="flex items-center gap-2">
            <Checkbox v-model="depositForm.payment_ids" :value="p.id" />
            <span>{{ p.date }} — {{ formatAmount(p.amount) }} ({{ p.method }})</span>
          </div>
        </div>
        <div class="flex justify-end gap-2">
          <Button :label="t('common.cancel')" severity="secondary" text @click="depositDialogVisible = false" />
          <Button :label="t('common.save')" :loading="saving" :disabled="depositForm.payment_ids.length === 0" @click="submitDeposit" />
        </div>
      </div>
    </Dialog>
  </div>
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
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
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
import { useTableFilter, applyFilter } from '../composables/useTableFilter'

const { t } = useI18n()
const toast = useToast()

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

const txForm = ref({ date: new Date(), amount: 0, description: '', reference: '', balance_after: 0 })
const depositForm = ref({ date: new Date(), type: 'cheques' as 'cheques' | 'especes', bank_reference: '', payment_ids: [] as number[] })

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
    transactions.value = await listTransactions({ unreconciled_only: unreconciledOnly.value })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    loadingTx.value = false
  }
}

async function loadDeposits() {
  loadingDeposits.value = true
  try {
    deposits.value = await listDeposits()
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
    await Promise.all([getBankBalance().then((b) => (balance.value = b.balance)), loadTransactions()])
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
    toast.add({ severity: 'success', summary: t('bank.import_success', { n: imported.length }), life: 3000 })
    await Promise.all([getBankBalance().then((b) => (balance.value = b.balance)), loadTransactions()])
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    saving.value = false
  }
}

async function openDepositDialog() {
  undepositedPayments.value = await listPayments({ undeposited_only: true })
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

onMounted(loadAll)
</script>

<style scoped>
.balance-card {
  display: inline-flex;
  align-items: center;
  gap: 1rem;
  background: var(--p-surface-100);
  border-radius: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: 1px solid var(--p-surface-200);
}
.balance-card .label {
  font-size: 0.9rem;
  color: var(--p-text-muted-color);
}
.balance-card .amount {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--p-primary-color);
}
</style>
