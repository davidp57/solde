<template>
  <AppPage width="wide">
    <AppPageHeader :eyebrow="t('ui.page.collection_eyebrow')" :title="t('contact_history.title')">
      <template #actions>
        <Button icon="pi pi-arrow-left" severity="secondary" text @click="$router.back()" />
      </template>
    </AppPageHeader>

    <div v-if="loading" class="contact-detail-loading">
      <ProgressSpinner />
    </div>

    <template v-else-if="history">
      <AppPanel
        :title="contactFullName(history.contact)"
        :subtitle="contactSubtitle(history.contact)"
      >
        <template #actions>
          <div class="contact-detail-actions">
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

        <div class="contact-detail-meta">
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
            <template #filter="{ filterModel }">
              <AppFilterMultiSelect
                v-model="filterModel.value"
                :options="invoiceStatusOptions"
                option-label="label"
                option-value="value"
                :placeholder="t('common.all')"
                display="chip"
                show-clear
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
              <span :class="Number(data.balance_due) > 0 ? 'contact-detail-due' : ''">
                {{ fmt(data.balance_due) }} €
              </span>
            </template>
            <template #filter="{ filterModel }">
              <AppNumberRangeFilter v-model="filterModel.value" />
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
        </DataTable>
        <div v-else class="app-empty-state">{{ t('contact_history.no_payments') }}</div>
      </AppPanel>
    </template>

    <div v-else class="app-empty-state">
      {{ t('common.error.notFound') }}
    </div>

    <ConfirmDialog />
    <Toast />
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import ConfirmDialog from 'primevue/confirmdialog'
import DataTable from 'primevue/datatable'
import InputText from 'primevue/inputtext'
import ProgressSpinner from 'primevue/progressspinner'
import Tag from 'primevue/tag'
import Toast from 'primevue/toast'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import AppDateRangeFilter from '../components/ui/AppDateRangeFilter.vue'
import AppFilterMultiSelect from '../components/ui/AppFilterMultiSelect.vue'
import AppNumberRangeFilter from '../components/ui/AppNumberRangeFilter.vue'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import AppStatCard from '../components/ui/AppStatCard.vue'
import { getContactHistoryApi, markCreanceDouteuse } from '../api/accounting'
import type { ContactHistory } from '../api/accounting'
import {
  dateRangeFilter,
  inFilter,
  numericRangeFilter,
  textFilter,
  useDataTableFilters,
} from '../composables/useDataTableFilters'
import { formatDisplayDate } from '@/utils/format'

const { t } = useI18n()
const route = useRoute()
const confirm = useConfirm()
const toast = useToast()

const history = ref<ContactHistory | null>(null)
const loading = ref(false)
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
const { filters: invoiceTableFilters, resetFilters: resetInvoiceFilters, hasActiveFilters: hasActiveInvoiceFilters } = useDataTableFilters(invoiceRows, {
  global: textFilter(''),
  number: textFilter(),
  date: dateRangeFilter(),
  status: inFilter(),
  total_amount_value: numericRangeFilter(),
  balance_due_value: numericRangeFilter(),
})
const { filters: paymentTableFilters, resetFilters: resetPaymentFilters, hasActiveFilters: hasActivePaymentFilters } = useDataTableFilters(paymentRows, {
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

function confirmMarkDouteux() {
  const amount = history.value ? fmt(history.value.total_due) : ''
  confirm.require({
    message: t('contact_history.mark_douteux_confirm', { amount }),
    header: t('contact_history.mark_douteux'),
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: t('common.cancel'), severity: 'secondary', outlined: true },
    acceptProps: { label: t('common.confirm'), severity: 'warn' },
    accept: async () => {
      const id = Number(route.params.id)
      try {
        const res = await markCreanceDouteuse(id)
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
        toast.add({
          severity: 'error',
          summary: t('common.error.unknown'),
          life: 4000,
        })
      }
    },
  })
}

async function loadHistory() {
  loading.value = true
  try {
    const id = Number(route.params.id)
    history.value = await getContactHistoryApi(id)
  } finally {
    loading.value = false
  }
}

onMounted(loadHistory)
</script>

<style scoped>
.contact-detail-loading {
  display: flex;
  justify-content: center;
  padding: 4rem 0;
}

.contact-detail-actions {
  display: flex;
  align-items: center;
  gap: var(--app-space-3);
  flex-wrap: wrap;
}

.contact-detail-meta {
  display: flex;
  gap: var(--app-space-4);
  flex-wrap: wrap;
  margin-bottom: var(--app-space-4);
  color: var(--p-text-muted-color);
  font-size: 0.95rem;
}

.contact-detail-due {
  color: var(--p-red-600);
}
</style>
