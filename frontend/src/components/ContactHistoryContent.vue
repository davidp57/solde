<template>
  <div v-if="loading" class="contact-history-loading">
    <section class="app-stat-grid">
      <Skeleton v-for="n in 3" :key="n" height="132px" border-radius="8px" />
    </section>
    <AppTableSkeleton :rows="10" :cols="4" style="margin-top: 1.5rem" />
  </div>

  <template v-else-if="history">
    <AppPanel
      :title="contactFullName(history.contact)"
      :subtitle="contactSubtitle(history.contact)"
    >
      <template #actions>
        <div class="contact-history-actions">
          <Tag :value="t(`contacts.types.${history.contact.type}`)" />
          <Button
            v-if="Number(history.total_due) > 0"
            :label="t('contact_history.mark_douteux')"
            icon="pi pi-exclamation-triangle"
            severity="warn"
            outlined
            size="small"
            @click="confirmMarkDouteux"
          />
        </div>
      </template>

      <div class="contact-history-meta">
        <span v-if="history.contact.email">{{ history.contact.email }}</span>
        <span v-if="history.contact.telephone">{{ history.contact.telephone }}</span>
      </div>

      <section class="app-stat-grid">
        <AppStatCard
          :label="t('contact_history.total_invoiced')"
          :value="`${fmt(history.total_invoiced)} €`"
        />
        <AppStatCard
          :label="t('contact_history.total_paid')"
          :value="`${fmt(history.total_paid)} €`"
          tone="success"
        />
        <AppStatCard
          :label="t('contact_history.total_due')"
          :value="`${fmt(history.total_due)} €`"
          :tone="Number(history.total_due) > 0 ? 'danger' : 'default'"
        />
      </section>
    </AppPanel>

    <AppPanel :title="t('contact_history.invoices_section')" dense>
      <template #actions>
        <Button
          icon="pi pi-filter-slash"
          severity="secondary"
          text
          size="small"
          :disabled="!hasActiveInvoiceFilters"
          :title="t('common.reset_filters')"
          @click="resetInvoiceFilters"
        />
      </template>
      <DataTable
        v-if="history.invoices.length"
        v-model:filters="invoiceTableFilters"
        :value="invoiceRows"
        class="app-data-table"
        filter-display="menu"
        striped-rows
        paginator
        :rows="20"
        :rows-per-page-options="[20, 50, 100, 500]"
        size="small"
        row-hover
        :global-filter-fields="[
          'number',
          'date',
          'status',
          'total_amount_value',
          'balance_due_value',
        ]"
        removable-sort
      >
        <Column
          field="number"
          :header="t('invoices.number')"
          style="width: 10rem"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('invoices.number')" />
          </template>
        </Column>
        <Column
          field="date"
          :header="t('invoices.date')"
          style="width: 8rem"
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
          field="status_label"
          :header="t('invoices.status')"
          filter-field="status"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            <Tag
              :value="t(`invoices.statuses.${data.status}`)"
              :severity="statusSeverity(data.status)"
            />
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="invoiceStatusOptions"
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
          :header="t('invoices.total')"
          class="app-money"
          sortable
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ fmt(data.total_amount) }} €</template>
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column
          field="balance_due_value"
          :header="t('contact_history.total_due')"
          class="app-money"
          sortable
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            <span :class="Number(data.balance_due) > 0 ? 'contact-history-due' : ''">
              {{ fmt(data.balance_due) }} €
            </span>
          </template>
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column :header="t('common.actions')" style="width: 4rem">
          <template #body="{ data }">
            <div class="app-inline-actions">
              <Button
                icon="pi pi-eye"
                size="small"
                severity="secondary"
                text
                :title="t('contact_history.view_invoice')"
                @click.stop="openInvoiceDetail(data)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
      <div v-else class="app-empty-state">{{ t('contact_history.no_invoices') }}</div>
    </AppPanel>

    <AppPanel :title="t('contact_history.payments_section')" dense>
      <template #actions>
        <Button
          icon="pi pi-filter-slash"
          severity="secondary"
          text
          size="small"
          :disabled="!hasActivePaymentFilters"
          :title="t('common.reset_filters')"
          @click="resetPaymentFilters"
        />
      </template>
      <DataTable
        v-if="history.payments.length"
        v-model:filters="paymentTableFilters"
        :value="paymentRows"
        class="app-data-table"
        filter-display="menu"
        striped-rows
        paginator
        :rows="20"
        :rows-per-page-options="[20, 50, 100, 500]"
        size="small"
        row-hover
        :global-filter-fields="['date', 'invoice_number', 'method', 'amount_value']"
        removable-sort
      >
        <Column
          field="date"
          :header="t('payments.date')"
          style="width: 8rem"
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
          field="invoice_number"
          :header="t('payments.invoice')"
          style="width: 10rem"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('payments.invoice')" />
          </template>
        </Column>
        <Column
          field="method_label"
          :header="t('payments.method')"
          filter-field="method"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ t(`payments.methods.${data.method}`) }}</template>
          <template #filter="{ filterModel, filterCallback }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="paymentMethodOptions"
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
          field="amount_value"
          :header="t('payments.amount')"
          class="app-money"
          sortable
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ fmt(data.amount) }} €</template>
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column :header="t('common.actions')" style="width: 4rem">
          <template #body="{ data }">
            <div class="app-inline-actions">
              <Button
                icon="pi pi-eye"
                size="small"
                severity="secondary"
                text
                :title="t('contact_history.view_payment')"
                @click.stop="openPaymentDetail(data)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
      <div v-else class="app-empty-state">{{ t('contact_history.no_payments') }}</div>
    </AppPanel>
  </template>

  <div v-else class="app-empty-state">
    {{ t('common.error.notFound') }}
  </div>

  <Dialog
    v-model:visible="invoiceDetailVisible"
    :header="
      invoiceDetail
        ? t('contact_history.invoice_detail_title', { number: invoiceDetail.number })
        : ''
    "
    modal
    class="app-dialog app-dialog--large"
  >
    <Skeleton v-if="invoiceDetailLoading" height="220px" border-radius="8px" />
    <div v-else-if="invoiceDetail" class="contact-history-dialog">
      <div class="contact-history-dialog__meta">
        <Tag
          :value="t(`invoices.statuses.${invoiceDetail.status}`)"
          :severity="statusSeverity(invoiceDetail.status)"
        />
        <span>{{ formatDisplayDate(invoiceDetail.date) }}</span>
        <span v-if="invoiceDetail.due_date"
          >{{ t('invoices.due_date') }} : {{ formatDisplayDate(invoiceDetail.due_date) }}</span
        >
      </div>
      <section class="app-stat-grid contact-history-dialog__stats">
        <AppStatCard
          :label="t('invoices.total')"
          :value="`${fmt(invoiceDetail.total_amount)} €`"
        />
        <AppStatCard
          :label="t('invoices.paid')"
          :value="`${fmt(invoiceDetail.paid_amount)} €`"
          tone="success"
        />
        <AppStatCard
          :label="t('invoices.remaining')"
          :value="`${invoiceRemaining.toFixed(2)} €`"
          :tone="invoiceRemaining > 0 ? 'danger' : 'default'"
        />
      </section>
      <DataTable
        v-if="invoiceDetail.lines.length"
        :value="invoiceDetail.lines"
        size="small"
        class="app-data-table contact-history-dialog__lines"
        striped-rows
      >
        <Column field="description" :header="t('invoices.line_description')" />
        <Column
          field="quantity"
          :header="t('invoices.line_qty')"
          style="width: 5rem"
          class="app-money"
        />
        <Column
          field="unit_price"
          :header="t('invoices.line_price')"
          style="width: 8rem"
          class="app-money"
        >
          <template #body="{ data }">{{ fmt(data.unit_price) }} €</template>
        </Column>
        <Column
          field="amount"
          :header="t('invoices.total')"
          style="width: 8rem"
          class="app-money"
        >
          <template #body="{ data }">{{ fmt(data.amount) }} €</template>
        </Column>
      </DataTable>
      <div class="contact-history-dialog__actions">
        <Button
          icon="pi pi-file-pdf"
          :label="t('invoices.generate_pdf')"
          severity="secondary"
          outlined
          :loading="downloadingPdf"
          @click="downloadPdf(invoiceDetail)"
        />
        <Button
          v-if="contactEmail && invoiceDetail.type === 'client'"
          icon="pi pi-send"
          :label="t('invoices.send_email')"
          @click="sendEmail(invoiceDetail)"
        />
      </div>
    </div>
  </Dialog>

  <Dialog
    v-model:visible="paymentDetailVisible"
    :header="t('contact_history.payment_detail_title')"
    modal
    class="app-dialog app-dialog--medium"
  >
    <Skeleton v-if="paymentDetailLoading" height="160px" border-radius="8px" />
    <div v-else-if="paymentDetail" class="contact-history-dialog">
      <dl class="contact-history-dialog__fields">
        <div class="contact-history-dialog__field">
          <dt>{{ t('payments.date') }}</dt>
          <dd>{{ formatDisplayDate(paymentDetail.date) }}</dd>
        </div>
        <div class="contact-history-dialog__field">
          <dt>{{ t('payments.method') }}</dt>
          <dd>{{ t(`payments.methods.${paymentDetail.method}`) }}</dd>
        </div>
        <div class="contact-history-dialog__field">
          <dt>{{ t('payments.amount') }}</dt>
          <dd>{{ fmt(paymentDetail.amount) }} €</dd>
        </div>
        <div v-if="paymentDetail.invoice_number" class="contact-history-dialog__field">
          <dt>{{ t('payments.invoice') }}</dt>
          <dd>{{ paymentDetail.invoice_number }}</dd>
        </div>
        <div v-if="paymentDetail.cheque_number" class="contact-history-dialog__field">
          <dt>{{ t('payments.cheque_number') }}</dt>
          <dd>{{ paymentDetail.cheque_number }}</dd>
        </div>
        <div v-if="paymentDetail.reference" class="contact-history-dialog__field">
          <dt>{{ t('payments.reference') }}</dt>
          <dd>{{ paymentDetail.reference }}</dd>
        </div>
        <div v-if="paymentDetail.notes" class="contact-history-dialog__field">
          <dt>{{ t('payments.notes') }}</dt>
          <dd>{{ paymentDetail.notes }}</dd>
        </div>
        <div class="contact-history-dialog__field">
          <dt>{{ t('payments.deposited') }}</dt>
          <dd>{{ paymentDetail.deposited ? t('common.yes') : t('common.no') }}</dd>
        </div>
        <div v-if="paymentDetail.deposit_date" class="contact-history-dialog__field">
          <dt>{{ t('payments.deposit_date') }}</dt>
          <dd>{{ formatDisplayDate(paymentDetail.deposit_date) }}</dd>
        </div>
      </dl>
    </div>
  </Dialog>

  <ConfirmDialog />
  <Toast />

  <InvoiceEmailDialog
    :invoice-id="emailDialogInvoiceId"
    @sent="emailDialogInvoiceId = null"
    @close="emailDialogInvoiceId = null"
  />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import ConfirmDialog from 'primevue/confirmdialog'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Skeleton from 'primevue/skeleton'
import Tag from 'primevue/tag'
import Toast from 'primevue/toast'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import AppDateRangeFilter from './ui/AppDateRangeFilter.vue'
import AppFilterMultiSelect from './ui/AppFilterMultiSelect.vue'
import AppNumberRangeFilter from './ui/AppNumberRangeFilter.vue'
import AppPanel from './ui/AppPanel.vue'
import AppStatCard from './ui/AppStatCard.vue'
import AppTableSkeleton from './ui/AppTableSkeleton.vue'
import { getContactHistoryApi, markCreanceDouteuse } from '../api/accounting'
import type { ContactHistory, ContactInvoiceSummary, ContactPaymentSummary } from '../api/accounting'
import { downloadInvoicePdfApi, getInvoiceApi } from '../api/invoices'
import type { Invoice } from '../api/invoices'
import { getPayment } from '../api/payments'
import type { Payment } from '../api/payments'
import {
  dateRangeFilter,
  inFilter,
  numericRangeFilter,
  textFilter,
  useDataTableFilters,
} from '../composables/useDataTableFilters'
import { formatDisplayDate } from '@/utils/format'
import InvoiceEmailDialog from './InvoiceEmailDialog.vue'

const props = defineProps<{ contactId: number }>()
const emit = defineEmits<{ 'contact-loaded': [name: string] }>()

const { t } = useI18n()
const confirm = useConfirm()
const toast = useToast()

const history = ref<ContactHistory | null>(null)
const loading = ref(false)
const invoiceDetailVisible = ref(false)
const invoiceDetail = ref<Invoice | null>(null)
const invoiceDetailLoading = ref(false)
const paymentDetailVisible = ref(false)
const paymentDetail = ref<Payment | null>(null)
const paymentDetailLoading = ref(false)
const downloadingPdf = ref(false)
const emailDialogInvoiceId = ref<number | null>(null)

const contactEmail = computed((): string | null => {
  const email = history.value?.contact.email
  return typeof email === 'string' && email.length > 0 ? email : null
})
const invoiceRemaining = computed((): number => {
  if (!invoiceDetail.value) return 0
  return Number(invoiceDetail.value.total_amount) - Number(invoiceDetail.value.paid_amount)
})
const invoiceRows = computed(() =>
  (history.value?.invoices ?? []).map((invoice) => ({
    ...invoice,
    status_label: t(`invoices.statuses.${invoice.status}`),
    total_amount_value: Number(invoice.total_amount),
    balance_due_value: Number(invoice.balance_due),
  })),
)
const paymentRows = computed(() =>
  (history.value?.payments ?? []).map((payment) => ({
    ...payment,
    method_label: t(`payments.methods.${payment.method}`),
    amount_value: Number(payment.amount),
  })),
)
const invoiceStatusOptions = computed(() =>
  Array.from(new Set((history.value?.invoices ?? []).map((invoice) => invoice.status))).map(
    (status) => ({
      label: t(`invoices.statuses.${status}`),
      value: status,
    }),
  ),
)
const paymentMethodOptions = computed(() =>
  Array.from(new Set((history.value?.payments ?? []).map((payment) => payment.method))).map(
    (method) => ({
      label: t(`payments.methods.${method}`),
      value: method,
    }),
  ),
)
const {
  filters: invoiceTableFilters,
  resetFilters: resetInvoiceFilters,
  hasActiveFilters: hasActiveInvoiceFilters,
} = useDataTableFilters(invoiceRows, {
  global: textFilter(''),
  number: textFilter(),
  date: dateRangeFilter(),
  status: inFilter(),
  total_amount_value: numericRangeFilter(),
  balance_due_value: numericRangeFilter(),
})
const {
  filters: paymentTableFilters,
  resetFilters: resetPaymentFilters,
  hasActiveFilters: hasActivePaymentFilters,
} = useDataTableFilters(paymentRows, {
  global: textFilter(''),
  date: dateRangeFilter(),
  invoice_number: textFilter(),
  method: inFilter(),
  amount_value: numericRangeFilter(),
})

function fmt(val: string | number): string {
  return Number(val).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function statusSeverity(status: string): string {
  const map: Record<string, string> = {
    draft: 'secondary',
    sent: 'info',
    paid: 'success',
    partial: 'warn',
    overdue: 'danger',
    disputed: 'danger',
  }
  return map[status] ?? 'secondary'
}

function contactFullName(contact: ContactHistory['contact']): string {
  return [contact.nom, contact.prenom]
    .filter((value): value is string => typeof value === 'string' && value.length > 0)
    .join(' ')
}

function contactSubtitle(contact: ContactHistory['contact']): string {
  return [contact.email, contact.telephone]
    .filter((value): value is string => typeof value === 'string' && value.length > 0)
    .join(' • ')
}

async function openInvoiceDetail(data: ContactInvoiceSummary): Promise<void> {
  invoiceDetailVisible.value = true
  invoiceDetailLoading.value = true
  invoiceDetail.value = null
  try {
    invoiceDetail.value = await getInvoiceApi(data.id)
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
    invoiceDetailVisible.value = false
  } finally {
    invoiceDetailLoading.value = false
  }
}

async function openPaymentDetail(data: ContactPaymentSummary): Promise<void> {
  paymentDetailVisible.value = true
  paymentDetailLoading.value = true
  paymentDetail.value = null
  try {
    paymentDetail.value = await getPayment(data.id)
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
    paymentDetailVisible.value = false
  } finally {
    paymentDetailLoading.value = false
  }
}

async function downloadPdf(invoice: Invoice): Promise<void> {
  downloadingPdf.value = true
  try {
    const blob = await downloadInvoicePdfApi(invoice.id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `facture-${invoice.number ?? invoice.id}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  } finally {
    downloadingPdf.value = false
  }
}

function sendEmail(invoice: Invoice): void {
  emailDialogInvoiceId.value = invoice.id
}

function confirmMarkDouteux() {
  const amount = history.value ? fmt(history.value.total_due) : ''
  confirm.require({
    message: t('contact_history.mark_douteux_confirm', { amount }),
    header: t('contact_history.mark_douteux'),
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: t('common.cancel'), severity: 'secondary', outlined: true },
    acceptProps: { label: t('common.confirm'), severity: 'warn' },
    accept: async () => {
      try {
        const res = await markCreanceDouteuse(props.contactId)
        toast.add({
          severity: 'success',
          summary: t('contact_history.mark_douteux'),
          detail: t('contact_history.mark_douteux_success', {
            debit: res.account_douteux,
            credit: res.account_client,
          }),
          life: 5000,
        })
        await loadHistory()
      } catch {
        toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
      }
    },
  })
}

async function loadHistory() {
  loading.value = true
  try {
    history.value = await getContactHistoryApi(props.contactId)
    if (history.value) {
      emit('contact-loaded', contactFullName(history.value.contact))
    }
  } finally {
    loading.value = false
  }
}

onMounted(loadHistory)
</script>

<style scoped>
.contact-history-loading {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.contact-history-actions {
  display: flex;
  align-items: center;
  gap: var(--app-space-3);
  flex-wrap: wrap;
}

.contact-history-meta {
  display: flex;
  gap: var(--app-space-4);
  flex-wrap: wrap;
  margin-bottom: var(--app-space-4);
  color: var(--p-text-muted-color);
  font-size: 0.95rem;
}

.contact-history-due {
  color: var(--p-red-600);
}

.contact-history-dialog__meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
  font-size: 0.9rem;
  color: var(--p-text-muted-color);
}

.contact-history-dialog__stats {
  margin-bottom: 1rem;
}

.contact-history-dialog__lines {
  margin-bottom: 1rem;
}

.contact-history-dialog__actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  padding-top: 0.5rem;
}

.contact-history-dialog__fields {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0;
  margin: 0;
  list-style: none;
}

.contact-history-dialog__field {
  display: flex;
  gap: 1rem;
  align-items: baseline;
  padding: 0.35rem 0;
  border-bottom: 1px solid var(--p-content-border-color);
}

.contact-history-dialog__field:last-child {
  border-bottom: none;
}

.contact-history-dialog__field dt {
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
  min-width: 9rem;
  font-weight: 500;
}

.contact-history-dialog__field dd {
  margin: 0;
}
</style>
