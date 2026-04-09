<template>
  <div class="contact-detail-view p-4">
    <div class="flex items-center gap-3 mb-6">
      <Button icon="pi pi-arrow-left" severity="secondary" text @click="$router.back()" />
      <h2 class="text-2xl font-semibold">{{ t('contact_history.title') }}</h2>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <ProgressSpinner />
    </div>

    <template v-else-if="history">
      <!-- Contact info card -->
      <Card class="mb-6">
        <template #content>
          <div class="flex items-start justify-between">
            <div class="flex flex-col gap-1">
              <div class="text-xl font-semibold">
                {{ history.contact.nom }} {{ history.contact.prenom }}
              </div>
              <div class="text-sm text-gray-500">{{ history.contact.email }}</div>
              <div class="text-sm text-gray-500">{{ history.contact.telephone }}</div>
            </div>
            <div class="flex flex-col items-end gap-2">
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
          </div>

          <!-- KPI strip -->
          <div class="grid grid-cols-3 gap-4 mt-5 pt-4 border-t">
            <div class="text-center">
              <div class="text-xs text-gray-500 uppercase mb-1">{{ t('contact_history.total_invoiced') }}</div>
              <div class="text-lg font-semibold">{{ fmt(history.total_invoiced) }} €</div>
            </div>
            <div class="text-center">
              <div class="text-xs text-gray-500 uppercase mb-1">{{ t('contact_history.total_paid') }}</div>
              <div class="text-lg font-semibold text-green-600">{{ fmt(history.total_paid) }} €</div>
            </div>
            <div class="text-center">
              <div class="text-xs text-gray-500 uppercase mb-1">{{ t('contact_history.total_due') }}</div>
              <div :class="['text-lg font-semibold', Number(history.total_due) > 0 ? 'text-red-600' : 'text-gray-700']">
                {{ fmt(history.total_due) }} €
              </div>
            </div>
          </div>
        </template>
      </Card>

      <!-- Invoices -->
      <Card class="mb-6">
        <template #header>
          <div class="px-4 pt-4 font-semibold">{{ t('contact_history.invoices_section') }}</div>
        </template>
        <template #content>
          <DataTable
            v-if="history.invoices.length"
            :value="history.invoices"
            class="text-sm"
            striped-rows
          >
            <Column field="number" :header="t('invoices.number')" style="width:10rem" />
            <Column field="date" :header="t('invoices.date')" style="width:8rem" />
            <Column field="status" :header="t('invoices.status')">
              <template #body="{ data }">
                <Tag :value="t(`invoices.statuses.${data.status}`)" :severity="statusSeverity(data.status)" />
              </template>
            </Column>
            <Column field="total_amount" :header="t('invoices.total')" class="text-right font-mono">
              <template #body="{ data }">{{ fmt(data.total_amount) }} €</template>
            </Column>
            <Column field="balance_due" :header="t('contact_history.total_due')" class="text-right font-mono">
              <template #body="{ data }">
                <span :class="Number(data.balance_due) > 0 ? 'text-red-600' : ''">
                  {{ fmt(data.balance_due) }} €
                </span>
              </template>
            </Column>
          </DataTable>
          <div v-else class="text-gray-400 text-sm py-2">{{ t('contact_history.no_invoices') }}</div>
        </template>
      </Card>

      <!-- Payments -->
      <Card>
        <template #header>
          <div class="px-4 pt-4 font-semibold">{{ t('contact_history.payments_section') }}</div>
        </template>
        <template #content>
          <DataTable
            v-if="history.payments.length"
            :value="history.payments"
            class="text-sm"
            striped-rows
          >
            <Column field="date" :header="t('payments.date')" style="width:8rem" />
            <Column field="invoice_number" :header="t('payments.invoice')" style="width:10rem" />
            <Column field="method" :header="t('payments.method')">
              <template #body="{ data }">{{ t(`payments.methods.${data.method}`) }}</template>
            </Column>
            <Column field="amount" :header="t('payments.amount')" class="text-right font-mono">
              <template #body="{ data }">{{ fmt(data.amount) }} €</template>
            </Column>
          </DataTable>
          <div v-else class="text-gray-400 text-sm py-2">{{ t('contact_history.no_payments') }}</div>
        </template>
      </Card>
    </template>

    <div v-else class="text-gray-400 text-center mt-12">
      {{ t('common.error.notFound') }}
    </div>

    <!-- Confirm dialog -->
    <ConfirmDialog />
    <Toast />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { getContactHistoryApi, markCreanceDouteuse } from '../api/accounting'
import type { ContactHistory } from '../api/accounting'

const { t } = useI18n()
const route = useRoute()
const confirm = useConfirm()
const toast = useToast()

const history = ref<ContactHistory | null>(null)
const loading = ref(false)

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
