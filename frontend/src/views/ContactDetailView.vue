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
        <DataTable
          v-if="history.invoices.length"
          :value="history.invoices"
          class="app-data-table"
          striped-rows
          paginator
          :rows="20"
          :rows-per-page-options="[20, 50, 100, 500]"
          size="small"
          row-hover
        >
          <Column field="number" :header="t('invoices.number')" style="width: 10rem" />
          <Column field="date" :header="t('invoices.date')" style="width: 8rem">
            <template #body="{ data }">{{ formatDisplayDate(data.date) }}</template>
          </Column>
          <Column field="status" :header="t('invoices.status')">
            <template #body="{ data }">
              <Tag
                :value="t(`invoices.statuses.${data.status}`)"
                :severity="statusSeverity(data.status)"
              />
            </template>
          </Column>
          <Column field="total_amount" :header="t('invoices.total')" class="app-money">
            <template #body="{ data }">{{ fmt(data.total_amount) }} €</template>
          </Column>
          <Column field="balance_due" :header="t('contact_history.total_due')" class="app-money">
            <template #body="{ data }">
              <span :class="Number(data.balance_due) > 0 ? 'contact-detail-due' : ''">
                {{ fmt(data.balance_due) }} €
              </span>
            </template>
          </Column>
        </DataTable>
        <div v-else class="app-empty-state">{{ t('contact_history.no_invoices') }}</div>
      </AppPanel>

      <AppPanel :title="t('contact_history.payments_section')" dense>
        <DataTable
          v-if="history.payments.length"
          :value="history.payments"
          class="app-data-table"
          striped-rows
          paginator
          :rows="20"
          :rows-per-page-options="[20, 50, 100, 500]"
          size="small"
          row-hover
        >
          <Column field="date" :header="t('payments.date')" style="width: 8rem">
            <template #body="{ data }">{{ formatDisplayDate(data.date) }}</template>
          </Column>
          <Column field="invoice_number" :header="t('payments.invoice')" style="width: 10rem" />
          <Column field="method" :header="t('payments.method')">
            <template #body="{ data }">{{ t(`payments.methods.${data.method}`) }}</template>
          </Column>
          <Column field="amount" :header="t('payments.amount')" class="app-money">
            <template #body="{ data }">{{ fmt(data.amount) }} €</template>
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
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import ConfirmDialog from 'primevue/confirmdialog'
import DataTable from 'primevue/datatable'
import ProgressSpinner from 'primevue/progressspinner'
import Tag from 'primevue/tag'
import Toast from 'primevue/toast'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import AppStatCard from '../components/ui/AppStatCard.vue'
import { getContactHistoryApi, markCreanceDouteuse } from '../api/accounting'
import type { ContactHistory } from '../api/accounting'
import { formatDisplayDate } from '@/utils/format'

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
