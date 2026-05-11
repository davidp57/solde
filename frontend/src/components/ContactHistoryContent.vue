<template>
  <div v-if="loading" class="contact-history-loading">
    <section class="app-stat-grid">
      <Skeleton v-for="n in 3" :key="n" height="132px" border-radius="8px" />
    </section>
    <AppTableSkeleton :rows="10" :cols="4" style="margin-top: 1.5rem" />
  </div>

  <template v-else-if="history && !invoiceDetailVisible">
    <AppPanel
      :title="contactFullName(history.contact)"
      :subtitle="contactSubtitle(history.contact)"
    >
      <template #actions>
        <div class="contact-history-actions">
          <Tag :value="t(`contacts.types.${history.contact.type}`)" />
          <Button
            v-if="Number(history.total_due) > 0 && history.contact.type === 'client'"
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
      <AppMobileCardList
        v-if="isMobile && history.invoices.length"
        :items="invoiceRows"
        :empty-message="t('contact_history.no_invoices')"
      >
        <template #card="{ item: data }">
          <div class="app-mobile-card-row app-mobile-card-row--between">
            <span class="app-mobile-card-value" style="font-weight:700">{{ data.number }}</span>
            <Tag
              :value="t(`invoices.statuses.${data.status}`)"
              :severity="statusSeverity(data.status)"
            />
          </div>
          <div class="app-mobile-card-row app-mobile-card-row--between">
            <span class="app-mobile-card-label">{{ formatDisplayDate(data.date) }}</span>
            <span class="app-mobile-card-value" style="font-weight:600">{{ fmt(data.total_amount) }} €</span>
          </div>
          <div v-if="Number(data.balance_due) > 0" class="app-mobile-card-row app-mobile-card-row--between">
            <span class="app-mobile-card-label">{{ t('contact_history.total_due') }} :</span>
            <span class="app-mobile-card-value contact-history-due">{{ fmt(data.balance_due) }} €</span>
          </div>
          <div class="app-mobile-card-actions">
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
      </AppMobileCardList>
      <DataTable
        v-else-if="history.invoices.length"
        v-model:filters="invoiceTableFilters"
        :value="invoiceRows"
        class="app-data-table"
        filter-display="menu"
        striped-rows
        paginator
        :rows="50"
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
      <AppMobileCardList
        v-if="isMobile && history.payments.length"
        :items="paymentRows"
        :empty-message="t('contact_history.no_payments')"
      >
        <template #card="{ item: data }">
          <div class="app-mobile-card-row app-mobile-card-row--between">
            <span class="app-mobile-card-label">{{ formatDisplayDate(data.date) }}</span>
            <span class="app-mobile-card-value" style="font-weight:700">{{ fmt(data.amount) }} €</span>
          </div>
          <div class="app-mobile-card-row">
            <span class="app-mobile-card-label">{{ t('payments.method') }} :</span>
            <span class="app-mobile-card-value">{{ t(`payments.methods.${data.method}`) }}</span>
          </div>
          <div v-if="data.invoice_number" class="app-mobile-card-row">
            <span class="app-mobile-card-label">{{ t('payments.invoice') }} :</span>
            <span class="app-mobile-card-value">{{ data.invoice_number }}</span>
          </div>
          <div class="app-mobile-card-actions">
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
      </AppMobileCardList>
      <DataTable
        v-else-if="history.payments.length"
        v-model:filters="paymentTableFilters"
        :value="paymentRows"
        class="app-data-table"
        filter-display="menu"
        striped-rows
        paginator
        :rows="50"
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

  <template v-else-if="history && invoiceDetailVisible">
    <div class="chd-back-bar">
      <Button
        icon="pi pi-arrow-left"
        text
        :label="t('contact_history.back_to_list')"
        @click="closeInvoiceDetail"
      />
      <span class="chd-back-bar__title">{{ invoiceDetail?.number ?? '' }}</span>
      <div class="chd-back-bar__nav">
        <Button
          icon="pi pi-chevron-left"
          text
          rounded
          size="small"
          :disabled="invoiceDetailIndex <= 0"
          :title="t('common.previous')"
          @click="goToPrevInvoice"
        />
        <span class="chd-back-bar__counter">{{ invoiceDetailIndex + 1 }} / {{ invoiceRows.length }}</span>
        <Button
          icon="pi pi-chevron-right"
          text
          rounded
          size="small"
          :disabled="invoiceDetailIndex >= invoiceRows.length - 1"
          :title="t('common.next')"
          @click="goToNextInvoice"
        />
      </div>
    </div>
    <Skeleton v-if="invoiceDetailLoading" height="220px" border-radius="8px" />

    <!-- Supplier invoice: 2-column layout with file preview -->
    <div v-else-if="invoiceDetail && invoiceDetail.type === 'fournisseur'" class="chd-supplier">
      <div class="chd-supplier__meta">
        <Tag
          :value="t(`invoices.statuses.${invoiceDetail.status}`)"
          :severity="statusSeverity(invoiceDetail.status)"
        />
        <span>{{ formatDisplayDate(invoiceDetail.date) }}</span>
        <span v-if="invoiceDetail.due_date"
          >{{ t('invoices.due_date') }} : {{ formatDisplayDate(invoiceDetail.due_date) }}</span
        >
        <span v-if="invoiceDetail.reference"
          >{{ t('invoices.reference') }} : {{ invoiceDetail.reference }}</span
        >
      </div>

      <div class="chd-supplier__summary">
        <div class="history-dialog__metric">
          <div class="history-dialog__label">{{ t('invoices.total') }}</div>
          <div class="history-dialog__value">{{ fmt(invoiceDetail.total_amount) }} €</div>
        </div>
        <div class="history-dialog__metric">
          <div class="history-dialog__label">{{ t('invoices.paid') }}</div>
          <div class="history-dialog__value history-dialog__value--success">{{ fmt(invoiceDetail.paid_amount) }} €</div>
        </div>
        <div class="history-dialog__metric">
          <div class="history-dialog__label">{{ t('invoices.remaining') }}</div>
          <div
            class="history-dialog__value"
            :class="invoiceRemaining > 0 ? 'history-dialog__value--warn' : 'history-dialog__value--success'"
          >{{ invoiceRemaining.toFixed(2) }} €</div>
        </div>
      </div>

      <div class="chd-supplier__body">
        <!-- Payments -->
        <div class="chd-supplier__payments">
          <h3 class="app-dialog-section__title">{{ t('invoices.history') }}</h3>
          <AppTableSkeleton v-if="invoiceDetailPaymentsLoading" :rows="3" :cols="3" />
          <div v-else-if="invoiceDetailPayments.length === 0" class="app-empty-state">
            {{ t('invoices.no_payments') }}
          </div>
          <DataTable
            v-else
            :value="invoiceDetailPayments"
            class="app-data-table"
            size="small"
          >
            <Column field="date" :header="t('payments.date')" sortable>
              <template #body="{ data }">{{ formatDisplayDate(data.date) }}</template>
            </Column>
            <Column field="amount" :header="t('payments.amount')" class="app-money" sortable>
              <template #body="{ data }">{{ fmt(data.amount) }} €</template>
            </Column>
            <Column field="method" :header="t('payments.method')" sortable>
              <template #body="{ data }">{{ t(`payments.methods.${data.method}`) }}</template>
            </Column>
          </DataTable>
        </div>

        <!-- File preview -->
        <div class="chd-supplier__file">
          <h3 class="app-dialog-section__title">{{ t('invoices.file') }}</h3>
          <div v-if="!invoiceDetail.file_path" class="app-empty-state">
            {{ t('invoices.supplier.no_attachment') }}
          </div>
          <div v-else-if="invoiceFileLoading" class="chd-supplier__file-loading">
            <i class="pi pi-spin pi-spinner" style="font-size: 2rem" />
          </div>
          <div v-else-if="invoiceFileBlobUrl" class="chd-supplier__file-frame">
            <embed
              v-if="invoiceFileBlobIsPdf"
              :src="invoiceFileBlobUrl"
              type="application/pdf"
              class="chd-supplier__embed"
            />
            <img
              v-else
              :src="invoiceFileBlobUrl"
              class="chd-supplier__img"
              :alt="t('invoices.supplier.preview_file')"
            />
          </div>
          <div v-else class="app-empty-state">{{ t('common.error.unknown') }}</div>
        </div>
      </div>
    </div>

    <!-- Client invoice: existing layout -->
    <div v-else-if="invoiceDetail" class="contact-history-dialog"
      :class="{ 'contact-history-dialog--with-preview': invoiceDetail.status === 'archived' && invoiceDetail.file_path }"
    >
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
      <div class="contact-history-dialog__body">
        <div class="contact-history-dialog__main">
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
              v-if="!(invoiceDetail.status === 'archived' && invoiceDetail.file_path)"
              icon="pi pi-file-pdf"
              :label="t('invoices.generate_pdf')"
              severity="secondary"
              outlined
              :loading="downloadingPdf"
              @click="downloadPdf(invoiceDetail)"
            />
            <Button
              v-if="invoiceDetail.status === 'archived' && invoiceDetail.file_path"
              icon="pi pi-download"
              :label="t('invoices.download_file')"
              severity="secondary"
              outlined
              :loading="downloadingPdf"
              @click="downloadAttachment(invoiceDetail)"
            />
            <Button
              v-if="contactEmail && invoiceDetail.type === 'client'"
              icon="pi pi-send"
              :label="t('invoices.send_email')"
              @click="sendEmail(invoiceDetail)"
            />
          </div>
        </div><!-- end contact-history-dialog__main -->
        <!-- Docx preview for archived client invoices -->
        <div
          v-if="invoiceDetail.status === 'archived' && invoiceDetail.file_path"
          class="contact-history-dialog__preview"
        >
          <div v-if="invoiceDocxLoading" class="contact-history-dialog__preview-loading">
            <i class="pi pi-spin pi-spinner" style="font-size: 2rem" />
          </div>
          <DocxPreview v-else-if="invoiceDocxBlob" :blob="invoiceDocxBlob" />
          <div v-else class="app-empty-state">{{ t('common.error.unknown') }}</div>
        </div>
      </div><!-- end contact-history-dialog__body -->
    </div>
  </template>

  <div v-else class="app-empty-state">
    {{ t('common.error.notFound') }}
  </div>

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
import AppMobileCardList from './ui/AppMobileCardList.vue'
import AppTableSkeleton from './ui/AppTableSkeleton.vue'
import DocxPreview from './DocxPreview.vue'
import { getContactHistoryApi, markCreanceDouteuse } from '../api/accounting'
import type { ContactHistory, ContactInvoiceSummary, ContactPaymentSummary } from '../api/accounting'
import { downloadInvoicePdfApi, downloadInvoiceFileApi, getInvoiceApi } from '../api/invoices'
import type { Invoice } from '../api/invoices'
import { getPayment, listPayments } from '../api/payments'
import type { Payment } from '../api/payments'
import {
  dateRangeFilter,
  inFilter,
  numericRangeFilter,
  textFilter,
  useDataTableFilters,
} from '../composables/useDataTableFilters'
import { formatDisplayDate } from '@/utils/format'
import { useBreakpoints } from '../composables/useBreakpoints'
import InvoiceEmailDialog from './InvoiceEmailDialog.vue'

const props = defineProps<{ contactId: number }>()
const emit = defineEmits<{ 'contact-loaded': [name: string] }>()

const { t } = useI18n()
const { isMobile } = useBreakpoints()
const confirm = useConfirm()
const toast = useToast()

const history = ref<ContactHistory | null>(null)
const loading = ref(false)
const invoiceDetailVisible = ref(false)
const invoiceDetailIndex = ref(-1)
const invoiceDetail = ref<Invoice | null>(null)
const invoiceDetailLoading = ref(false)
const paymentDetailVisible = ref(false)
const paymentDetail = ref<Payment | null>(null)
const paymentDetailLoading = ref(false)
const downloadingPdf = ref(false)
const emailDialogInvoiceId = ref<number | null>(null)
const invoiceFileBlobUrl = ref<string | null>(null)
const invoiceFileBlobIsPdf = ref(false)
const invoiceFileLoading = ref(false)
const invoiceDocxBlob = ref<Blob | null>(null)
const invoiceDocxLoading = ref(false)
const invoiceDetailPayments = ref<Payment[]>([])
const invoiceDetailPaymentsLoading = ref(false)

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
  invoiceDetailIndex.value = invoiceRows.value.findIndex((r) => r.id === data.id)
  invoiceDetailVisible.value = true
  await loadInvoiceDetailData(data.id)
}

async function loadInvoiceDetailData(id: number): Promise<void> {
  invoiceDetailLoading.value = true
  invoiceDetail.value = null
  if (invoiceFileBlobUrl.value) {
    URL.revokeObjectURL(invoiceFileBlobUrl.value)
    invoiceFileBlobUrl.value = null
  }
  invoiceDocxBlob.value = null
  invoiceDetailPayments.value = []
  try {
    const inv = await getInvoiceApi(id)
    invoiceDetail.value = inv
    // For supplier invoices: load payments + file in parallel
    if (inv.type === 'fournisseur') {
      invoiceDetailPaymentsLoading.value = true
      if (inv.file_path) invoiceFileLoading.value = true
      const tasks: Promise<void>[] = [
        listPayments({ invoice_id: inv.id })
          .then((p) => { invoiceDetailPayments.value = p })
          .catch((e) => console.error('Failed to load payments', e))
          .finally(() => { invoiceDetailPaymentsLoading.value = false }),
      ]
      if (inv.file_path) {
        tasks.push(
          downloadInvoiceFileApi(inv.id)
            .then((blob) => {
              invoiceFileBlobIsPdf.value = blob.type === 'application/pdf'
              invoiceFileBlobUrl.value = URL.createObjectURL(blob)
            })
            .catch((e) => console.error('Failed to download invoice file', e))
            .finally(() => { invoiceFileLoading.value = false }),
        )
      }
      await Promise.all(tasks)
    }
    // For archived client invoices with file: load docx blob for preview
    if (inv.type === 'client' && inv.status === 'archived' && inv.file_path) {
      invoiceDocxLoading.value = true
      downloadInvoiceFileApi(inv.id)
        .then((blob) => { invoiceDocxBlob.value = blob })
        .catch((e) => console.error('Failed to download docx for preview', e))
        .finally(() => { invoiceDocxLoading.value = false })
    }
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
    closeInvoiceDetail()
  } finally {
    invoiceDetailLoading.value = false
  }
}

function closeInvoiceDetail(): void {
  if (invoiceFileBlobUrl.value) {
    URL.revokeObjectURL(invoiceFileBlobUrl.value)
    invoiceFileBlobUrl.value = null
  }
  invoiceDocxBlob.value = null
  invoiceDetailVisible.value = false
  invoiceDetail.value = null
}

async function goToPrevInvoice(): Promise<void> {
  const idx = invoiceDetailIndex.value - 1
  if (idx < 0) return
  invoiceDetailIndex.value = idx
  await loadInvoiceDetailData(invoiceRows.value[idx].id)
}

async function goToNextInvoice(): Promise<void> {
  const idx = invoiceDetailIndex.value + 1
  if (idx >= invoiceRows.value.length) return
  invoiceDetailIndex.value = idx
  await loadInvoiceDetailData(invoiceRows.value[idx].id)
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

async function downloadAttachment(invoice: Invoice): Promise<void> {
  downloadingPdf.value = true
  try {
    const blob = await downloadInvoiceFileApi(invoice.id)
    const ext = invoice.file_path?.split('.').pop() ?? 'docx'
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `facture-${invoice.number ?? invoice.id}.${ext}`
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

.contact-history-dialog__body {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.contact-history-dialog--with-preview .contact-history-dialog__body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 460px;
  gap: var(--app-space-5);
  align-items: start;
}

.contact-history-dialog__main {
  display: flex;
  flex-direction: column;
}

.contact-history-dialog__preview {
  position: sticky;
  top: 0;
}

.contact-history-dialog__preview-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: var(--p-text-muted-color);
}

/* Inline detail navigation bar */
.chd-back-bar {
  display: flex;
  align-items: center;
  gap: var(--app-space-3);
  padding-bottom: var(--app-space-4);
  border-bottom: 1px solid var(--app-surface-border);
  margin-bottom: var(--app-space-4);
}

.chd-back-bar__title {
  flex: 1;
  font-weight: 600;
  font-size: 1rem;
  color: var(--p-text-color);
}

.chd-back-bar__nav {
  display: flex;
  align-items: center;
  gap: var(--app-space-1);
  margin-left: auto;
}

.chd-back-bar__counter {
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
  min-width: 3.5rem;
  text-align: center;
}

/* Supplier invoice preview layout */
.chd-supplier {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.chd-supplier__meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  font-size: 0.9rem;
  color: var(--p-text-muted-color);
}

.chd-supplier__summary {
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

.history-dialog__value--success { color: var(--p-green-600); }
.history-dialog__value--warn { color: var(--p-orange-500); }

.chd-supplier__body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 460px;
  gap: var(--app-space-5);
  align-items: start;
}

.chd-supplier__payments,
.chd-supplier__file {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
}

.chd-supplier__file-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: var(--p-text-muted-color);
}

.chd-supplier__file-frame {
  border: 1px solid var(--app-surface-border);
  border-radius: var(--app-surface-radius-sm);
  overflow: hidden;
}

.chd-supplier__embed {
  width: 100%;
  height: 520px;
  border: none;
  display: block;
}

.chd-supplier__img {
  width: 100%;
  height: auto;
  display: block;
}

@media (max-width: 1000px) {
  .chd-supplier__body {
    grid-template-columns: 1fr;
  }
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
