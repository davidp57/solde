<template>
  <AppPage>
    <AppPageHeader
      :eyebrow="t('ui.page.collection_eyebrow')"
      :title="t('invoices.client.title')"
      :subtitle="t('invoices.client.subtitle')"
    >
      <template #actions>
        <Button :label="t('invoices.new')" icon="pi pi-plus" @click="openCreateDialog" />
      </template>
    </AppPageHeader>

    <section class="app-stat-grid">
      <AppStatCard
        :label="t('invoices.client.metrics.visible_count')"
        :value="portfolioMetrics.visibleCount"
        :caption="t('invoices.client.metrics.total_count', { count: invoices.length })"
      />
      <AppStatCard
        :label="t('invoices.client.metrics.total_amount')"
        :value="formatAmount(portfolioMetrics.totalAmount) + ' €'"
        :caption="
          t('invoices.client.metrics.average_amount', {
            amount: formatAmount(portfolioMetrics.averageAmount),
          })
        "
      />
      <AppStatCard
        :label="t('invoices.client.metrics.paid_amount')"
        :value="formatAmount(portfolioMetrics.paidAmount) + ' €'"
        :caption="
          t('invoices.client.metrics.partial_count', { count: portfolioMetrics.partialCount })
        "
        tone="success"
      />
      <AppStatCard
        :label="t('invoices.client.metrics.overdue_amount')"
        :value="formatAmount(portfolioMetrics.overdueAmount) + ' €'"
        :caption="
          t('invoices.client.metrics.overdue_count', { count: portfolioMetrics.overdueCount })
        "
        :tone="portfolioMetrics.overdueCount > 0 ? 'danger' : 'warn'"
      />
    </section>

    <AppPanel
      :title="t('invoices.client.portfolio_title')"
      :subtitle="t('invoices.client.portfolio_subtitle')"
    >
      <div class="app-toolbar">
        <div class="app-toolbar__meta">
          <p class="app-toolbar__hint">{{ t('invoices.client.filters_hint') }}</p>
          <div class="app-toolbar__meta-actions">
            <AppListState
              :displayed-count="displayedInvoices.length"
              :total-count="invoices.length"
              :loading="loading"
              :search-text="globalFilter"
              :active-filters="activeFilterLabels"
            />
            <Button
              v-if="hasActiveFilters"
              icon="pi pi-filter-slash"
              severity="secondary"
              text
              :title="t('common.reset_filters')"
              @click="resetFilters"
            />
          </div>
        </div>

        <div class="app-filter-grid">
          <div class="app-field">
            <label class="app-field__label">{{ t('invoices.filter_status') }}</label>
            <Select
              v-model="statusFilter"
              :options="statusOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
              show-clear
              @change="loadInvoices"
            />
          </div>
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('common.filter_placeholder') }}</label>
            <InputText v-model="globalFilter" :placeholder="t('common.filter_placeholder')" />
          </div>
        </div>
      </div>

      <DataTable
        v-model:filters="tableFilters"
        :value="invoiceRows"
        :loading="loading"
        class="app-data-table invoices-table"
        filter-display="menu"
        striped-rows
        paginator
        :rows="20"
        :rows-per-page-options="[20, 50, 100, 500]"
        :global-filter-fields="[
          'number',
          'date',
          'contact_name',
          'label_label',
          'total_amount',
          'status_label',
        ]"
        data-key="id"
        size="small"
        row-hover
        removable-sort
        @value-change="syncDisplayedInvoices"
      >
        <Column field="number" :header="t('invoices.number')" sortable>
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('invoices.number')" />
          </template>
        </Column>
        <Column
          field="date"
          :header="t('invoices.date')"
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
          field="contact_name"
          :header="t('invoices.contact')"
          sortable
          filter-field="contact_name"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            {{ contactName(data.contact_id) }}
          </template>
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('invoices.contact')" />
          </template>
        </Column>
        <Column
          field="label_label"
          :header="t('invoices.label')"
          sortable
          filter-field="label"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            <Tag v-if="data.label" :value="t(`invoices.labels.${data.label}`)" severity="info" />
          </template>
          <template #filter="{ filterModel }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="labelOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
              show-clear
            />
          </template>
        </Column>
        <Column
          field="total_amount_value"
          :header="t('invoices.total')"
          class="app-money"
          sortable
          filter-field="total_amount_value"
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ formatAmount(data.total_amount) }} €</template>
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column
          field="status_label"
          :header="t('invoices.status')"
          sortable
          filter-field="status"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            <Tag
              :value="t(`invoices.statuses.${data.status}`)"
              :severity="statusSeverity(data.status)"
            />
          </template>
          <template #filter="{ filterModel }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="statusOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
              show-clear
            />
          </template>
        </Column>
        <Column :header="t('common.actions')" class="invoices-table__actions-column">
          <template #body="{ data }">
            <div class="app-inline-actions">
              <Button
                icon="pi pi-eye"
                size="small"
                severity="secondary"
                text
                :title="t('invoices.history')"
                @click="openHistory(data)"
              />
              <Button
                icon="pi pi-pencil"
                size="small"
                severity="secondary"
                text
                @click="openEditDialog(data)"
              />
              <Button
                icon="pi pi-file-pdf"
                size="small"
                severity="secondary"
                text
                :title="t('invoices.generate_pdf')"
                @click="openPdf(data)"
              />
              <Button
                icon="pi pi-send"
                size="small"
                severity="secondary"
                text
                :title="t('invoices.send_email')"
                @click="sendEmail(data)"
              />
              <Button
                icon="pi pi-copy"
                size="small"
                severity="secondary"
                text
                :title="t('invoices.duplicate')"
                @click="duplicate(data)"
              />
              <Button
                icon="pi pi-trash"
                size="small"
                severity="danger"
                text
                @click="confirmDelete(data)"
              />
            </div>
          </template>
        </Column>
        <template #empty>
          <div class="app-empty-state">{{ t('invoices.client.empty') }}</div>
        </template>
      </DataTable>
    </AppPanel>

    <Dialog
      v-model:visible="dialogVisible"
      :header="editingInvoice ? t('invoices.edit') : t('invoices.new')"
      modal
      class="app-dialog app-dialog--large"
    >
      <ClientInvoiceForm
        :invoice="editingInvoice"
        :contacts="contacts"
        @saved="onSaved"
        @cancel="dialogVisible = false"
      />
    </Dialog>

    <ConfirmDialog />

    <Dialog
      v-model:visible="historyVisible"
      :header="historyInvoice ? t('invoices.history_title', { number: historyInvoice.number }) : ''"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div v-if="historyInvoice" class="history-dialog">
        <section class="app-dialog-intro">
          <p class="app-dialog-intro__eyebrow">{{ t('invoices.history') }}</p>
          <p class="app-dialog-intro__text">{{ t('invoices.client.history_intro') }}</p>
        </section>
        <div class="history-dialog__summary">
          <div class="history-dialog__metric">
            <div class="history-dialog__label">{{ t('invoices.total') }}</div>
            <div class="history-dialog__value">
              {{ formatAmount(historyInvoice.total_amount) }} €
            </div>
          </div>
          <div class="history-dialog__metric">
            <div class="history-dialog__label">{{ t('invoices.paid') }}</div>
            <div class="history-dialog__value history-dialog__value--success">
              {{ formatAmount(historyInvoice.paid_amount) }} €
            </div>
          </div>
          <div class="history-dialog__metric">
            <div class="history-dialog__label">{{ t('invoices.remaining') }}</div>
            <div
              class="history-dialog__value"
              :class="
                remaining > 0 ? 'history-dialog__value--warn' : 'history-dialog__value--success'
              "
            >
              {{ remaining.toFixed(2) }} €
            </div>
          </div>
        </div>

        <div v-if="historyLoading" class="history-dialog__loading">
          <ProgressSpinner style="width: 32px; height: 32px" />
        </div>
        <div v-else-if="historyPayments.length === 0" class="app-empty-state">
          {{ t('invoices.no_payments') }}
        </div>
        <DataTable
          v-else
          v-model:filters="historyTableFilters"
          :value="historyPaymentRows"
          class="app-data-table"
          filter-display="menu"
          paginator
          :rows="20"
          :rows-per-page-options="[20, 50, 100, 500]"
          size="small"
          :global-filter-fields="['date', 'amount_value', 'method', 'cheque_number']"
          removable-sort
        >
          <Column
            field="date"
            :header="t('payments.date')"
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
            :header="t('payments.amount')"
            class="app-money"
            sortable
            data-type="numeric"
            :show-filter-match-modes="false"
            :show-add-button="false"
          >
            <template #body="{ data }">{{ parseFloat(data.amount).toFixed(2) }} €</template>
            <template #filter="{ filterModel }">
              <AppNumberRangeFilter v-model="filterModel.value" />
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
            <template #filter="{ filterModel }">
              <AppFilterMultiSelect
                v-model="filterModel.value"
                :options="paymentMethodOptions"
                option-label="label"
                option-value="value"
                :placeholder="t('common.all')"
                display="chip"
                show-clear
              />
            </template>
          </Column>
          <Column
            field="cheque_number"
            :header="t('payments.cheque_number')"
            sortable
            :show-filter-match-modes="false"
            :show-add-button="false"
          >
            <template #filter="{ filterModel }">
              <InputText v-model="filterModel.value" :placeholder="t('payments.cheque_number')" />
            </template>
          </Column>
        </DataTable>
      </div>
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
import ProgressSpinner from 'primevue/progressspinner'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { listContactsApi, type Contact } from '../api/contacts'
import {
  deleteInvoiceApi,
  duplicateInvoiceApi,
  getInvoicePdfUrl,
  listInvoicesApi,
  sendInvoiceEmailApi,
  type Invoice,
  type InvoiceStatus,
} from '../api/invoices'
import { listPayments, type Payment } from '../api/payments'
import ClientInvoiceForm from '../components/ClientInvoiceForm.vue'
import AppDateRangeFilter from '../components/ui/AppDateRangeFilter.vue'
import AppFilterMultiSelect from '../components/ui/AppFilterMultiSelect.vue'
import AppListState from '../components/ui/AppListState.vue'
import AppNumberRangeFilter from '../components/ui/AppNumberRangeFilter.vue'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import AppStatCard from '../components/ui/AppStatCard.vue'
import {
  dateRangeFilter,
  inFilter,
  numericRangeFilter,
  textFilter,
  useDataTableFilters,
} from '../composables/useDataTableFilters'
import {
  collectActiveFilterLabels,
  findSelectedFilterLabel,
} from '../composables/activeFilterLabels'
import { useFiscalYearStore } from '../stores/fiscalYear'
import { formatContactDisplayName } from '../utils/contact'
import { formatDisplayDate } from '@/utils/format'

const { t } = useI18n()
const confirm = useConfirm()
const route = useRoute()
const router = useRouter()
const toast = useToast()
const fiscalYearStore = useFiscalYearStore()

const invoices = ref<Invoice[]>([])
const contacts = ref<Contact[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editingInvoice = ref<Invoice | null>(null)
const statusFilter = ref<InvoiceStatus | null>(null)

// History dialog
const historyVisible = ref(false)
const historyInvoice = ref<Invoice | null>(null)
const historyLoading = ref(false)
const historyPayments = ref<Payment[]>([])
const historyPaymentRows = computed(() =>
  historyPayments.value.map((payment) => ({
    ...payment,
    amount_value: parseFloat(payment.amount),
    method_label: t(`payments.methods.${payment.method}`),
  })),
)

const invoiceRows = computed(() =>
  invoices.value.map((invoice) => ({
    ...invoice,
    contact_name: contactName(invoice.contact_id),
    label_label: invoice.label ? t(`invoices.labels.${invoice.label}`) : '',
    total_amount_value: parseFloat(invoice.total_amount),
    status_label: t(`invoices.statuses.${invoice.status}`),
  })),
)

const {
  filters: tableFilters,
  globalFilter,
  displayedRows: displayedInvoices,
  activeColumnFilterCount,
  hasActiveFilters,
  resetFilters,
  syncDisplayedRows: syncDisplayedInvoices,
} = useDataTableFilters(invoiceRows, {
  global: textFilter(''),
  number: textFilter(),
  date: dateRangeFilter(),
  contact_name: textFilter(),
  label: inFilter(),
  total_amount_value: numericRangeFilter(),
  status: inFilter(),
})
const { filters: historyTableFilters } = useDataTableFilters(historyPaymentRows, {
  global: textFilter(''),
  date: dateRangeFilter(),
  amount_value: numericRangeFilter(),
  method: inFilter(),
  cheque_number: textFilter(),
})

const remaining = computed(() => {
  if (!historyInvoice.value) return 0
  return (
    parseFloat(historyInvoice.value.total_amount) - parseFloat(historyInvoice.value.paid_amount)
  )
})

const portfolioMetrics = computed(() => {
  const visible = displayedInvoices.value
  const totalAmount = visible.reduce((sum, invoice) => sum + parseFloat(invoice.total_amount), 0)
  const paidAmount = visible.reduce((sum, invoice) => sum + parseFloat(invoice.paid_amount), 0)
  const overdueInvoices = visible.filter((invoice) => invoice.status === 'overdue')
  const overdueAmount = overdueInvoices.reduce((sum, invoice) => {
    return sum + Math.max(0, parseFloat(invoice.total_amount) - parseFloat(invoice.paid_amount))
  }, 0)
  const partialCount = visible.filter((invoice) => invoice.status === 'partial').length

  return {
    visibleCount: visible.length,
    totalAmount,
    paidAmount,
    overdueAmount,
    overdueCount: overdueInvoices.length,
    partialCount,
    averageAmount: visible.length > 0 ? totalAmount / visible.length : 0,
  }
})

const activeFilterLabels = computed(() =>
  collectActiveFilterLabels(
    findSelectedFilterLabel(statusOptions, statusFilter.value),
    activeColumnFilterCount.value > 0
      ? t('common.list.column_filters_chip', { count: activeColumnFilterCount.value })
      : undefined,
  ),
)

const statusOptions = [
  { label: t('invoices.statuses.draft'), value: 'draft' },
  { label: t('invoices.statuses.sent'), value: 'sent' },
  { label: t('invoices.statuses.paid'), value: 'paid' },
  { label: t('invoices.statuses.partial'), value: 'partial' },
  { label: t('invoices.statuses.overdue'), value: 'overdue' },
  { label: t('invoices.statuses.disputed'), value: 'disputed' },
]

const paymentMethodOptions = [
  { label: t('payments.methods.especes'), value: 'especes' },
  { label: t('payments.methods.cheque'), value: 'cheque' },
  { label: t('payments.methods.virement'), value: 'virement' },
]

const labelOptions = [
  { label: t('invoices.labels.cs'), value: 'cs' },
  { label: t('invoices.labels.a'), value: 'a' },
  { label: t('invoices.labels.cs+a'), value: 'cs+a' },
  { label: t('invoices.labels.general'), value: 'general' },
]

function formatAmount(val: string | number) {
  return parseFloat(String(val)).toFixed(2)
}

function contactName(id: number): string {
  const c = contacts.value.find((c) => c.id === id)
  if (!c) return String(id)
  return formatContactDisplayName(c)
}

function statusSeverity(s: InvoiceStatus): string {
  const map: Record<InvoiceStatus, string> = {
    draft: 'secondary',
    sent: 'info',
    paid: 'success',
    partial: 'warn',
    overdue: 'danger',
    disputed: 'danger',
  }
  return map[s] ?? 'secondary'
}

async function loadInvoices() {
  loading.value = true
  try {
    const filters: Record<string, unknown> = { invoice_type: 'client' }
    if (fiscalYearStore.selectedFiscalYear) {
      filters.from_date = fiscalYearStore.selectedFiscalYear.start_date
      filters.to_date = fiscalYearStore.selectedFiscalYear.end_date
    }
    if (statusFilter.value) filters.invoice_status = statusFilter.value
    invoices.value = await listInvoicesApi(filters)
    openInvoiceFromQuery()
  } finally {
    loading.value = false
  }
}

function openInvoiceFromQuery() {
  const rawInvoiceId = Array.isArray(route.query.invoiceId)
    ? route.query.invoiceId[0]
    : route.query.invoiceId
  const invoiceId = Number(rawInvoiceId)
  if (!invoiceId) return
  const invoice = invoices.value.find((candidate) => candidate.id === invoiceId)
  if (!invoice) return
  openEditDialog(invoice)
  const nextQuery = { ...route.query }
  delete nextQuery.invoiceId
  void router.replace({ name: 'invoices-client', query: nextQuery })
}

async function loadContacts() {
  contacts.value = await listContactsApi()
}

function openCreateDialog() {
  editingInvoice.value = null
  dialogVisible.value = true
}

function openEditDialog(invoice: Invoice) {
  editingInvoice.value = invoice
  dialogVisible.value = true
}

function onSaved() {
  dialogVisible.value = false
  void loadInvoices()
}

function openPdf(invoice: Invoice) {
  window.open(getInvoicePdfUrl(invoice.id), '_blank')
}

async function sendEmail(invoice: Invoice) {
  try {
    await sendInvoiceEmailApi(invoice.id)
    toast.add({ severity: 'success', summary: t('invoices.email_sent'), life: 3000 })
    await loadInvoices()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  }
}

async function duplicate(invoice: Invoice) {
  try {
    await duplicateInvoiceApi(invoice.id)
    toast.add({ severity: 'success', summary: t('invoices.duplicated'), life: 3000 })
    await loadInvoices()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  }
}

async function openHistory(invoice: Invoice) {
  historyInvoice.value = invoice
  historyVisible.value = true
  historyLoading.value = true
  historyPayments.value = []
  try {
    historyPayments.value = await listPayments({ invoice_id: invoice.id })
  } finally {
    historyLoading.value = false
  }
}

function confirmDelete(invoice: Invoice) {
  confirm.require({
    message: t('invoices.confirm_delete', { number: invoice.number }),
    header: t('common.confirm'),
    icon: 'pi pi-exclamation-triangle',
    acceptProps: { severity: 'danger', label: t('common.delete') },
    rejectProps: { severity: 'secondary', outlined: true, label: t('common.cancel') },
    accept: async () => {
      try {
        await deleteInvoiceApi(invoice.id)
        toast.add({ severity: 'success', summary: t('invoices.deleted'), life: 3000 })
        await loadInvoices()
      } catch {
        toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
      }
    },
  })
}

watch(
  () => fiscalYearStore.selectedFiscalYearId,
  (newId, oldId) => {
    if (!fiscalYearStore.initialized || newId === oldId) return
    void loadInvoices()
  },
)

watch(
  () => route.query.invoiceId,
  () => {
    openInvoiceFromQuery()
  },
)

onMounted(async () => {
  await fiscalYearStore.initialize()
  await Promise.all([loadInvoices(), loadContacts()])
})
</script>

<style scoped>
.invoices-table__actions-column {
  width: 13.5rem;
}

.history-dialog {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.history-dialog__summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--app-space-3);
  padding-bottom: var(--app-space-4);
  border-bottom: 1px solid var(--app-surface-border);
}

.history-dialog__metric {
  padding: var(--app-space-3);
  border-radius: var(--app-surface-radius-sm);
  background: color-mix(in srgb, var(--app-surface-bg) 85%, transparent 15%);
}

.history-dialog__label {
  color: var(--p-text-muted-color);
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.history-dialog__value {
  margin-top: var(--app-space-2);
  font-size: 1.05rem;
  font-weight: 800;
}

.history-dialog__value--success {
  color: var(--p-green-600);
}

.history-dialog__value--warn {
  color: var(--p-orange-500);
}

.history-dialog__loading {
  display: flex;
  justify-content: center;
  padding: var(--app-space-5) 0;
}

@media (max-width: 767px) {
  .history-dialog__summary {
    grid-template-columns: 1fr;
  }
}
</style>
