<template>
  <div class="payments-view p-4">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-2xl font-semibold">{{ t('payments.title') }}</h2>
    </div>

    <!-- Filters -->
    <div class="flex gap-3 mb-4 flex-wrap">
      <ToggleButton
        v-model="undepositedOnly"
        :on-label="t('payments.filter_undeposited')"
        :off-label="t('payments.filter_undeposited')"
        @change="loadPayments"
      />
    </div>

    <!-- Table -->
    <DataTable
      :value="payments"
      :loading="loading"
      striped-rows
      paginator
      :rows="20"
      data-key="id"
    >
      <Column field="date" :header="t('payments.date')" sortable />
      <Column field="amount" :header="t('payments.amount')">
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
      <Column :header="t('common.actions')" style="width: 6rem">
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
    </DataTable>

    <ConfirmDialog />
  </div>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import ConfirmDialog from 'primevue/confirmdialog'
import DataTable from 'primevue/datatable'
import Tag from 'primevue/tag'
import ToggleButton from 'primevue/togglebutton'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { deletePayment, listPayments, type Payment } from '@/api/payments'

const { t } = useI18n()
const confirm = useConfirm()
const toast = useToast()

const payments = ref<Payment[]>([])
const loading = ref(false)
const undepositedOnly = ref(false)

function formatAmount(value: string): string {
  return `${parseFloat(value).toFixed(2)} €`
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
    acceptSeverity: 'danger',
    accept: async () => {
      await deletePayment(payment.id)
      toast.add({ severity: 'success', summary: t('payments.deleted'), life: 2000 })
      await loadPayments()
    },
  })
}

onMounted(loadPayments)
</script>
