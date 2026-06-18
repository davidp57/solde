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

    <InvoiceFunnelHero
      type="supplier"
      :total-invoiced="funnelMetrics.totalInvoiced"
      :collected="funnelMetrics.collected"
      :remaining="funnelMetrics.remaining"
      :overdue="funnelMetrics.overdue"
      :invoice-count="funnelMetrics.count"
    />

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
            <Button
              :label="t('common.export_excel')"
              icon="pi pi-file-excel"
              severity="secondary"
              outlined
              size="small"
              @click="doExportExcel"
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

      <AppListLimitBanner
        :view-key="LIMIT_VIEW_KEY"
        :fetched-count="invoices.length"
        :limit="limitStore.systemLimit"
        @reload="loadInvoices"
      />
      <template v-if="isMobile">
        <AppMobileCardList :items="invoiceRows" :empty-message="t('invoices.supplier.empty')">
          <template #card="{ item: data }">
            <div class="app-mobile-card-row app-mobile-card-row--between">
              <span class="app-mobile-card-value" style="font-weight: 700">{{ data.number }}</span>
              <InvoiceStatusBadge :status="data.status" />
            </div>
            <div class="app-mobile-card-row">
              <span class="app-mobile-card-label">{{ t('invoices.contact') }} :</span>
              <span class="app-mobile-card-value">{{ contactName(data.contact_id) }}</span>
            </div>
            <div class="app-mobile-card-row app-mobile-card-row--between">
              <span class="app-mobile-card-label">{{ formatDisplayDate(data.date) }}</span>
              <span class="app-mobile-card-value" style="font-weight: 600">{{ formatAmount(data.total_amount) }} €</span>
            </div>
            <div v-if="data.reference || data.file_path" class="app-mobile-card-row">
              <template v-if="data.reference">
                <span class="app-mobile-card-label">{{ t('invoices.reference') }} :</span>
                <span class="app-mobile-card-value">{{ data.reference }}</span>
              </template>
              <i v-if="data.file_path" class="pi pi-paperclip supplier-card__attachment" />
            </div>
            <div class="app-mobile-card-actions">
              <InvoiceRowActions
                :primary="supplierPrimaryAction(data)"
                :menu-items="supplierMenuItems(data)"
                :menu-aria-label="t('invoices.actions.more')"
              />
            </div>
          </template>
        </AppMobileCardList>
      </template>
      <DataTable
        v-else
        v-model:filters="tableFilters"
        :value="invoiceRows"
        :loading="loading"
        class="app-data-table supplier-invoices-table"
        filter-display="menu"
        striped-rows
        paginator
        :rows="50"
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
        sort-field="date"
        :sort-order="-1"
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
            <InvoiceStatusBadge :status="data.status" />
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
            <InvoiceRowActions
              :primary="supplierPrimaryAction(data)"
              :menu-items="supplierMenuItems(data)"
              :menu-aria-label="t('invoices.actions.more')"
            />
          </template>
        </Column>
        <template #empty>
          <div class="app-empty-state">{{ t('invoices.supplier.empty') }}</div>
        </template>
      </DataTable>
    </AppPanel>

    <Dialog
      :visible="dialogVisible"
      @update:visible="onCloseDialog"
      @show="focusFormInput"
      :header="editingInvoice ? `${t('invoices.edit')} — ${editingInvoice.number}` : t('invoices.new')"
      modal
      :class="['app-dialog', editingInvoice?.file_path ? 'app-dialog--large' : 'app-dialog--medium']"
    >
      <div ref="formWrapperEl" :class="editingInvoice?.file_path ? 'supplier-edit-dialog__layout' : ''">
        <div class="supplier-edit-dialog__form-col">
          <SupplierInvoiceForm
            ref="supplierFormRef"
            :invoice="editingInvoice"
            :contacts="contacts"
            @saved="onSaved"
            @cancel="onCloseDialog(false)"
          />
        </div>
        <div v-if="editingInvoice?.file_path" class="supplier-edit-dialog__preview">
          <h3 class="app-dialog-section__title">{{ t('invoices.file') }}</h3>
          <div v-if="editFileLoading" class="supplier-preview-dialog__file-loading">
            <i class="pi pi-spin pi-spinner" style="font-size: 2rem" />
          </div>
          <div v-else-if="editFileBlobUrl" class="supplier-preview-dialog__file-frame">
            <embed
              v-if="editFileIsPdf"
              :src="`${editFileBlobUrl}#toolbar=0&navpanes=0&pagemode=none&view=FitH`"
              type="application/pdf"
              class="supplier-preview-dialog__embed"
               :title="t('invoices.file')"
            />
            <img
              v-else
              :src="editFileBlobUrl"
              class="supplier-preview-dialog__img"
              :alt="t('invoices.supplier.preview_file')"
            />
          </div>
          <div v-else class="app-empty-state">{{ t('common.error.unknown') }}</div>
        </div>
      </div>
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

    <!-- Preview dialog -->
    <Dialog
      v-model:visible="previewVisible"
      :header="previewInvoice ? t('invoices.supplier.preview_title', { number: previewInvoice.number }) : ''"
      modal
      class="app-dialog app-dialog--large"
      @hide="onPreviewHide"
    >
      <div class="preview-nav-bar">
        <Button
          icon="pi pi-chevron-left"
          text
          rounded
          size="small"
          :disabled="previewIndex <= 0"
          :title="t('common.previous')"
          @click="goToPrevPreview"
        />
        <span class="preview-nav-bar__counter">{{ previewIndex + 1 }} / {{ displayedInvoices.length }}</span>
        <Button
          icon="pi pi-chevron-right"
          text
          rounded
          size="small"
          :disabled="previewIndex >= displayedInvoices.length - 1"
          :title="t('common.next')"
          @click="goToNextPreview"
        />
      </div>
      <div v-if="previewInvoice" ref="previewDialogBodyRef" class="supplier-preview-dialog">

        <!-- Header info + actions -->
        <section class="app-dialog-intro history-dialog__intro">
          <div>
            <p class="app-dialog-intro__eyebrow">{{ contactName(previewInvoice.contact_id) }}</p>
            <div class="supplier-preview-meta">
              <span>{{ t('invoices.date') }} : {{ formatDisplayDate(previewInvoice.date) }}</span>
              <span v-if="previewInvoice.due_date">{{ t('invoices.due_date') }} : {{ formatDisplayDate(previewInvoice.due_date) }}</span>
              <span v-if="previewInvoice.reference">{{ t('invoices.reference') }} : {{ previewInvoice.reference }}</span>
            </div>
          </div>
          <div class="app-inline-actions">
            <InvoiceStatusBadge :status="previewInvoice.status" />
            <Button
              icon="pi pi-download"
              size="small"
              severity="secondary"
              outlined
              :label="isMobile ? undefined : t('invoices.supplier.download_file')"
              :title="t('invoices.supplier.download_file')"
              :loading="previewDownloading"
              :disabled="!previewInvoice.file_path"
              @click="downloadFile(previewInvoice)"
            />
            <Button
              icon="pi pi-upload"
              size="small"
              severity="secondary"
              outlined
              :label="isMobile ? undefined : t('invoices.upload_file')"
              :title="t('invoices.upload_file')"
              @click="openUploadFromPreview"
            />
            <Button
              v-if="canRecordPayment(previewInvoice)"
              icon="pi pi-wallet"
              size="small"
              :label="isMobile ? undefined : t('invoices.record_payment')"
              :title="t('invoices.record_payment')"
              @click="openPaymentDialog(previewInvoice!)"
            />
          </div>
        </section>

        <!-- Amounts summary -->
        <div class="history-dialog__summary">
          <div class="history-dialog__metric">
            <div class="history-dialog__label">{{ t('invoices.total') }}</div>
            <div class="history-dialog__value">{{ formatAmount(previewInvoice.total_amount) }} €</div>
          </div>
          <div class="history-dialog__metric">
            <div class="history-dialog__label">{{ t('invoices.paid') }}</div>
            <div class="history-dialog__value history-dialog__value--success">{{ formatAmount(previewInvoice.paid_amount) }} €</div>
          </div>
          <div class="history-dialog__metric">
            <div class="history-dialog__label">{{ t('invoices.remaining') }}</div>
            <div
              class="history-dialog__value"
              :class="previewRemaining > 0 ? 'history-dialog__value--warn' : 'history-dialog__value--success'"
            >{{ previewRemaining.toFixed(2) }} €</div>
          </div>
        </div>

        <!-- Two-column layout: payments + file preview -->
        <div class="supplier-preview-dialog__body">

          <!-- Payments -->
          <div class="supplier-preview-dialog__payments">
            <h3 class="app-dialog-section__title">{{ t('invoices.history') }}</h3>
            <AppTableSkeleton v-if="previewPaymentsLoading" :rows="3" :cols="3" />
            <div v-else-if="previewPayments.length === 0" class="app-empty-state">
              {{ t('invoices.no_payments') }}
            </div>
            <AppMobileCardList v-else-if="isMobile" :items="previewPayments" :empty-message="t('invoices.no_payments')">
              <template #card="{ item: data }">
                <div class="app-mobile-card-row app-mobile-card-row--between">
                  <span class="app-mobile-card-label">{{ formatDisplayDate(data.date) }}</span>
                  <span class="app-mobile-card-value" style="font-weight:700">{{ parseFloat(data.amount).toFixed(2) }} €</span>
                </div>
                <div class="app-mobile-card-row">
                  <span class="app-mobile-card-label">{{ t('payments.method') }} :</span>
                  <span class="app-mobile-card-value">{{ t(`payments.methods.${data.method}`) }}</span>
                </div>
              </template>
            </AppMobileCardList>
            <DataTable
              v-else
              :value="previewPayments"
              class="app-data-table"
              size="small"
              :rows="10"
            >
              <Column field="date" :header="t('payments.date')" sortable>
                <template #body="{ data }">{{ formatDisplayDate(data.date) }}</template>
              </Column>
              <Column field="amount" :header="t('payments.amount')" class="app-money" sortable>
                <template #body="{ data }">{{ parseFloat(data.amount).toFixed(2) }} €</template>
              </Column>
              <Column field="method" :header="t('payments.method')" sortable>
                <template #body="{ data }">{{ t(`payments.methods.${data.method}`) }}</template>
              </Column>
            </DataTable>
          </div>

          <!-- File preview -->
          <div class="supplier-preview-dialog__file">
            <h3 class="app-dialog-section__title">{{ t('invoices.file') }}</h3>
            <div v-if="!previewInvoice.file_path" class="app-empty-state">
              {{ t('invoices.supplier.no_attachment') }}
            </div>
            <div v-else-if="previewFileLoading" class="supplier-preview-dialog__file-loading">
              <i class="pi pi-spin pi-spinner" style="font-size: 2rem" />
            </div>
            <div v-else-if="previewBlobUrl" class="supplier-preview-dialog__file-frame">
              <embed
                v-if="previewIsPdf"
                :src="`${previewBlobUrl}#toolbar=0&navpanes=0&pagemode=none&view=FitH`"
                type="application/pdf"
                class="supplier-preview-dialog__embed"
                :title="t('invoices.file')"
              />
              <img
                v-else
                :src="previewBlobUrl"
                class="supplier-preview-dialog__img"
                :alt="t('invoices.supplier.preview_file')"
              />
            </div>
            <div v-else class="app-empty-state">
              {{ t('common.error.unknown') }}
            </div>
          </div>

        </div>

        <div class="preview-nav-bar preview-nav-bar--bottom">
          <Button
            icon="pi pi-chevron-left"
            text
            rounded
            size="small"
            :disabled="previewIndex <= 0"
            :title="t('common.previous')"
            @click="goToPrevPreviewBottom"
          />
          <span class="preview-nav-bar__counter">{{ previewIndex + 1 }} / {{ displayedInvoices.length }}</span>
          <Button
            icon="pi pi-chevron-right"
            text
            rounded
            size="small"
            :disabled="previewIndex >= displayedInvoices.length - 1"
            :title="t('common.next')"
            @click="goToNextPreviewBottom"
          />
        </div>

      </div>
    </Dialog>
    <InvoicePaymentDialog
      v-model:visible="paymentDialogVisible"
      :invoice="paymentInvoice"
      :contact-name="paymentInvoice ? contactName(paymentInvoice.contact_id) : undefined"
      @paid="onPaymentRecorded"
    />

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
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import AppDateRangeFilter from '../components/ui/AppDateRangeFilter.vue'
import AppFilterMultiSelect from '../components/ui/AppFilterMultiSelect.vue'
import AppListState from '../components/ui/AppListState.vue'
import AppNumberRangeFilter from '../components/ui/AppNumberRangeFilter.vue'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import AppTableSkeleton from '../components/ui/AppTableSkeleton.vue'
import AppMobileCardList from '../components/ui/AppMobileCardList.vue'
import AppListLimitBanner from '../components/ui/AppListLimitBanner.vue'
import { useBreakpoints } from '../composables/useBreakpoints'
import { useTableExport, type ExportColumn } from '@/composables/useTableExport'

import { listContactsApi, type Contact } from '../api/contacts'
import {
  deleteInvoiceApi,
  downloadInvoiceFileApi,
  listInvoicesWithCountApi,
  uploadInvoiceFileApi,
  type Invoice,
  type InvoiceStatus,
} from '../api/invoices'
import { listPayments, type Payment } from '../api/payments'
import SupplierInvoiceForm from '../components/SupplierInvoiceForm.vue'
import InvoiceStatusBadge from '../components/invoices/InvoiceStatusBadge.vue'
import InvoicePaymentDialog from '../components/invoices/InvoicePaymentDialog.vue'
import InvoiceFunnelHero from '../components/invoices/InvoiceFunnelHero.vue'
import InvoiceRowActions, {
  type InvoiceRowPrimaryAction,
} from '../components/invoices/InvoiceRowActions.vue'
import type { MenuItem } from 'primevue/menuitem'
import { isOverdueInvoice, remainingForInvoice } from '../composables/useInvoiceMetrics'
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
import { useUnsavedChangesGuard } from '../composables/useUnsavedChangesGuard'
import { useFiscalYearStore } from '../stores/fiscalYear'
import { useListLimitStore } from '../stores/listLimit'
import { formatContactDisplayName } from '../utils/contact'
import { formatDisplayDate } from '@/utils/format'
import { getErrorDetail } from '@/utils/errorUtils'

const { t } = useI18n()
const confirm = useConfirm()
const route = useRoute()
const router = useRouter()
const toast = useToast()
const fiscalYearStore = useFiscalYearStore()
const limitStore = useListLimitStore()
const LIMIT_VIEW_KEY = 'invoices-supplier'
const { isMobile } = useBreakpoints()
const { exportToExcel } = useTableExport()
const exportColumns: ExportColumn[] = [
  { field: 'number', header: t('invoices.number') },
  { field: 'date', header: t('invoices.date') },
  { field: 'contact_name', header: t('invoices.contact') },
  { field: 'reference', header: t('invoices.reference') },
  { field: 'total_amount_value', header: t('invoices.total') },
  { field: 'status_label', header: t('invoices.status') },
]
function doExportExcel(): void {
  exportToExcel(displayedInvoices.value, exportColumns, 'supplier-invoices-export')
}

const invoices = ref<Invoice[]>([])
const contacts = ref<Contact[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editingInvoice = ref<Invoice | null>(null)
const supplierFormRef = ref<InstanceType<typeof SupplierInvoiceForm> | null>(null)
const formWrapperEl = ref<HTMLElement | null>(null)

function focusFormInput(): void {
  nextTick(() => {
    formWrapperEl.value?.querySelector<HTMLElement>('input:not([type="hidden"]):not([disabled])')?.focus()
  })
}

const onCloseDialog = useUnsavedChangesGuard(dialogVisible, () => Boolean(supplierFormRef.value?.isDirty))
const uploadDialogVisible = ref(false)
const uploadTargetId = ref<number | null>(null)
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const statusFilter = ref<InvoiceStatus | null>(null)

const editFileBlobUrl = ref<string | null>(null)
const editFileIsPdf = ref(false)
const editFileLoading = ref(false)

watch(dialogVisible, (val) => {
  if (!val && editFileBlobUrl.value) {
    URL.revokeObjectURL(editFileBlobUrl.value)
    editFileBlobUrl.value = null
  }
})

// Preview dialog
const previewVisible = ref(false)
const previewInvoice = ref<Invoice | null>(null)
const previewPayments = ref<Payment[]>([])
const previewPaymentsLoading = ref(false)
const previewFileLoading = ref(false)
const previewDownloading = ref(false)
const previewBlobUrl = ref<string | null>(null)
const previewIsPdf = ref(false)

const previewRemaining = computed(() => {
  if (!previewInvoice.value) return 0
  return parseFloat(previewInvoice.value.total_amount) - parseFloat(previewInvoice.value.paid_amount)
})

const previewIndex = ref(-1)
const previewDialogBodyRef = ref<HTMLElement | null>(null)

function scrollPreviewDialogToBottom(): void {
  nextTick(() => {
    const el = previewDialogBodyRef.value?.closest('.p-dialog-content') as HTMLElement | null
    if (el) el.scrollTop = el.scrollHeight
  })
}

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

const funnelMetrics = computed(() => {
  const visible = displayedInvoices.value
  const totalInvoiced = visible.reduce((sum, invoice) => sum + parseFloat(invoice.total_amount), 0)
  const collected = visible.reduce((sum, invoice) => sum + parseFloat(invoice.paid_amount), 0)
  const overdue = visible
    .filter(isOverdueInvoice)
    .reduce((sum, invoice) => sum + remainingForInvoice(invoice), 0)
  return {
    totalInvoiced,
    collected,
    remaining: Math.max(0, totalInvoiced - collected),
    overdue,
    count: visible.length,
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

const fileFilterOptions = [
  { label: t('common.yes'), value: true },
  { label: t('common.no'), value: false },
]

// Payment dialog state
const paymentDialogVisible = ref(false)
const paymentInvoice = ref<Invoice | null>(null)

function canRecordPayment(invoice: Invoice | null): boolean {
  if (!invoice) return false
  const remaining = parseFloat(invoice.total_amount) - parseFloat(invoice.paid_amount)
  return invoice.status !== 'draft' && remaining > 0
}

function openPaymentDialog(invoice: Invoice) {
  paymentInvoice.value = invoice
  paymentDialogVisible.value = true
}

// Contextual primary row action, chosen by status (handoff decision #3).
function supplierPrimaryAction(invoice: Invoice): InvoiceRowPrimaryAction {
  if (invoice.status === 'draft') {
    return { key: 'edit', label: t('invoices.edit'), icon: 'pi pi-pencil', command: () => openEditDialog(invoice) }
  }
  if (canRecordPayment(invoice)) {
    return {
      key: 'pay',
      label: t('invoices.record_payment'),
      icon: 'pi pi-wallet',
      severity: 'success',
      command: () => openPaymentDialog(invoice),
    }
  }
  if (invoice.file_path) {
    return {
      key: 'view',
      label: t('invoices.actions.view'),
      icon: 'pi pi-eye',
      command: () => openPreviewDialog(invoice),
    }
  }
  return { key: 'edit', label: t('invoices.edit'), icon: 'pi pi-pencil', command: () => openEditDialog(invoice) }
}

// Remaining actions live in the overflow menu; destructive ones are isolated.
function supplierMenuItems(invoice: Invoice): MenuItem[] {
  const primaryKey = supplierPrimaryAction(invoice).key
  const normal: MenuItem[] = [
    { key: 'edit', label: t('invoices.edit'), icon: 'pi pi-pencil', command: () => openEditDialog(invoice) },
  ]
  if (invoice.file_path) {
    normal.push({ key: 'view', label: t('invoices.supplier.preview_file'), icon: 'pi pi-eye', command: () => openPreviewDialog(invoice) })
  }
  normal.push({ key: 'upload', label: t('invoices.upload_file'), icon: 'pi pi-upload', command: () => openUploadDialog(invoice) })
  if (canRecordPayment(invoice)) {
    normal.push({ key: 'pay', label: t('invoices.record_payment'), icon: 'pi pi-wallet', command: () => openPaymentDialog(invoice) })
  }

  const danger: MenuItem[] = []
  if (invoice.status === 'draft') {
    danger.push({
      key: 'delete',
      label: t('common.delete'),
      icon: 'pi pi-trash',
      class: 'invoice-row-actions-danger',
      command: () => confirmDelete(invoice),
    })
  }

  const items = normal.filter((item) => item.key !== primaryKey)
  const dangerItems = danger.filter((item) => item.key !== primaryKey)
  if (dangerItems.length) {
    items.push({ separator: true }, ...dangerItems)
  }
  return items
}

async function onPaymentRecorded(invoiceId: number): Promise<void> {
  await loadInvoices()
  // Refresh preview payments if preview is open for the same invoice
  if (previewInvoice.value?.id === invoiceId) {
    previewPayments.value = await listPayments({ invoice_id: invoiceId })
    // Re-fetch invoice to update paid_amount / status
    const updated = invoices.value.find((inv) => inv.id === invoiceId)
    if (updated) previewInvoice.value = updated
  }
}

function formatAmount(val: string | number) {
  return parseFloat(String(val)).toFixed(2)
}

function contactName(id: number): string {
  const c = contacts.value.find((c) => c.id === id)
  if (!c) return String(id)
  return formatContactDisplayName(c)
}

async function loadInvoices() {
  loading.value = true
  try {
    const filters: Record<string, unknown> = {
      invoice_type: 'fournisseur',
      limit: limitStore.requestLimit(LIMIT_VIEW_KEY),
    }
    if (fiscalYearStore.selectedFiscalYear) {
      filters.from_date = fiscalYearStore.selectedFiscalYear.start_date
      filters.to_date = fiscalYearStore.selectedFiscalYear.end_date
    }
    if (statusFilter.value) filters.invoice_status = statusFilter.value
    const { items, total } = await listInvoicesWithCountApi(filters)
    limitStore.setTotalCount(LIMIT_VIEW_KEY, total)
    invoices.value = items
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
  editFileBlobUrl.value = null
  editFileLoading.value = !!invoice.file_path
  dialogVisible.value = true
  if (invoice.file_path) {
    downloadInvoiceFileApi(invoice.id)
      .then((blob) => {
        editFileIsPdf.value = blob.type === 'application/pdf'
        editFileBlobUrl.value = URL.createObjectURL(blob)
      })
      .catch((e) => console.error('Failed to download invoice file', e))
      .finally(() => { editFileLoading.value = false })
  }
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

async function openPreviewDialog(invoice: Invoice) {
  previewIndex.value = displayedInvoices.value.findIndex((r) => r.id === invoice.id)
  previewInvoice.value = invoice
  if (previewBlobUrl.value) {
    URL.revokeObjectURL(previewBlobUrl.value)
  }
  previewBlobUrl.value = null
  previewPayments.value = []
  previewVisible.value = true

  // Load payments and file in parallel
  previewPaymentsLoading.value = true
  previewFileLoading.value = !!invoice.file_path

  const tasks: Promise<void>[] = [
    listPayments({ invoice_id: invoice.id })
      .then((p) => { previewPayments.value = p })
      .catch((e) => console.error('Failed to load payments', e))
      .finally(() => { previewPaymentsLoading.value = false }),
  ]

  if (invoice.file_path) {
    tasks.push(
      downloadInvoiceFileApi(invoice.id)
        .then((blob) => {
          previewIsPdf.value = blob.type === 'application/pdf'
          previewBlobUrl.value = URL.createObjectURL(blob)
        })
        .catch((e) => console.error('Failed to download invoice file', e))
        .finally(() => { previewFileLoading.value = false }),
    )
  }

  await Promise.all(tasks)
}

function onPreviewHide() {
  if (previewBlobUrl.value) {
    URL.revokeObjectURL(previewBlobUrl.value)
    previewBlobUrl.value = null
  }
  previewInvoice.value = null
}

async function downloadFile(invoice: Invoice) {
  previewDownloading.value = true
  try {
    const blob = await downloadInvoiceFileApi(invoice.id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const ext = invoice.file_path?.split('.').pop() ?? 'pdf'
    a.download = `facture-${invoice.number}.${ext}`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  } finally {
    previewDownloading.value = false
  }
}

function openUploadFromPreview() {
  if (!previewInvoice.value) return
  const inv = previewInvoice.value
  previewVisible.value = false
  nextTick(() => openUploadDialog(inv))
}

async function goToPrevPreview(): Promise<void> {
  const idx = previewIndex.value - 1
  if (idx < 0) return
  previewIndex.value = idx
  await openPreviewDialog(displayedInvoices.value[idx] as Invoice)
}

async function goToNextPreview(): Promise<void> {
  const idx = previewIndex.value + 1
  if (idx >= displayedInvoices.value.length) return
  previewIndex.value = idx
  await openPreviewDialog(displayedInvoices.value[idx] as Invoice)
}

async function goToPrevPreviewBottom(): Promise<void> {
  await goToPrevPreview()
  scrollPreviewDialogToBottom()
}

async function goToNextPreviewBottom(): Promise<void> {
  await goToNextPreview()
  scrollPreviewDialogToBottom()
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
      } catch (error) {
        toast.add({
          severity: 'error',
          summary: getErrorDetail(error, t('common.error.unknown')),
          life: 5000,
        })
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
  await Promise.all([fiscalYearStore.initialize(), limitStore.init()])
  await Promise.all([loadInvoices(), loadContacts()])
})
</script>

<style scoped>
.supplier-invoices-table__actions {
  width: 13rem;
  min-width: 13rem;
}

:deep(.supplier-invoices-table .supplier-invoices-table__actions) {
  white-space: nowrap;
  width: 13rem;
  min-width: 13rem;
}

:deep(.supplier-invoices-table .app-inline-actions) {
  flex-wrap: nowrap;
  justify-content: flex-end;
  min-width: 12rem;
}

.supplier-edit-dialog__form-col {
  min-width: 0;
  overflow: hidden;
}

:deep(.supplier-edit-dialog__form-col .app-dialog-section),
:deep(.supplier-edit-dialog__form-col .app-dialog-form) {
  min-width: 0;
}

:deep(.supplier-edit-dialog__form-col .p-inputtext),
:deep(.supplier-edit-dialog__form-col .p-select),
:deep(.supplier-edit-dialog__form-col .p-inputnumber),
:deep(.supplier-edit-dialog__form-col .p-inputnumber-input) {
  max-width: 100%;
  width: 100%;
  box-sizing: border-box;
}

.supplier-edit-dialog__layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 420px;
  gap: var(--app-space-5);
  align-items: start;
  min-width: 0;
}

.supplier-edit-dialog__preview {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
  min-width: 0;
  overflow: hidden;
  position: sticky;
  top: 0;
}

@media (max-width: 1000px) {
  .supplier-edit-dialog__layout {
    grid-template-columns: 1fr;
  }
}

.upload-dialog {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.preview-nav-bar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--app-space-1);
  padding-bottom: var(--app-space-3);
  border-bottom: 1px solid var(--app-surface-border);
  margin-bottom: var(--app-space-4);
}

.preview-nav-bar--bottom {
  padding-bottom: 0;
  border-bottom: none;
  padding-top: var(--app-space-3);
  border-top: 1px solid var(--app-surface-border);
  margin-bottom: 0;
  margin-top: var(--app-space-4);
}

.preview-nav-bar__counter {
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
  min-width: 3.5rem;
  text-align: center;
}

.supplier-preview-dialog {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.supplier-preview-dialog__body {
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: var(--app-space-5);
  align-items: start;
}

.supplier-preview-dialog__payments {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
}

.supplier-preview-dialog__file {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
}

.supplier-preview-dialog__file-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: var(--p-text-muted-color);
}

.supplier-preview-dialog__file-frame {
  border: 1px solid var(--app-surface-border);
  border-radius: var(--app-surface-radius-sm);
  overflow: hidden;
}

.supplier-preview-dialog__embed {
  width: 100%;
  height: 520px;
  border: none;
  display: block;
}

.supplier-preview-dialog__img {
  width: 100%;
  height: auto;
  display: block;
}

.history-dialog {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.history-dialog__intro {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-3);
}

.supplier-preview-meta {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  font-size: 0.9rem;
  color: var(--p-text-muted-color);
}

.supplier-card__attachment {
  font-size: 0.9rem;
  color: var(--p-primary-color);
  margin-left: auto;
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

@media (max-width: 900px) {
  .supplier-preview-dialog__body {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767px) {
  .history-dialog__intro {
    flex-direction: column;
    align-items: flex-start;
  }

  .history-dialog__label {
    font-size: 0.7rem;
    letter-spacing: 0.03em;
  }

  .history-dialog__value {
    font-size: 0.9rem;
  }
}
</style>
