<template>
  <AppPage>
    <AppPageHeader
      :eyebrow="t('ui.page.collection_eyebrow')"
      :title="t('payments.title')"
      :subtitle="t('payments.subtitle')"
    />

    <section class="app-stat-grid">
      <AppStatCard :label="t('payments.metrics.visible')" :value="filtered.length" :caption="t('payments.metrics.total', { count: payments.length })" />
      <AppStatCard :label="t('payments.metrics.amount')" :value="formatAmount(totalAmount)" :caption="t('payments.metrics.average', { amount: formatAmount(averageAmount) })" />
      <AppStatCard :label="t('payments.metrics.undeposited')" :value="undepositedCount" :caption="t('payments.metrics.cheques', { count: chequeCount })" tone="warn" />
    </section>

    <AppPanel :title="t('payments.workspace_title')" :subtitle="t('payments.workspace_subtitle')">
      <div class="app-toolbar">
        <div class="app-toolbar__meta">
          <p class="app-toolbar__hint">{{ t('payments.filters_hint') }}</p>
          <span class="app-chip">{{ t('payments.results_label', { count: filtered.length }) }}</span>
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
        data-key="id"
        size="small"
        row-hover
      >
      <Column field="date" :header="t('payments.date')" sortable />
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
      <Column field="cheque_number" :header="t('payments.cheque_number')" />
      <Column field="deposited" :header="t('payments.deposited')">
        <template #body="{ data }">
          <i :class="data.deposited ? 'pi pi-check text-green-500' : 'pi pi-times text-red-400'" />
        </template>
      </Column>
      <Column :header="t('common.actions')" class="payments-table__actions">
        <template #body="{ data }">
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
  </AppPage>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import ConfirmDialog from 'primevue/confirmdialog'
import DataTable from 'primevue/datatable'
import InputText from 'primevue/inputtext'
import Tag from 'primevue/tag'
import ToggleButton from 'primevue/togglebutton'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { deletePayment, listPayments, type Payment } from '@/api/payments'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppPanel from '@/components/ui/AppPanel.vue'
import AppStatCard from '@/components/ui/AppStatCard.vue'
import { useTableFilter } from '../composables/useTableFilter'

const { t } = useI18n()
const confirm = useConfirm()
const toast = useToast()

const payments = ref<Payment[]>([])
const { filterText, filtered } = useTableFilter(payments)
const loading = ref(false)
const undepositedOnly = ref(false)
const totalAmount = computed(() => filtered.value.reduce((sum, payment) => sum + parseFloat(payment.amount), 0))
const averageAmount = computed(() => filtered.value.length ? totalAmount.value / filtered.value.length : 0)
const undepositedCount = computed(() => filtered.value.filter((payment) => !payment.deposited).length)
const chequeCount = computed(() => filtered.value.filter((payment) => payment.method === 'cheque').length)

function formatAmount(value: string | number): string {
  return `${parseFloat(String(value)).toFixed(2)} €`
}

async function loadPayments() {
  loading.value = true
  try {
    payments.value = await listPayments({ undeposited_only: undepositedOnly.value })
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

onMounted(loadPayments)
</script>

<style scoped>
.payments-table__actions {
  width: 6rem;
}
</style>
