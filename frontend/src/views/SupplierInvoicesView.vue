<template>
  <AppPage width="wide">
    <AppPageHeader
      :eyebrow="t('ui.page.collection_eyebrow')"
      :title="t('invoices.supplier.title')"
      :subtitle="t('invoices.supplier.subtitle')"
    >
      <template #actions>
        <Button :label="t('invoices.new')" icon="pi pi-plus" @click="openCreateDialog" />
      </template>
    </AppPageHeader>

    <section class="app-stat-grid">
      <AppStatCard
        :label="t('invoices.supplier.metrics.visible_count')"
        :value="displayedInvoices.length"
        :caption="t('invoices.supplier.metrics.total_count', { count: invoices.length })"
      />
      <AppStatCard
        :label="t('invoices.supplier.metrics.total_amount')"
        :value="formatAmount(totalAmount) + ' €'"
        :caption="t('invoices.supplier.metrics.files_attached', { count: attachedFilesCount })"
      />
      <AppStatCard
        :label="t('invoices.supplier.metrics.overdue_count')"
        :value="overdueCount"
        :caption="t('invoices.supplier.metrics.pending_count', { count: pendingCount })"
        tone="warn"
      />
    </section>

    <AppPanel
      :title="t('invoices.supplier.workspace_title')"
      :subtitle="t('invoices.supplier.workspace_subtitle')"
    >
      <div class="app-toolbar">
        <div class="app-toolbar__meta">
          <p class="app-toolbar__hint">{{ t('invoices.supplier.filters_hint') }}</p>
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
            <label class="app-field__label">{{ t('invoices.status') }}</label>
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
        class="app-data-table supplier-invoices-table"
        filter-display="menu"
        striped-rows
        paginator
        :rows="20"
        :rows-per-page-options="[20, 50, 100, 500]"
        :global-filter-fields="[
          'number',
          'date',
          'contact_name',
          'reference',
          'total_amount',
          'status_label',
          'file_label',
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
          <template #body="{ data }">{{ contactName(data.contact_id) }}</template>
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('invoices.contact')" />
          </template>
        </Column>
        <Column
          field="reference"
          :header="t('invoices.reference')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('invoices.reference')" />
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
        <Column
          field="file_label"
          :header="t('invoices.file')"
          sortable
          filter-field="has_file"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            <i v-if="data.file_path" class="pi pi-paperclip text-primary" />
          </template>
          <template #filter="{ filterModel }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="fileFilterOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
              show-clear
            />
          </template>
        </Column>
        <Column :header="t('common.actions')" class="supplier-invoices-table__actions">
          <template #body="{ data }">
            <div class="app-inline-actions">
              <Button
                icon="pi pi-pencil"
                size="small"
                severity="secondary"
                text
                @click="openEditDialog(data)"
              />
              <Button
                icon="pi pi-upload"
                size="small"
                severity="secondary"
                text
                :title="t('invoices.upload_file')"
                @click="openUploadDialog(data)"
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
          <div class="app-empty-state">{{ t('invoices.supplier.empty') }}</div>
        </template>
      </DataTable>
    </AppPanel>

    <Dialog
      v-model:visible="dialogVisible"
      :header="editingInvoice ? t('invoices.edit') : t('invoices.new')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <SupplierInvoiceForm
        :invoice="editingInvoice"
        :contacts="contacts"
        @saved="onSaved"
        @cancel="dialogVisible = false"
      />
    </Dialog>

    <Dialog
      v-model:visible="uploadDialogVisible"
      :header="t('invoices.upload_file')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div class="app-dialog-form upload-dialog">
        <section class="app-dialog-intro">
          <p class="app-dialog-intro__eyebrow">{{ t('invoices.file') }}</p>
          <p class="app-dialog-intro__text">{{ t('invoices.supplier.upload_intro') }}</p>
        </section>
        <section class="app-dialog-section">
          <FileUpload
            mode="basic"
            accept=".pdf,.jpg,.jpeg,.png,.webp"
            :max-file-size="10000000"
            :auto="false"
            :choose-label="t('invoices.choose_file')"
            @select="onFileSelect"
          />
        </section>
        <div class="app-form-actions">
          <Button
            :label="t('common.cancel')"
            severity="secondary"
            outlined
            @click="uploadDialogVisible = false"
          />
          <Button
            :label="t('common.save')"
            :loading="uploading"
            :disabled="!selectedFile"
            @click="uploadFile"
          />
        </div>
      </div>
    </Dialog>

    <ConfirmDialog />
  </AppPage>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import ConfirmDialog from 'primevue/confirmdialog'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import FileUpload from 'primevue/fileupload'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import AppDateRangeFilter from '../components/ui/AppDateRangeFilter.vue'
import AppFilterMultiSelect from '../components/ui/AppFilterMultiSelect.vue'
import AppListState from '../components/ui/AppListState.vue'
import AppNumberRangeFilter from '../components/ui/AppNumberRangeFilter.vue'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import AppStatCard from '../components/ui/AppStatCard.vue'

import { listContactsApi, type Contact } from '../api/contacts'
import {
  deleteInvoiceApi,
  listInvoicesApi,
  uploadInvoiceFileApi,
  type Invoice,
  type InvoiceStatus,
} from '../api/invoices'
import SupplierInvoiceForm from '../components/SupplierInvoiceForm.vue'
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
const uploadDialogVisible = ref(false)
const uploadTargetId = ref<number | null>(null)
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const statusFilter = ref<InvoiceStatus | null>(null)

const invoiceRows = computed(() =>
  invoices.value.map((invoice) => ({
    ...invoice,
    contact_name: contactName(invoice.contact_id),
    total_amount_value: parseFloat(invoice.total_amount),
    status_label: t(`invoices.statuses.${invoice.status}`),
    has_file: Boolean(invoice.file_path),
    file_label: invoice.file_path ? t('common.yes') : t('common.no'),
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
  reference: textFilter(),
  total_amount_value: numericRangeFilter(),
  status: inFilter(),
  has_file: inFilter(),
})

const totalAmount = computed(() =>
  displayedInvoices.value.reduce((sum, invoice) => sum + parseFloat(invoice.total_amount), 0),
)
const attachedFilesCount = computed(
  () => displayedInvoices.value.filter((invoice) => Boolean(invoice.file_path)).length,
)
const overdueCount = computed(
  () => displayedInvoices.value.filter((invoice) => invoice.status === 'overdue').length,
)
const pendingCount = computed(
  () =>
    displayedInvoices.value.filter(
      (invoice) => invoice.status === 'sent' || invoice.status === 'partial',
    ).length,
)
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

const fileFilterOptions = [
  { label: t('common.yes'), value: true },
  { label: t('common.no'), value: false },
]

function formatAmount(val: string | number) {
  return parseFloat(String(val)).toFixed(2)
}

function contactName(id: number): string {
  const c = contacts.value.find((c) => c.id === id)
  if (!c) return String(id)
  return c.prenom ? `${c.prenom} ${c.nom}` : c.nom
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
    const filters: Record<string, unknown> = { invoice_type: 'fournisseur' }
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
  void router.replace({ name: 'invoices-supplier', query: nextQuery })
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

function openUploadDialog(invoice: Invoice) {
  uploadTargetId.value = invoice.id
  selectedFile.value = null
  uploadDialogVisible.value = true
}

function onFileSelect(event: { files: File[] }) {
  selectedFile.value = event.files[0] ?? null
}

async function uploadFile() {
  if (!uploadTargetId.value || !selectedFile.value) return
  uploading.value = true
  try {
    await uploadInvoiceFileApi(uploadTargetId.value, selectedFile.value)
    toast.add({ severity: 'success', summary: t('invoices.file_uploaded'), life: 3000 })
    uploadDialogVisible.value = false
    await loadInvoices()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  } finally {
    uploading.value = false
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
.supplier-invoices-table__actions {
  width: 11.5rem;
  min-width: 11.5rem;
}

:deep(.supplier-invoices-table .supplier-invoices-table__actions) {
  white-space: nowrap;
  width: 11.5rem;
  min-width: 11.5rem;
}

:deep(.supplier-invoices-table .app-inline-actions) {
  flex-wrap: nowrap;
  justify-content: flex-end;
  min-width: 10rem;
}

.upload-dialog {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}
</style>
