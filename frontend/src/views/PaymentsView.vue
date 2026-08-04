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
        :label="t('payments.metrics.cheques_to_deposit')"
        :value="formatAmount(chequesToDepositAmount)"
        :caption="t('payments.metrics.cheques_caption', { count: chequesToDepositCount })"
        tone="warn"
      />
    </section>

    <AppPanel :title="t('payments.workspace_title')" :subtitle="t('payments.workspace_subtitle')">
      <div class="app-toolbar">
        <div class="app-toolbar__meta">
          <p class="app-toolbar__hint">{{ t('payments.filters_hint') }}</p>
          <AppListState
            :displayed-count="filtered.length"
            :total-count="payments.length"
            :loading="loading"
            :search-text="filterText"
            :active-filters="activeFilterLabels"
          />
          <Button
            :label="t('common.reset_filters')"
            icon="pi pi-filter-slash"
            severity="secondary"
            outlined
            size="small"
            :disabled="!hasAnyFilters"
            @click="resetAllFilters"
          />
          <Button
            :label="t('common.export_excel')"
            icon="pi pi-file-excel"
            severity="secondary"
            outlined
            size="small"
            @click="doExportExcel"
          />
          <Button
            data-testid="payments-show-all-history"
            :label="t('payments.show_all_history')"
            :icon="showAllHistory ? 'pi pi-calendar-times' : 'pi pi-calendar'"
            :severity="showAllHistory ? 'primary' : 'secondary'"
            outlined
            size="small"
            @click="showAllHistory = !showAllHistory; loadPayments()"
          />
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

      <AppListLimitBanner
        :view-key="LIMIT_VIEW_KEY"
        :fetched-count="payments.length"
        :limit="limitStore.systemLimit"
        @reload="loadPayments"
      />
      <AppTableSkeleton v-if="loading && !payments.length" :rows="8" :cols="5" />
      <template v-else-if="isMobile">
        <AppMobileCardList :items="paymentRows" :empty-message="t('payments.empty')">
          <template #card="{ item: data }">
            <div class="app-mobile-card-row app-mobile-card-row--between">
              <span class="app-mobile-card-label">{{ formatDisplayDate(data.date) }}</span>
              <span class="app-mobile-card-value" style="font-weight:700">{{ formatAmount(data.amount) }} €</span>
            </div>
            <div class="app-mobile-card-row" v-if="data.invoice_number">
              <span class="app-mobile-card-label">{{ t('payments.invoice') }} :</span>
              <span class="app-mobile-card-value">{{ data.invoice_number }}</span>
            </div>
            <div class="app-mobile-card-row">
              <Tag :value="t(`payments.methods.${data.method}`)" />
              <span v-if="data.reference_value" class="app-mobile-card-value">{{ data.reference_value }}</span>
              <span v-if="data.cheque_number" class="app-mobile-card-label">({{ data.cheque_number }})</span>
            </div>
            <div class="app-mobile-card-row">
              <span class="app-mobile-card-label">{{ t('payments.deposited') }} :</span>
              <i v-if="data.deposited" class="pi pi-check text-green-500" />
              <span v-else-if="data.in_deposit" class="payments-status--transit"><i class="pi pi-clock" /> {{ t('payments.deposit_status_in_transit') }}</span>
              <i v-else class="pi pi-times text-red-400" />
            </div>
            <div class="app-mobile-card-actions">
              <AppRowActions
                :primary="paymentPrimaryAction(data)"
                :menu-items="paymentMenuItems(data)"
                :menu-aria-label="t('common.actions')"
              />
            </div>
          </template>
        </AppMobileCardList>
      </template>
      <DataTable
        v-else
        v-model:filters="tableFilters"
        :value="paymentRows"
        :loading="loading"
        class="app-data-table payments-table"
        filter-display="menu"
        striped-rows
        paginator
        :rows="50"
        :rows-per-page-options="[20, 50, 100, 500]"
        data-key="id"
        size="small"
        row-hover
        :global-filter-fields="[
          'date',
          'amount_value',
          'method',
          'reference_value',
          'invoice_number',
          'cheque_number',
          'deposited',
        ]"
        sort-field="date"
        :sort-order="-1"
        removable-sort
        @value-change="syncDisplayedPayments"
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
          filter-field="amount_value"
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            {{ formatAmount(data.amount) }}
          </template>
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column
          field="method_label"
          :header="t('payments.method')"
          sortable
          filter-field="method"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            <Tag :value="t(`payments.methods.${data.method}`)" />
          </template>
          <template #filter="{ filterModel }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="allMethodOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
              show-clear
            />
          </template>
        </Column>
        <Column
          field="invoice_number"
          :header="t('payments.invoice')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ data.invoice_number ?? '' }}</template>
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('payments.invoice')" />
          </template>
        </Column>
        <Column
          field="reference_value"
          :header="t('payments.reference')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ data.reference_value }}</template>
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('payments.reference')" />
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
        <Column
          field="deposited_label"
          :header="t('payments.deposited')"
          sortable
          filter-field="deposited"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            <i
              v-if="data.deposited"
              class="pi pi-check text-green-500"
            />
            <span
              v-else-if="data.in_deposit"
              class="payments-status--transit"
            >
              <i class="pi pi-clock" />
              {{ t('payments.deposit_status_in_transit') }}
            </span>
            <i
              v-else
              class="pi pi-times text-red-400"
            />
          </template>
          <template #filter="{ filterModel }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="yesNoOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
              show-clear
            />
          </template>
        </Column>
        <Column :header="t('common.actions')" class="payments-table__actions">
          <template #body="{ data }">
            <AppRowActions
              :primary="paymentPrimaryAction(data)"
              :menu-items="paymentMenuItems(data)"
              :menu-aria-label="t('common.actions')"
            />
          </template>
        </Column>
        <template #empty>
          <div class="app-empty-state">{{ t('payments.empty') }}</div>
        </template>
      </DataTable>
    </AppPanel>
    <Dialog
      v-model:visible="dialogVisible"
      :header="t('payments.edit')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div class="app-dialog-form">
        <div class="app-form-grid">
          <div class="app-field">
            <label class="app-field__label">{{ t('payments.invoice') }}</label>
            <InputText :model-value="editingPayment?.invoice_number ?? ''" disabled />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('payments.date') }}</label>
            <InputText v-model="paymentForm.date" type="date" disabled />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('payments.amount') }}</label>
            <InputText
              v-model="paymentForm.amount"
              type="number"
              step="0.01"
              min="0.01"
              disabled
            />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('payments.method') }}</label>
            <Select
              v-model="paymentForm.method"
              :options="editableMethodOptions"
              option-label="label"
              option-value="value"
              disabled
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
    <Dialog
      v-model:visible="cancelDialogVisible"
      :header="t('payments.cancel_title')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div class="app-dialog-form" data-testid="payment-cancel-body">
        <p v-if="cancelPreviewLoading">{{ t('payments.cancel_loading') }}</p>
        <template v-else-if="cancelPreview && cancelPreview.can_cancel">
          <p>{{ cancelIntroText }}</p>
          <p v-if="cancelDepositText">{{ cancelDepositText }}</p>
          <p class="app-dialog-hint">{{ t('payments.cancel_hint') }}</p>
        </template>
        <Message v-else-if="cancelPreview" severity="warn">{{ cancelRefusalText }}</Message>
      </div>
      <template #footer>
        <Button :label="t('common.close')" text @click="cancelDialogVisible = false" />
        <Button
          v-if="cancelPreview?.can_cancel"
          data-testid="payment-cancel-confirm"
          :label="t('payments.cancel_confirm')"
          icon="pi pi-trash"
          severity="danger"
          :loading="cancelling"
          @click="confirmCancelPayment"
        />
      </template>
    </Dialog>
  </AppPage>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import type { MenuItem } from 'primevue/menuitem'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import ToggleButton from 'primevue/togglebutton'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  cancelPayment,
  getPaymentCancelPreview,
  listPaymentsWithCount,
  updatePayment,
  type Payment,
  type PaymentCancelPreview,
  type PaymentMethod,
} from '@/api/payments'
import { useAuthStore } from '@/stores/auth'
import AppPage from '@/components/ui/AppPage.vue'
import AppDateRangeFilter from '@/components/ui/AppDateRangeFilter.vue'
import AppFilterMultiSelect from '@/components/ui/AppFilterMultiSelect.vue'
import AppListState from '@/components/ui/AppListState.vue'
import AppNumberRangeFilter from '@/components/ui/AppNumberRangeFilter.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppPanel from '@/components/ui/AppPanel.vue'
import AppStatCard from '@/components/ui/AppStatCard.vue'
import AppRowActions, { type RowAction } from '@/components/ui/AppRowActions.vue'
import AppTableSkeleton from '@/components/ui/AppTableSkeleton.vue'
import AppMobileCardList from '@/components/ui/AppMobileCardList.vue'
import { useFiscalYearStore } from '@/stores/fiscalYear'
import AppListLimitBanner from '@/components/ui/AppListLimitBanner.vue'
import { useListLimitStore } from '@/stores/listLimit'
import { formatDisplayDate } from '@/utils/format'
import { collectActiveFilterLabels } from '../composables/activeFilterLabels'
import { useBreakpoints } from '../composables/useBreakpoints'
import { useTableExport, type ExportColumn } from '@/composables/useTableExport'
import {
  dateRangeFilter,
  inFilter,
  numericRangeFilter,
  textFilter,
  useDataTableFilters,
} from '../composables/useDataTableFilters'

const { t } = useI18n()
const { isMobile } = useBreakpoints()
const route = useRoute()
const toast = useToast()
const fiscalYearStore = useFiscalYearStore()
const limitStore = useListLimitStore()
const LIMIT_VIEW_KEY = 'payments'
const { exportToExcel } = useTableExport()
const exportColumns: ExportColumn[] = [
  { field: 'date', header: t('payments.date') },
  { field: 'amount_value', header: t('payments.amount') },
  { field: 'method_label', header: t('payments.method') },
  { field: 'invoice_number', header: t('payments.invoice') },
  { field: 'reference_value', header: t('payments.reference') },
  { field: 'cheque_number', header: t('payments.cheque_number') },
  { field: 'deposited_label', header: t('payments.deposited') },
]
function doExportExcel(): void {
  exportToExcel(filtered.value, exportColumns, 'payments-export')
}

const authStore = useAuthStore()
const payments = ref<Payment[]>([])
const loading = ref(false)
const saving = ref(false)
const undepositedOnly = ref(false)
// Lifts the fiscal-year date filter — records dated outside the selected year
// (or outside every year) are otherwise invisible here.
const showAllHistory = ref(false)

const dialogVisible = ref(false)
const editingPayment = ref<Payment | null>(null)
const cancelDialogVisible = ref(false)
const cancelPreviewLoading = ref(false)
const cancelling = ref(false)
const cancelPreview = ref<PaymentCancelPreview | null>(null)
const cancelTarget = ref<Payment | null>(null)
const paymentForm = ref({
  amount: '',
  date: '',
  method: 'cheque' as PaymentMethod,
  cheque_number: '',
  reference: '',
  notes: '',
})
const paymentRows = computed(() =>
  payments.value.map((payment) => ({
    ...payment,
    amount_value: parseFloat(payment.amount),
    method_label: t(`payments.methods.${payment.method}`),
    reference_value: paymentReference(payment),
    deposited_label: payment.deposited
      ? t('common.yes')
      : payment.in_deposit
        ? t('payments.deposit_status_in_transit')
        : t('common.no'),
  })),
)
const {
  filters: tableFilters,
  globalFilter: filterText,
  displayedRows: filtered,
  syncDisplayedRows: syncDisplayedPayments,
  resetFilters,
  hasActiveFilters,
} = useDataTableFilters(paymentRows, {
  global: textFilter(''),
  date: dateRangeFilter(),
  amount_value: numericRangeFilter(),
  method: inFilter(),
  reference_value: textFilter(),
  invoice_number: textFilter(),
  cheque_number: textFilter(),
  deposited: inFilter(),
})
const totalAmount = computed(() =>
  filtered.value.reduce((sum, payment) => sum + parseFloat(payment.amount), 0),
)
const averageAmount = computed(() =>
  filtered.value.length ? totalAmount.value / filtered.value.length : 0,
)
const chequesToDepositCount = computed(
  () => filtered.value.filter((p) => p.method === 'cheque' && !p.deposited && !p.in_deposit).length,
)
const chequesToDepositAmount = computed(() =>
  filtered.value
    .filter((p) => p.method === 'cheque' && !p.deposited && !p.in_deposit)
    .reduce((sum, p) => sum + parseFloat(p.amount), 0),
)
const activeFilterLabels = computed(() =>
  collectActiveFilterLabels(undepositedOnly.value ? t('payments.filter_undeposited') : undefined),
)
const allMethodOptions = computed(() => [
  { label: t('payments.methods.especes'), value: 'especes' },
  { label: t('payments.methods.cheque'), value: 'cheque' },
  { label: t('payments.methods.virement'), value: 'virement' },
])
const editableMethodOptions = computed(() => {
  const currentMethod = editingPayment.value?.method

  if (!currentMethod) {
    return allMethodOptions.value
  }

  if (currentMethod === 'especes' || currentMethod === 'cheque') {
    return allMethodOptions.value.filter((option) => option.value === currentMethod)
  }

  if (currentMethod === 'virement') {
    return allMethodOptions.value
  }

  return allMethodOptions.value
})
const yesNoOptions = computed(() => [
  { label: t('common.yes'), value: true },
  { label: t('common.no'), value: false },
])

function paymentReference(payment: Payment): string {
  return payment.reference ?? ''
}

function formatAmount(value: string | number): string {
  return `${parseFloat(String(value)).toFixed(2)} €`
}

function normalizeOptionalField(value: string): string | null {
  const trimmedValue = value.trim()
  return trimmedValue.length > 0 ? trimmedValue : null
}

function paymentPrimaryAction(payment: Payment): RowAction {
  return {
    key: 'edit',
    label: t('payments.edit'),
    icon: 'pi pi-pencil',
    severity: 'secondary',
    command: () => openEditDialog(payment),
  }
}

// Cancelling destroys the payment and its accounting entries — admins only.
function paymentMenuItems(payment: Payment): MenuItem[] {
  if (!authStore.isAdmin) return []
  return [
    {
      label: t('payments.cancel_action'),
      icon: 'pi pi-trash',
      class: 'app-row-actions-danger',
      command: () => openCancelDialog(payment),
    },
  ]
}

async function openCancelDialog(payment: Payment): Promise<void> {
  cancelTarget.value = payment
  cancelPreview.value = null
  cancelDialogVisible.value = true
  cancelPreviewLoading.value = true
  try {
    cancelPreview.value = await getPaymentCancelPreview(payment.id)
  } catch {
    cancelDialogVisible.value = false
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    cancelPreviewLoading.value = false
  }
}

const cancelIntroText = computed(() => {
  const preview = cancelPreview.value
  if (!preview) return ''
  return t('payments.cancel_intro', {
    amount: formatAmount(preview.amount),
    date: formatDisplayDate(preview.date),
  })
})

const cancelDepositText = computed(() => {
  const preview = cancelPreview.value
  if (!preview || preview.deposit_id === null) return ''
  const depositDate = formatDisplayDate(preview.deposit_date ?? '')
  if (preview.deposit_will_be_deleted) {
    return t('payments.cancel_deposit_deleted', { date: depositDate })
  }
  return t('payments.cancel_deposit_kept', {
    date: depositDate,
    before: formatAmount(preview.deposit_total_before ?? '0'),
    after: formatAmount(preview.deposit_total_after ?? '0'),
  })
})

const cancelRefusalText = computed(() => {
  const code = cancelPreview.value?.reason_code
  return code ? t(`payments.cancel_refused.${code}`) : ''
})

async function confirmCancelPayment(): Promise<void> {
  const payment = cancelTarget.value
  if (!payment) return
  cancelling.value = true
  try {
    await cancelPayment(payment.id)
    cancelDialogVisible.value = false
    // Drop the row here rather than re-fetching the list: the screen must not depend on
    // a second request to reflect what the server has already confirmed.
    payments.value = payments.value.filter((candidate) => candidate.id !== payment.id)
    toast.add({ severity: 'success', summary: t('payments.cancelled'), life: 3000 })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    cancelling.value = false
  }
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

/** Replace a row with what the server just returned, in place. */
function applyUpdatedPayment(updated: Payment): void {
  const index = payments.value.findIndex((candidate) => candidate.id === updated.id)
  if (index >= 0) payments.value[index] = { ...payments.value[index], ...updated }
}

async function savePayment() {
  if (!editingPayment.value) return

  saving.value = true
  try {
    const updated = await updatePayment(editingPayment.value.id, {
      cheque_number:
        paymentForm.value.method === 'cheque'
          ? normalizeOptionalField(paymentForm.value.cheque_number)
          : null,
      reference: normalizeOptionalField(paymentForm.value.reference),
      notes: normalizeOptionalField(paymentForm.value.notes),
    })
    dialogVisible.value = false
    applyUpdatedPayment(updated)
    toast.add({ severity: 'success', summary: t('payments.updated'), life: 3000 })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    saving.value = false
  }
}

const hasAnyFilters = computed(() => hasActiveFilters.value || undepositedOnly.value)

function resetAllFilters(): void {
  resetFilters()
  undepositedOnly.value = false
  void loadPayments()
}

async function loadPayments() {
  loading.value = true
  try {
    // Skip fiscal-year date filter when showing all undeposited — they can span multiple years
    const dateFilter = undepositedOnly.value || showAllHistory.value
      ? {}
      : {
          from_date: fiscalYearStore.selectedFiscalYear?.start_date,
          to_date: fiscalYearStore.selectedFiscalYear?.end_date,
        }
    const { items, total } = await listPaymentsWithCount({
      invoice_type: 'client',
      undeposited_only: undepositedOnly.value,
      ...dateFilter,
      limit: limitStore.requestLimit(LIMIT_VIEW_KEY),
    })
    limitStore.setTotalCount(LIMIT_VIEW_KEY, total)
    payments.value = items
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    loading.value = false
  }
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

watch(
  () => route.query.undeposited,
  (newValue) => {
    undepositedOnly.value = newValue === '1'
  },
)

onMounted(async () => {
  await Promise.all([fiscalYearStore.initialize(), limitStore.init()])
  if (route.query.undeposited === '1') {
    undepositedOnly.value = true
  }
  await loadPayments()
})
</script>

<style scoped>
.payments-table__actions {
  width: 8rem;
}

.payments-status--transit {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  color: var(--p-yellow-600);
  font-size: 0.85em;
}
</style>
