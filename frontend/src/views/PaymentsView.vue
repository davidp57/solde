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

      <AppTableSkeleton v-if="loading && !payments.length" :rows="8" :cols="5" />
      <DataTable
        v-else
        v-model:filters="tableFilters"
        :value="paymentRows"
        :loading="loading"
        class="app-data-table payments-table"
        filter-display="menu"
        striped-rows
        paginator
        :rows="20"
        :rows-per-page-options="[20, 50, 100, 500]"
        data-key="id"
        size="small"
        row-hover
        :global-filter-fields="[
          'date',
          'amount_value',
          'method',
          'reference_value',
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
              :class="data.deposited ? 'pi pi-check text-green-500' : 'pi pi-times text-red-400'"
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
            <Button
              data-testid="payment-edit-button"
              icon="pi pi-pencil"
              size="small"
              severity="secondary"
              text
              @click="openEditDialog(data)"
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
  </AppPage>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import ToggleButton from 'primevue/togglebutton'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  listPayments,
  updatePayment,
  type Payment,
  type PaymentMethod,
} from '@/api/payments'
import AppPage from '@/components/ui/AppPage.vue'
import AppDateRangeFilter from '@/components/ui/AppDateRangeFilter.vue'
import AppFilterMultiSelect from '@/components/ui/AppFilterMultiSelect.vue'
import AppListState from '@/components/ui/AppListState.vue'
import AppNumberRangeFilter from '@/components/ui/AppNumberRangeFilter.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppPanel from '@/components/ui/AppPanel.vue'
import AppStatCard from '@/components/ui/AppStatCard.vue'
import AppTableSkeleton from '@/components/ui/AppTableSkeleton.vue'
import { useFiscalYearStore } from '@/stores/fiscalYear'
import { formatDisplayDate } from '@/utils/format'
import { collectActiveFilterLabels } from '../composables/activeFilterLabels'
import {
  dateRangeFilter,
  inFilter,
  numericRangeFilter,
  textFilter,
  useDataTableFilters,
} from '../composables/useDataTableFilters'

const { t } = useI18n()
const route = useRoute()
const toast = useToast()
const fiscalYearStore = useFiscalYearStore()

const payments = ref<Payment[]>([])
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
const paymentRows = computed(() =>
  payments.value.map((payment) => ({
    ...payment,
    amount_value: parseFloat(payment.amount),
    method_label: t(`payments.methods.${payment.method}`),
    reference_value: paymentReference(payment),
    deposited_label: payment.deposited ? t('common.yes') : t('common.no'),
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
  cheque_number: textFilter(),
  deposited: inFilter(),
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
    const dateFilter = undepositedOnly.value
      ? {}
      : {
          from_date: fiscalYearStore.selectedFiscalYear?.start_date,
          to_date: fiscalYearStore.selectedFiscalYear?.end_date,
        }
    payments.value = await listPayments({
      invoice_type: 'client',
      undeposited_only: undepositedOnly.value,
      ...dateFilter,
    })
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
  await fiscalYearStore.initialize()
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
</style>
