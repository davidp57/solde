<template>
  <InvoiceWorkspace
    type="client"
    :title="t('invoices.client.title')"
    :subtitle="t('invoices.client.subtitle')"
    :panel-title="t('invoices.client.portfolio_title')"
    :panel-subtitle="t('invoices.client.portfolio_subtitle')"
    :filters-hint="t('invoices.client.filters_hint')"
    :funnel="funnelMetrics"
    :segments="statusSegments"
    :active-segment="activeSegment"
    v-model:search-value="globalFilterInput"
    :displayed-count="displayedInvoices.length"
    :total-count="loadedCount"
    :loading="loading"
    :active-filters="activeFilterLabels"
    :has-active-filters="hasActiveFilters"
    :segments-label="t('invoices.filter_status')"
    @new="openCreateDialog"
    @segment-change="onSegmentChange"
    @reset-filters="resetAllFilters"
    @export="doExportExcel"
  >
    <template #toolbar-extras>
      <div class="app-field">
        <Button
          :label="showIrrecoverable ? t('invoices.hide_irrecoverable') : t('invoices.show_irrecoverable')"
          :icon="showIrrecoverable ? 'pi pi-eye-slash' : 'pi pi-eye'"
          severity="secondary"
          outlined
          size="small"
          @click="showIrrecoverable = !showIrrecoverable; loadInvoices()"
        />
      </div>
      <div v-if="paidInDisplayed.length > 0" class="app-field">
        <Button
          :label="t('invoices.bulk_archive')"
          icon="pi pi-inbox"
          severity="secondary"
          outlined
          size="small"
          @click="confirmBulkArchive"
        />
      </div>
    </template>

      <AppListLimitBanner
        :view-key="LIMIT_VIEW_KEY"
        :fetched-count="rawFetchedCount"
        :limit="limitStore.systemLimit"
        @reload="loadInvoices"
      />
      <AppTableSkeleton v-if="loading && !invoices.length" :rows="8" :cols="5" />
      <template v-else-if="isMobile">
        <AppMobileCardList :items="invoiceRows" :empty-message="t('invoices.client.empty')">
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
            <div class="app-mobile-card-actions">
              <AppRowActions
                :primary="clientPrimaryAction(data)"
                :menu-items="clientMenuItems(data)"
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
        class="app-data-table invoices-table"
        filter-display="menu"
        striped-rows
        paginator
        :rows="50"
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
          <template #filter="{ filterModel, filterCallback }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="labelOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
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
          <template #filter="{ filterModel, filterCallback }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="statusOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
              show-clear
              :filter-callback="filterCallback"
            />
          </template>
        </Column>
        <Column :header="t('common.actions')" class="invoices-table__actions-column">
          <template #body="{ data }">
            <AppRowActions
              :primary="clientPrimaryAction(data)"
              :menu-items="clientMenuItems(data)"
              :menu-aria-label="t('invoices.actions.more')"
            />
          </template>
        </Column>
        <template #empty>
          <div class="app-empty-state">{{ t('invoices.client.empty') }}</div>
        </template>
        <template #footer>
          <div class="invoices-table-footer">
            <span>{{ t('invoices.table_footer.count', { count: displayedInvoices.length }) }}</span>
            <span class="invoices-table-footer__total">
              {{ t('invoices.total') }} : {{ formatAmount(displayedTotal) }} €
            </span>
          </div>
        </template>
      </DataTable>

    <template #dialogs>
    <Dialog
      :visible="dialogVisible"
      @update:visible="onCloseDialog"
      @show="focusFormInput"
      :header="editingInvoice ? `${t('invoices.edit')} — ${editingInvoice.number}` : t('invoices.new')"
      modal
      class="app-dialog app-dialog--large"
    >
      <div ref="formWrapperEl">
        <ClientInvoiceForm
          ref="invoiceFormRef"
          :invoice="editingInvoice"
          :contacts="contacts"
          @saved="onSaved"
          @cancel="onCloseDialog(false)"
        />
      </div>
    </Dialog>

    <ConfirmDialog />

    <!-- Email send dialog -->
    <InvoiceEmailDialog
      :invoice-id="emailDialogInvoiceId"
      @sent="onEmailSent"
      @close="emailDialogInvoiceId = null"
    />

    <!-- Write-off confirmation dialog -->
    <Dialog
      v-model:visible="writeOffDialogVisible"
      :header="t('invoices.write_off_confirm_title')"
      modal
      :style="{ width: 'min(30rem, 100vw)' }"
    >
      <div class="write-off-dialog-body">
        <p>{{ t('invoices.write_off_confirm_msg') }}</p>
        <p v-if="writeOffTarget" class="write-off-invoice-ref">
          {{ writeOffTarget.number }} — {{ parseFloat(writeOffTarget.total_amount).toFixed(2) }} €
        </p>
      </div>
      <template #footer>
        <Button
          :label="t('common.cancel')"
          severity="secondary"
          outlined
          @click="writeOffDialogVisible = false"
        />
        <Button
          :label="t('invoices.write_off')"
          icon="pi pi-ban"
          severity="danger"
          :loading="writeOffLoading"
          @click="confirmWriteOff"
        />
      </template>
    </Dialog>

    <Dialog
      v-model:visible="historyVisible"
      :header="historyInvoice ? t('invoices.history_title', { number: historyInvoice.number }) : ''"
      modal
      class="app-dialog app-dialog--xlarge"
      @hide="onHistoryHide"
    >
      <div v-if="historyIndex >= 0" class="preview-nav-bar">
        <Button
          icon="pi pi-chevron-left"
          text
          rounded
          size="small"
          :disabled="historyIndex <= 0"
          :title="t('common.previous')"
          @click="goToPrevHistory"
        />
        <span class="preview-nav-bar__counter">{{ historyIndex + 1 }} / {{ displayedInvoices.length }}</span>
        <Button
          icon="pi pi-chevron-right"
          text
          rounded
          size="small"
          :disabled="historyIndex >= displayedInvoices.length - 1"
          :title="t('common.next')"
          @click="goToNextHistory"
        />
      </div>
      <div v-if="historyInvoice" ref="historyDialogBodyRef" class="history-dialog history-dialog--with-preview">
        <section class="app-dialog-intro history-dialog__intro">
          <div>
            <p class="app-dialog-intro__eyebrow">{{ t('invoices.history') }}</p>
            <p class="app-dialog-intro__text">{{ t('invoices.client.history_intro') }}</p>
          </div>
          <Button
            v-if="canRecordPayment(historyInvoice)"
            :label="t('invoices.record_payment')"
            icon="pi pi-wallet"
            size="small"
            @click="openPaymentDialog(historyInvoice)"
          />
        </section>

        <div class="history-dialog__body">
          <div class="history-dialog__payments">
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

            <AppTableSkeleton v-if="historyLoading" :rows="5" :cols="3" />
            <div v-else-if="historyPayments.length === 0" class="app-empty-state">
              {{ t('invoices.no_payments') }}
            </div>
            <AppMobileCardList v-else-if="isMobile" :items="historyPaymentRows" :empty-message="t('invoices.no_payments')">
              <template #card="{ item: data }">
                <div class="app-mobile-card-row app-mobile-card-row--between">
                  <span class="app-mobile-card-label">{{ formatDisplayDate(data.date) }}</span>
                  <span class="app-mobile-card-value" style="font-weight:700">{{ parseFloat(data.amount).toFixed(2) }} €</span>
                </div>
                <div class="app-mobile-card-row">
                  <span class="app-mobile-card-label">{{ t('payments.method') }} :</span>
                  <span class="app-mobile-card-value">{{ t(`payments.methods.${data.method}`) }}</span>
                </div>
                <div v-if="data.cheque_number" class="app-mobile-card-row">
                  <span class="app-mobile-card-label">{{ t('payments.cheque_number') }} :</span>
                  <span class="app-mobile-card-value">{{ data.cheque_number }}</span>
                </div>
              </template>
            </AppMobileCardList>
            <DataTable
              v-else
              v-model:filters="historyTableFilters"
              :value="historyPaymentRows"
              class="app-data-table"
              filter-display="menu"
              paginator
              :rows="50"
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
          </div><!-- end history-dialog__payments -->

          <!-- PDF preview -->
          <div class="history-dialog__preview">
            <h3 class="app-dialog-section__title">{{ t('invoices.email_preview') }}</h3>
            <div v-if="historyPdfLoading" class="history-dialog__preview-loading">
              <i class="pi pi-spin pi-spinner" style="font-size: 2rem" />
            </div>
            <div v-else-if="historyPdfBlobUrl" class="history-dialog__preview-frame">
              <Button
                v-if="isMobile"
                icon="pi pi-external-link"
                :label="t('invoices.open_pdf_new_tab')"
                severity="secondary"
                outlined
                @click="() => window.open(historyPdfBlobUrl!, '_blank', 'noopener,noreferrer')"
              />
              <embed
                v-else
                :src="`${historyPdfBlobUrl}#toolbar=0&navpanes=0&pagemode=none&view=FitH`"
                type="application/pdf"
                class="history-dialog__preview-embed"
                 :title="t('invoices.email_preview')"
              />
            </div>
            <div v-else class="history-dialog__preview-empty">
              <i class="pi pi-file-pdf" />
              <span>{{ t('invoices.email_preview_unavailable') }}</span>
            </div>
          </div><!-- end history-dialog__preview -->
        </div><!-- end history-dialog__body -->

        <div v-if="historyIndex >= 0" class="preview-nav-bar preview-nav-bar--bottom">
          <Button
            icon="pi pi-chevron-left"
            text
            rounded
            size="small"
            :disabled="historyIndex <= 0"
            :title="t('common.previous')"
            @click="goToPrevHistoryBottom"
          />
          <span class="preview-nav-bar__counter">{{ historyIndex + 1 }} / {{ displayedInvoices.length }}</span>
          <Button
            icon="pi pi-chevron-right"
            text
            rounded
            size="small"
            :disabled="historyIndex >= displayedInvoices.length - 1"
            :title="t('common.next')"
            @click="goToNextHistoryBottom"
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
    </template>
  </InvoiceWorkspace>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import ConfirmDialog from 'primevue/confirmdialog'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Tag from 'primevue/tag'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, onUnmounted, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { listContactsApi, type Contact } from '../api/contacts'
import {
  deleteInvoiceApi,
  duplicateInvoiceApi,
  downloadInvoicePdfApi,
  bulkArchiveInvoicesApi,
  listInvoicesApi,
  listInvoicesWithCountApi,
  writeOffInvoiceApi,
  restoreFromWriteoffApi,
  type Invoice,
  type InvoiceStatus,
} from '../api/invoices'
import { listPayments, type Payment } from '../api/payments'
import ClientInvoiceForm from '../components/ClientInvoiceForm.vue'
import InvoiceEmailDialog from '../components/InvoiceEmailDialog.vue'
import InvoiceStatusBadge from '../components/invoices/InvoiceStatusBadge.vue'
import InvoicePaymentDialog from '../components/invoices/InvoicePaymentDialog.vue'
import InvoiceWorkspace from '../components/invoices/InvoiceWorkspace.vue'
import AppRowActions, { type RowAction } from '../components/ui/AppRowActions.vue'
import type { FilterSegment } from '../components/ui/AppFilterSegments.vue'
import type { MenuItem } from 'primevue/menuitem'
import AppListLimitBanner from '../components/ui/AppListLimitBanner.vue'
import AppMobileCardList from '../components/ui/AppMobileCardList.vue'
import { useBreakpoints } from '../composables/useBreakpoints'
import { useKeyboardShortcuts } from '../composables/useKeyboardShortcuts'
import { useTableExport, type ExportColumn } from '../composables/useTableExport'
import { useUnsavedChangesGuard } from '../composables/useUnsavedChangesGuard'
import AppDateRangeFilter from '../components/ui/AppDateRangeFilter.vue'
import AppFilterMultiSelect from '../components/ui/AppFilterMultiSelect.vue'
import AppNumberRangeFilter from '../components/ui/AppNumberRangeFilter.vue'
import AppTableSkeleton from '../components/ui/AppTableSkeleton.vue'
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
import {
  useInvoiceMetrics,
  remainingForInvoice,
  isOverdueInvoice,
  isOpenReceivableInvoice,
} from '../composables/useInvoiceMetrics'
import { useFiscalYearStore } from '../stores/fiscalYear'
import { useListLimitStore } from '../stores/listLimit'
import { formatContactDisplayName } from '../utils/contact'
import { formatDisplayDate } from '@/utils/format'
import { getErrorDetail } from '@/utils/errorUtils'

const { t } = useI18n()
const limitStore = useListLimitStore()
const LIMIT_VIEW_KEY = 'invoices-client'
const { isMobile } = useBreakpoints()
const confirm = useConfirm()
const route = useRoute()
const router = useRouter()
const toast = useToast()
const fiscalYearStore = useFiscalYearStore()
const { exportToExcel } = useTableExport()

const exportColumns = computed<ExportColumn[]>(() => [
  { field: 'number', header: t('invoices.number') },
  { field: 'date', header: t('invoices.date') },
  { field: 'contact_name', header: t('invoices.contact') },
  { field: 'label_label', header: t('invoices.label') },
  { field: 'total_amount_value', header: t('invoices.total') },
  { field: 'status_label', header: t('invoices.status') },
])

function doExportExcel(): void {
  exportToExcel(displayedInvoices.value, exportColumns.value, 'client-invoices-export')
}

const invoices = ref<Invoice[]>([])
const allClientInvoices = ref<Invoice[]>([])
const rawFetchedCount = ref(0)
const contacts = ref<Contact[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const invoiceFormRef = ref<InstanceType<typeof ClientInvoiceForm> | null>(null)
const formWrapperEl = ref<HTMLElement | null>(null)

function focusFormInput(): void {
  nextTick(() => {
    formWrapperEl.value?.querySelector<HTMLElement>('input:not([type="hidden"]):not([disabled])')?.focus()
  })
}

const onCloseDialog = useUnsavedChangesGuard(dialogVisible, () => Boolean(invoiceFormRef.value?.isDirty))
const editingInvoice = ref<Invoice | null>(null)
const statusFilter = ref<InvoiceStatus | null>(null)
const unpaidOnly = ref(false)
const showIrrecoverable = ref(false)

// Email dialog
const emailDialogInvoiceId = ref<number | null>(null)

// Write-off dialog
const writeOffDialogVisible = ref(false)
const writeOffTarget = ref<Invoice | null>(null)
const writeOffLoading = ref(false)

// History dialog
const historyVisible = ref(false)
const historyInvoice = ref<Invoice | null>(null)
const historyIndex = ref(-1)
const historyDialogBodyRef = ref<HTMLElement | null>(null)

function scrollHistoryDialogToBottom(): void {
  nextTick(() => {
    const el = historyDialogBodyRef.value?.closest('.p-dialog-content') as HTMLElement | null
    if (el) el.scrollTop = el.scrollHeight
  })
}
const historyLoading = ref(false)
const historyPayments = ref<Payment[]>([])
const historyPdfBlobUrl = ref<string | null>(null)
const historyPdfLoading = ref(false)
const paymentDialogVisible = ref(false)
const paymentInvoice = ref<Invoice | null>(null)
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

// Debounced input: avoids filtering on every keystroke
const globalFilterInput = ref(globalFilter.value)
let _filterDebounce: ReturnType<typeof setTimeout> | null = null
watch(globalFilterInput, (val) => {
  if (_filterDebounce) clearTimeout(_filterDebounce)
  _filterDebounce = setTimeout(() => {
    globalFilter.value = val
  }, 300)
})
onUnmounted(() => {
  if (_filterDebounce) clearTimeout(_filterDebounce)
})

function resetAllFilters(): void {
  globalFilterInput.value = ''
  globalFilter.value = ''
  resetFilters()
}
const { filters: historyTableFilters } = useDataTableFilters(historyPaymentRows, {
  global: textFilter(''),
  date: dateRangeFilter(),
  amount_value: numericRangeFilter(),
  method: inFilter(),
  cheque_number: textFilter(),
})

const remaining = computed(() => {
  if (!historyInvoice.value) return 0
  return remainingForInvoice(historyInvoice.value)
})

const loadedCount = computed(() => invoices.value.length)

const { portfolioMetrics } = useInvoiceMetrics(allClientInvoices, displayedInvoices)

const funnelMetrics = computed(() => ({
  totalInvoiced: portfolioMetrics.value.totalAmount,
  collected: portfolioMetrics.value.paidAmount,
  remaining: Math.max(0, portfolioMetrics.value.totalAmount - portfolioMetrics.value.paidAmount),
  overdue: portfolioMetrics.value.overdueAmount,
  count: portfolioMetrics.value.visibleCount,
}))

const displayedTotal = computed(() =>
  displayedInvoices.value.reduce((sum, invoice) => sum + parseFloat(invoice.total_amount), 0),
)

// Quick-filter segments. Counts come from the full client-invoice snapshot:
// fiscal-year-scoped for all/draft/paid, cross-year for overdue/unpaid (matching
// the way loadInvoices fetches each segment).
const fiscalYearScopedInvoices = computed(() => {
  const fy = fiscalYearStore.selectedFiscalYear
  if (!fy) return allClientInvoices.value
  return allClientInvoices.value.filter((inv) => inv.date >= fy.start_date && inv.date <= fy.end_date)
})

const statusSegments = computed<FilterSegment[]>(() => [
  {
    key: 'all',
    label: t('invoices.segments.all'),
    count: fiscalYearScopedInvoices.value.filter((inv) => inv.status !== 'irrecoverable').length,
  },
  {
    key: 'overdue',
    label: t('invoices.segments.overdue'),
    count: allClientInvoices.value.filter(isOverdueInvoice).length,
  },
  {
    key: 'unpaid',
    label: t('invoices.segments.unpaid'),
    count: allClientInvoices.value.filter(isOpenReceivableInvoice).length,
  },
  {
    key: 'draft',
    label: t('invoices.segments.draft'),
    count: fiscalYearScopedInvoices.value.filter((inv) => inv.status === 'draft').length,
  },
  {
    key: 'paid',
    label: t('invoices.segments.paid'),
    count: fiscalYearScopedInvoices.value.filter((inv) => inv.status === 'paid').length,
  },
])

const activeSegment = computed(() => {
  if (unpaidOnly.value) return 'unpaid'
  if (statusFilter.value === 'overdue') return 'overdue'
  if (statusFilter.value === 'draft') return 'draft'
  if (statusFilter.value === 'paid') return 'paid'
  if (statusFilter.value == null) return 'all'
  return ''
})

function onSegmentChange(key: string): void {
  switch (key) {
    case 'overdue':
      statusFilter.value = 'overdue'
      unpaidOnly.value = false
      break
    case 'unpaid':
      statusFilter.value = null
      unpaidOnly.value = true
      break
    case 'draft':
      statusFilter.value = 'draft'
      unpaidOnly.value = false
      break
    case 'paid':
      statusFilter.value = 'paid'
      unpaidOnly.value = false
      break
    default:
      statusFilter.value = null
      unpaidOnly.value = false
  }
  void loadInvoices()
}

const paidInDisplayed = computed(() =>
  (displayedInvoices.value as Invoice[]).filter((inv) => inv.status === 'paid'),
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
  { label: t('invoices.statuses.irrecoverable'), value: 'irrecoverable' },
  { label: t('invoices.statuses.archived'), value: 'archived' },
]

const paymentMethodOptions = [
  { label: t('payments.methods.especes'), value: 'especes' },
  { label: t('payments.methods.cheque'), value: 'cheque' },
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

function canRecordPayment(invoice: Invoice | null): boolean {
  if (!invoice) return false
  return (
    invoice.status !== 'draft' &&
    invoice.status !== 'irrecoverable' &&
    invoice.status !== 'archived' &&
    remainingForInvoice(invoice) > 0
  )
}

function contactName(id: number): string {
  const c = contacts.value.find((c) => c.id === id)
  if (!c) return String(id)
  return formatContactDisplayName(c)
}

function isInvoiceEditable(invoice: Invoice): boolean {
  if (invoice.status === 'draft') return true
  if (invoice.status === 'sent' && parseFloat(invoice.paid_amount) === 0) return true
  return false
}

// Contextual primary row action, chosen by status (handoff decision #3).
function clientPrimaryAction(invoice: Invoice): RowAction {
  if (invoice.status === 'draft') {
    return { key: 'edit', label: t('invoices.edit'), icon: 'pi pi-pencil', command: () => openEditDialog(invoice) }
  }
  if (isOverdueInvoice(invoice)) {
    return {
      key: 'remind',
      label: t('invoices.actions.relaunch'),
      icon: 'pi pi-send',
      severity: 'danger',
      command: () => sendEmail(invoice),
    }
  }
  if (invoice.status === 'paid') {
    return { key: 'view', label: t('invoices.actions.view'), icon: 'pi pi-eye', command: () => openHistory(invoice) }
  }
  if (invoice.status === 'disputed') {
    return {
      key: 'process',
      label: t('invoices.actions.process'),
      icon: 'pi pi-exclamation-triangle',
      command: () => openHistory(invoice),
    }
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
  return { key: 'view', label: t('invoices.actions.view'), icon: 'pi pi-eye', command: () => openHistory(invoice) }
}

// Remaining actions live in the overflow menu; destructive ones are isolated.
function clientMenuItems(invoice: Invoice): MenuItem[] {
  const primaryKey = clientPrimaryAction(invoice).key
  const normal: MenuItem[] = [
    { key: 'history', label: t('invoices.history'), icon: 'pi pi-eye', command: () => openHistory(invoice) },
  ]
  if (canRecordPayment(invoice)) {
    normal.push({ key: 'pay', label: t('invoices.record_payment'), icon: 'pi pi-wallet', command: () => openPaymentDialog(invoice) })
  }
  if (isInvoiceEditable(invoice)) {
    normal.push({ key: 'edit', label: t('invoices.edit'), icon: 'pi pi-pencil', command: () => openEditDialog(invoice) })
  }
  normal.push({ key: 'pdf', label: t('invoices.generate_pdf'), icon: 'pi pi-file-pdf', command: () => openPdf(invoice) })
  if (invoice.status !== 'archived') {
    normal.push({ key: 'send', label: t('invoices.send_email'), icon: 'pi pi-send', command: () => sendEmail(invoice) })
    normal.push({ key: 'duplicate', label: t('invoices.duplicate'), icon: 'pi pi-copy', command: () => duplicate(invoice) })
  }
  if (invoice.status === 'irrecoverable') {
    normal.push({ key: 'restore', label: t('invoices.restore_from_writeoff'), icon: 'pi pi-refresh', command: () => restoreFromWriteoff(invoice) })
  }

  const danger: MenuItem[] = []
  const remaining = parseFloat(invoice.total_amount) - parseFloat(invoice.paid_amount)
  if (
    invoice.status !== 'draft' &&
    invoice.status !== 'paid' &&
    invoice.status !== 'irrecoverable' &&
    invoice.status !== 'archived' &&
    remaining > 0
  ) {
    danger.push({
      key: 'writeoff',
      label: t('invoices.write_off'),
      icon: 'pi pi-ban',
      class: 'app-row-actions-danger',
      command: () => openWriteOffDialog(invoice),
    })
  }
  if (invoice.status === 'draft') {
    danger.push({
      key: 'delete',
      label: t('common.delete'),
      icon: 'pi pi-trash',
      class: 'app-row-actions-danger',
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

async function loadInvoices() {
  loading.value = true
  try {
    const filters: Record<string, unknown> = {
      invoice_type: 'client',
      limit: limitStore.requestLimit(LIMIT_VIEW_KEY),
    }
    // Skip fiscal-year date filter for cross-year queries (overdue, unpaid from dashboard)
    const skipDateFilter = unpaidOnly.value || statusFilter.value === 'overdue'
    if (fiscalYearStore.selectedFiscalYear && !skipDateFilter) {
      filters.from_date = fiscalYearStore.selectedFiscalYear.start_date
      filters.to_date = fiscalYearStore.selectedFiscalYear.end_date
    }
    // For 'overdue', don't pass invoice_status to API — the DB field may be stale.
    // Filter client-side via isOverdueInvoice() to match dashboard logic.
    if (statusFilter.value && statusFilter.value !== 'overdue') {
      filters.invoice_status = statusFilter.value
    }
    const { items: all, total } = await listInvoicesWithCountApi(filters)
    limitStore.setTotalCount(LIMIT_VIEW_KEY, total)
    rawFetchedCount.value = all.length
    if (unpaidOnly.value) {
      invoices.value = all.filter(
        (inv) =>
          inv.status !== 'draft' &&
          inv.status !== 'irrecoverable' &&
          parseFloat(inv.total_amount) - parseFloat(inv.paid_amount) > 0,
      )
    } else if (statusFilter.value === 'overdue') {
      invoices.value = all.filter(isOverdueInvoice)
    } else if (!showIrrecoverable.value && !statusFilter.value) {
      invoices.value = all.filter((inv) => inv.status !== 'irrecoverable')
    } else {
      invoices.value = all
    }
    openInvoiceFromQuery()
  } finally {
    loading.value = false
  }
}

async function loadReceivablesSnapshot() {
  allClientInvoices.value = await listInvoicesApi({ invoice_type: 'client', limit: 5000 })
}

async function refreshInvoicesData() {
  await Promise.all([loadInvoices(), loadReceivablesSnapshot()])
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
  const all = await listContactsApi()
  contacts.value = all.filter((c) => c.type === 'client' || c.type === 'les_deux')
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
  void refreshInvoicesData()
}

useKeyboardShortcuts({
  onNew: () => {
    if (!dialogVisible.value) openCreateDialog()
  },
  onSave: () => {
    if (dialogVisible.value) void invoiceFormRef.value?.submit()
  },
  onClose: () => {
    if (dialogVisible.value) dialogVisible.value = false
  },
})

async function openPdf(invoice: Invoice) {
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
  }
}

function sendEmail(invoice: Invoice): void {
  emailDialogInvoiceId.value = invoice.id
}

async function onEmailSent(): Promise<void> {
  emailDialogInvoiceId.value = null
  await refreshInvoicesData()
}

function openWriteOffDialog(invoice: Invoice): void {
  writeOffTarget.value = invoice
  writeOffDialogVisible.value = true
}

async function confirmWriteOff(): Promise<void> {
  if (!writeOffTarget.value) return
  writeOffLoading.value = true
  try {
    await writeOffInvoiceApi(writeOffTarget.value.id)
    writeOffDialogVisible.value = false
    toast.add({ severity: 'success', summary: t('invoices.write_off'), life: 3000 })
    await refreshInvoicesData()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  } finally {
    writeOffLoading.value = false
  }
}

async function restoreFromWriteoff(invoice: Invoice): Promise<void> {
  try {
    await restoreFromWriteoffApi(invoice.id)
    toast.add({ severity: 'success', summary: t('invoices.restore_from_writeoff'), life: 3000 })
    await refreshInvoicesData()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  }
}

function confirmBulkArchive(): void {
  confirm.require({
    header: t('invoices.bulk_archive_confirm_title'),
    message: t('invoices.bulk_archive_confirm_msg'),
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: t('common.confirm'),
    rejectLabel: t('common.cancel'),
    accept: () => executeBulkArchive(),
  })
}

async function executeBulkArchive(): Promise<void> {
  const ids = paidInDisplayed.value.map((inv) => inv.id)
  try {
    const result = await bulkArchiveInvoicesApi(ids)
    toast.add({
      severity: 'success',
      summary: t('invoices.bulk_archive_result', { archived: result.archived, skipped: result.skipped }),
      life: 5000,
    })
    await refreshInvoicesData()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  }
}

async function duplicate(invoice: Invoice) {
  try {
    await duplicateInvoiceApi(invoice.id)
    toast.add({ severity: 'success', summary: t('invoices.duplicated'), life: 3000 })
    await refreshInvoicesData()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  }
}

async function openHistory(invoice: Invoice) {
  historyIndex.value = displayedInvoices.value.findIndex((r) => r.id === invoice.id)
  historyInvoice.value = invoice
  historyVisible.value = true
  if (historyPdfBlobUrl.value) {
    URL.revokeObjectURL(historyPdfBlobUrl.value)
  }
  historyPdfBlobUrl.value = null
  historyPdfLoading.value = true
  await Promise.all([
    loadHistoryPayments(invoice.id),
    downloadInvoicePdfApi(invoice.id)
      .then((blob) => { historyPdfBlobUrl.value = URL.createObjectURL(blob) })
      .catch((e) => console.error('Failed to download invoice PDF', e))
      .finally(() => { historyPdfLoading.value = false }),
  ])
}

function onHistoryHide() {
  if (historyPdfBlobUrl.value) {
    URL.revokeObjectURL(historyPdfBlobUrl.value)
    historyPdfBlobUrl.value = null
  }
}

async function goToPrevHistory(): Promise<void> {
  const idx = historyIndex.value - 1
  if (idx < 0) return
  historyIndex.value = idx
  const invoice = invoices.value.find((i) => i.id === displayedInvoices.value[idx]?.id)
  if (invoice) await openHistory(invoice)
}

async function goToNextHistory(): Promise<void> {
  const idx = historyIndex.value + 1
  if (idx >= displayedInvoices.value.length) return
  historyIndex.value = idx
  const invoice = invoices.value.find((i) => i.id === displayedInvoices.value[idx]?.id)
  if (invoice) await openHistory(invoice)
}

async function goToPrevHistoryBottom(): Promise<void> {
  await goToPrevHistory()
  scrollHistoryDialogToBottom()
}

async function goToNextHistoryBottom(): Promise<void> {
  await goToNextHistory()
  scrollHistoryDialogToBottom()
}

async function loadHistoryPayments(invoiceId: number) {
  historyLoading.value = true
  historyPayments.value = []
  try {
    historyPayments.value = await listPayments({ invoice_id: invoiceId })
    const refreshedInvoice = invoices.value.find((candidate) => candidate.id === invoiceId)
    if (refreshedInvoice) {
      historyInvoice.value = refreshedInvoice
    }
  } finally {
    historyLoading.value = false
  }
}

function openPaymentDialog(invoice: Invoice) {
  paymentInvoice.value = invoice
  paymentDialogVisible.value = true
}

async function onPaymentRecorded(invoiceId: number): Promise<void> {
  await refreshInvoicesData()
  paymentInvoice.value = invoices.value.find((invoice) => invoice.id === invoiceId) ?? null
  if (historyVisible.value && historyInvoice.value?.id === invoiceId) {
    await loadHistoryPayments(invoiceId)
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
        await refreshInvoicesData()
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
    void refreshInvoicesData()
  },
)

watch(
  () => route.query.invoiceId,
  () => {
    openInvoiceFromQuery()
  },
)

watch(
  () => route.query.status,
  (newStatus) => {
    const status = Array.isArray(newStatus) ? newStatus[0] : newStatus
    statusFilter.value = status ? (status as InvoiceStatus) : null
  },
)

watch(
  () => route.query.unpaid,
  (newVal) => {
    unpaidOnly.value = newVal === '1'
  },
)

onMounted(async () => {
  await Promise.all([fiscalYearStore.initialize(), limitStore.init()])
  const queryStatus = Array.isArray(route.query.status)
    ? route.query.status[0]
    : route.query.status
  if (queryStatus) {
    statusFilter.value = queryStatus as InvoiceStatus
  }
  unpaidOnly.value = route.query.unpaid === '1'
  await Promise.all([refreshInvoicesData(), loadContacts()])
  if (route.query.create === '1') {
    openCreateDialog()
    void router.replace({ name: 'invoices-client', query: { ...route.query, create: undefined } })
  }
})
</script>

<style scoped>
.invoices-table__actions-column {
  width: 16rem;
}

.invoices-table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-3);
  font-size: 0.9rem;
  color: var(--p-text-muted-color);
}

.invoices-table-footer__total {
  font-weight: 800;
  color: var(--p-text-color);
  font-variant-numeric: tabular-nums;
}

.history-dialog {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.history-dialog--with-preview .history-dialog__body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 480px;
  gap: var(--app-space-5);
  align-items: start;
}

.history-dialog__payments {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.history-dialog__preview {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
  position: sticky;
  top: 0;
}

.history-dialog__preview-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: var(--p-text-muted-color);
}

.history-dialog__preview-frame {
  border: 1px solid var(--app-surface-border);
  border-radius: var(--app-surface-radius-sm);
  overflow: hidden;
}

.history-dialog__preview-link {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: var(--app-space-4);
  text-decoration: none;
}

.history-dialog__preview-embed {
  width: 100%;
  height: 520px;
  border: none;
  display: block;
}

.history-dialog__preview-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--app-space-3);
  height: 200px;
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
}

.history-dialog__preview-empty .pi {
  font-size: 2.5rem;
}

.history-dialog__preview-dl {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--app-space-3);
}

.history-dialog__intro {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-3);
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

@media (max-width: 1050px) {
  .history-dialog--with-preview .history-dialog__body {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767px) {
  .history-dialog__intro {
    flex-direction: column;
    align-items: flex-start;
  }

  .history-dialog__summary {
    grid-template-columns: 1fr;
  }
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
</style>
