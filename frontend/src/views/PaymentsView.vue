<template>
  <AppPage>
    <AppPageHeader
      :eyebrow="t('ui.page.collection_eyebrow')"
      :title="t('payments.title')"
      :subtitle="t('payments.subtitle')"
    />

    <section class="app-stat-grid">
      <AppStatCard
        :label="t('payments.metrics.visible')"
        :value="filtered.length"
        :caption="t('payments.metrics.total', { count: payments.length })"
      />
      <AppStatCard
        :label="t('payments.metrics.amount')"
        :value="formatAmount(totalAmount)"
        :caption="t('payments.metrics.average', { amount: formatAmount(averageAmount) })"
      />
      <AppStatCard
        :label="t('payments.metrics.undeposited')"
        :value="undepositedCount"
        :caption="t('payments.metrics.cheques', { count: chequeCount })"
        tone="warn"
      />
    </section>

    <AppPanel :title="t('payments.workspace_title')" :subtitle="t('payments.workspace_subtitle')">
      <div class="app-toolbar">
        <div class="app-toolbar__meta">
          <p class="app-toolbar__hint">{{ t('payments.filters_hint') }}</p>
          <span class="app-chip">{{
            t('payments.results_label', { count: filtered.length })
          }}</span>
        </div>

        <div class="app-filter-grid">
          <div class="app-field">
            <label class="app-field__label">{{ t('payments.filter_undeposited') }}</label>
            <ToggleButton
              v-model="undepositedOnly"
              :on-label="t('payments.filter_undeposited')"
              :off-label="t('payments.filter_undeposited')"
              @change="loadPayments"
            />
          </div>
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('common.filter_placeholder') }}</label>
            <InputText v-model="filterText" :placeholder="t('common.filter_placeholder')" />
          </div>
        </div>
      </div>

      <DataTable
        :value="filtered"
        :loading="loading"
        class="app-data-table payments-table"
        striped-rows
        paginator
        :rows="20"
        :rows-per-page-options="[20, 50, 100, 500]"
        data-key="id"
        size="small"
        row-hover
      >
        <Column field="date" :header="t('payments.date')" sortable>
          <template #body="{ data }">{{ formatDisplayDate(data.date) }}</template>
        </Column>
        <Column field="amount" :header="t('payments.amount')" class="app-money">
          <template #body="{ data }">
            {{ formatAmount(data.amount) }}
          </template>
        </Column>
        <Column field="method" :header="t('payments.method')">
          <template #body="{ data }">
            <Tag :value="t(`payments.methods.${data.method}`)" />
          </template>
        </Column>
        <Column field="reference" :header="t('payments.reference')">
          <template #body="{ data }">{{ paymentReference(data) }}</template>
        </Column>
        <Column field="cheque_number" :header="t('payments.cheque_number')" />
        <Column field="deposited" :header="t('payments.deposited')">
          <template #body="{ data }">
            <i
              :class="data.deposited ? 'pi pi-check text-green-500' : 'pi pi-times text-red-400'"
            />
          </template>
        </Column>
        <Column :header="t('common.actions')" class="payments-table__actions">
          <template #body="{ data }">
            <Button
              data-testid="payment-edit-button"
              icon="pi pi-pencil"
              size="small"
              severity="secondary"
              text
              @click="openEditDialog(data)"
            />
            <Button
              icon="pi pi-trash"
              size="small"
              severity="danger"
              text
              @click="confirmDelete(data)"
            />
          </template>
        </Column>
        <template #empty>
          <div class="app-empty-state">{{ t('payments.empty') }}</div>
        </template>
      </DataTable>
    </AppPanel>

    <ConfirmDialog />

    <Dialog
      v-model:visible="dialogVisible"
      :header="t('payments.edit')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div class="app-dialog-form">
        <div class="app-form-grid">
          <div class="app-field">
            <label class="app-field__label">{{ t('payments.date') }}</label>
            <InputText v-model="paymentForm.date" type="date" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('payments.amount') }}</label>
            <InputText v-model="paymentForm.amount" type="number" step="0.01" min="0.01" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('payments.method') }}</label>
            <Select
              v-model="paymentForm.method"
              :options="methodOptions"
              option-label="label"
              option-value="value"
            />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('payments.cheque_number') }}</label>
            <InputText
              v-model="paymentForm.cheque_number"
              :disabled="paymentForm.method !== 'cheque'"
            />
          </div>
          <div class="app-field app-field--full">
            <label class="app-field__label">{{ t('payments.reference') }}</label>
            <InputText v-model="paymentForm.reference" data-testid="payment-reference-input" />
          </div>
          <div class="app-field app-field--full">
            <label class="app-field__label">{{ t('payments.notes') }}</label>
            <InputText v-model="paymentForm.notes" />
          </div>
        </div>
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" text @click="dialogVisible = false" />
        <Button
          data-testid="payment-save-button"
          :label="t('common.save')"
          icon="pi pi-check"
          :loading="saving"
          @click="savePayment"
        />
      </template>
    </Dialog>
  </AppPage>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import ConfirmDialog from 'primevue/confirmdialog'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import ToggleButton from 'primevue/togglebutton'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  deletePayment,
  listPayments,
  updatePayment,
  type Payment,
  type PaymentMethod,
} from '@/api/payments'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppPanel from '@/components/ui/AppPanel.vue'
import AppStatCard from '@/components/ui/AppStatCard.vue'
import { useFiscalYearStore } from '@/stores/fiscalYear'
import { formatDisplayDate } from '@/utils/format'
import { useTableFilter } from '../composables/useTableFilter'

const { t } = useI18n()
const confirm = useConfirm()
const toast = useToast()
const fiscalYearStore = useFiscalYearStore()

const payments = ref<Payment[]>([])
const { filterText, filtered } = useTableFilter(payments)
const loading = ref(false)
const saving = ref(false)
const undepositedOnly = ref(false)
const dialogVisible = ref(false)
const editingPayment = ref<Payment | null>(null)
const paymentForm = ref({
  amount: '',
  date: '',
  method: 'cheque' as PaymentMethod,
  cheque_number: '',
  reference: '',
  notes: '',
})
const totalAmount = computed(() =>
  filtered.value.reduce((sum, payment) => sum + parseFloat(payment.amount), 0),
)
const averageAmount = computed(() =>
  filtered.value.length ? totalAmount.value / filtered.value.length : 0,
)
const undepositedCount = computed(
  () => filtered.value.filter((payment) => !payment.deposited).length,
)
const chequeCount = computed(
  () => filtered.value.filter((payment) => payment.method === 'cheque').length,
)
const methodOptions = computed(() => [
  { label: t('payments.methods.especes'), value: 'especes' },
  { label: t('payments.methods.cheque'), value: 'cheque' },
  { label: t('payments.methods.virement'), value: 'virement' },
])

function paymentReference(payment: Payment): string {
  return payment.reference ?? payment.invoice_number ?? ''
}

function formatAmount(value: string | number): string {
  return `${parseFloat(String(value)).toFixed(2)} €`
}

function normalizeOptionalField(value: string): string | null {
  const trimmedValue = value.trim()
  return trimmedValue.length > 0 ? trimmedValue : null
}

function openEditDialog(payment: Payment) {
  editingPayment.value = payment
  paymentForm.value = {
    amount: payment.amount,
    date: payment.date,
    method: payment.method,
    cheque_number: payment.cheque_number ?? '',
    reference: payment.reference ?? '',
    notes: payment.notes ?? '',
  }
  dialogVisible.value = true
}

async function savePayment() {
  if (!editingPayment.value) return

  saving.value = true
  try {
    await updatePayment(editingPayment.value.id, {
      amount: paymentForm.value.amount,
      date: paymentForm.value.date,
      method: paymentForm.value.method,
      cheque_number:
        paymentForm.value.method === 'cheque'
          ? normalizeOptionalField(paymentForm.value.cheque_number)
          : null,
      reference: normalizeOptionalField(paymentForm.value.reference),
      notes: normalizeOptionalField(paymentForm.value.notes),
    })
    dialogVisible.value = false
    toast.add({ severity: 'success', summary: t('payments.updated'), life: 3000 })
    await loadPayments()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    saving.value = false
  }
}

async function loadPayments() {
  loading.value = true
  try {
    payments.value = await listPayments({
      invoice_type: 'client',
      undeposited_only: undepositedOnly.value,
      from_date: fiscalYearStore.selectedFiscalYear?.start_date,
      to_date: fiscalYearStore.selectedFiscalYear?.end_date,
    })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    loading.value = false
  }
}

function confirmDelete(payment: Payment) {
  confirm.require({
    message: t('payments.confirm_delete', { amount: parseFloat(payment.amount).toFixed(2) }),
    header: t('common.confirm'),
    icon: 'pi pi-exclamation-triangle',
    acceptProps: { severity: 'danger', label: t('common.delete') },
    rejectProps: { severity: 'secondary', outlined: true, label: t('common.cancel') },
    accept: async () => {
      await deletePayment(payment.id)
      toast.add({ severity: 'success', summary: t('payments.deleted'), life: 2000 })
      await loadPayments()
    },
  })
}

watch(
  () => paymentForm.value.method,
  (method) => {
    if (method !== 'cheque') {
      paymentForm.value.cheque_number = ''
    }
  },
)

watch(
  () => fiscalYearStore.selectedFiscalYearId,
  (newId, oldId) => {
    if (!fiscalYearStore.initialized || newId === oldId) return
    void loadPayments()
  },
)

onMounted(async () => {
  await fiscalYearStore.initialize()
  await loadPayments()
})
</script>

<style scoped>
.payments-table__actions {
  width: 8rem;
}
</style>
