<template>
  <div class="invoices-view p-4">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-2xl font-semibold">{{ t('invoices.client.title') }}</h2>
      <Button :label="t('invoices.new')" icon="pi pi-plus" @click="openCreateDialog" />
    </div>

    <!-- Filters -->
    <div class="flex gap-3 mb-4 flex-wrap">
      <Select
        v-model="statusFilter"
        :options="statusOptions"
        option-label="label"
        option-value="value"
        :placeholder="t('invoices.filter_status')"
        show-clear
        class="w-48"
        @change="loadInvoices"
      />
      <InputNumber
        v-model="yearFilter"
        :placeholder="t('invoices.filter_year')"
        class="w-28"
        :use-grouping="false"
        @blur="loadInvoices"
      />
    </div>

    <!-- Table -->
    <DataTable
      :value="invoices"
      :loading="loading"
      striped-rows
      paginator
      :rows="20"
      :rows-per-page-options="[10, 20, 50]"
      data-key="id"
    >
      <Column field="number" :header="t('invoices.number')" sortable />
      <Column field="date" :header="t('invoices.date')" sortable />
      <Column field="contact_id" :header="t('invoices.contact')">
        <template #body="{ data }">
          {{ contactName(data.contact_id) }}
        </template>
      </Column>
      <Column field="label" :header="t('invoices.label')">
        <template #body="{ data }">
          <Tag v-if="data.label" :value="t(`invoices.labels.${data.label}`)" severity="info" />
        </template>
      </Column>
      <Column field="total_amount" :header="t('invoices.total')" class="text-right">
        <template #body="{ data }">{{ formatAmount(data.total_amount) }} €</template>
      </Column>
      <Column field="status" :header="t('invoices.status')">
        <template #body="{ data }">
          <Tag
            :value="t(`invoices.statuses.${data.status}`)"
            :severity="statusSeverity(data.status)"
          />
        </template>
      </Column>
      <Column :header="t('common.actions')" style="width: 10rem">
        <template #body="{ data }">
          <div class="flex gap-1">
            <Button
              icon="pi pi-pencil"
              size="small"
              severity="secondary"
              text
              @click="openEditDialog(data)"
            />
            <Button
              icon="pi pi-file-pdf"
              size="small"
              severity="secondary"
              text
              :title="t('invoices.generate_pdf')"
              @click="openPdf(data)"
            />
            <Button
              icon="pi pi-send"
              size="small"
              severity="secondary"
              text
              :title="t('invoices.send_email')"
              @click="sendEmail(data)"
            />
            <Button
              icon="pi pi-copy"
              size="small"
              severity="secondary"
              text
              :title="t('invoices.duplicate')"
              @click="duplicate(data)"
            />
            <Button
              icon="pi pi-trash"
              size="small"
              severity="danger"
              text
              @click="confirmDelete(data)"
            />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Create / Edit Dialog -->
    <Dialog
      v-model:visible="dialogVisible"
      :header="editingInvoice ? t('invoices.edit') : t('invoices.new')"
      modal
      :style="{ width: '640px' }"
    >
      <ClientInvoiceForm
        :invoice="editingInvoice"
        :contacts="contacts"
        @saved="onSaved"
        @cancel="dialogVisible = false"
      />
    </Dialog>

    <ConfirmDialog />
  </div>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import ConfirmDialog from 'primevue/confirmdialog'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { listContactsApi, type Contact } from '../api/contacts'
import {
  deleteInvoiceApi,
  duplicateInvoiceApi,
  getInvoicePdfUrl,
  listInvoicesApi,
  sendInvoiceEmailApi,
  type Invoice,
  type InvoiceStatus,
} from '../api/invoices'
import ClientInvoiceForm from '../components/ClientInvoiceForm.vue'

const { t } = useI18n()
const confirm = useConfirm()
const toast = useToast()

const invoices = ref<Invoice[]>([])
const contacts = ref<Contact[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editingInvoice = ref<Invoice | null>(null)
const statusFilter = ref<InvoiceStatus | null>(null)
const yearFilter = ref<number | null>(new Date().getFullYear())

const statusOptions = [
  { label: t('invoices.statuses.draft'), value: 'draft' },
  { label: t('invoices.statuses.sent'), value: 'sent' },
  { label: t('invoices.statuses.paid'), value: 'paid' },
  { label: t('invoices.statuses.partial'), value: 'partial' },
  { label: t('invoices.statuses.overdue'), value: 'overdue' },
  { label: t('invoices.statuses.disputed'), value: 'disputed' },
]

function formatAmount(val: string) {
  return parseFloat(val).toFixed(2)
}

function contactName(id: number): string {
  const c = contacts.value.find((c) => c.id === id)
  if (!c) return String(id)
  return c.prenom ? `${c.prenom} ${c.nom}` : c.nom
}

function statusSeverity(s: InvoiceStatus): string {
  const map: Record<InvoiceStatus, string> = {
    draft: 'secondary',
    sent: 'info',
    paid: 'success',
    partial: 'warn',
    overdue: 'danger',
    disputed: 'danger',
  }
  return map[s] ?? 'secondary'
}

async function loadInvoices() {
  loading.value = true
  try {
    const filters: Record<string, unknown> = { invoice_type: 'client' }
    if (statusFilter.value) filters.invoice_status = statusFilter.value
    if (yearFilter.value) filters.year = yearFilter.value
    invoices.value = await listInvoicesApi(filters)
  } finally {
    loading.value = false
  }
}

async function loadContacts() {
  contacts.value = await listContactsApi({ limit: 500 })
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
  loadInvoices()
}

function openPdf(invoice: Invoice) {
  window.open(getInvoicePdfUrl(invoice.id), '_blank')
}

async function sendEmail(invoice: Invoice) {
  try {
    await sendInvoiceEmailApi(invoice.id)
    toast.add({ severity: 'success', summary: t('invoices.email_sent'), life: 3000 })
    await loadInvoices()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  }
}

async function duplicate(invoice: Invoice) {
  try {
    await duplicateInvoiceApi(invoice.id)
    toast.add({ severity: 'success', summary: t('invoices.duplicated'), life: 3000 })
    await loadInvoices()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  }
}

function confirmDelete(invoice: Invoice) {
  confirm.require({
    message: t('invoices.confirm_delete', { number: invoice.number }),
    header: t('common.confirm'),
    icon: 'pi pi-exclamation-triangle',
    acceptSeverity: 'danger',
    accept: async () => {
      try {
        await deleteInvoiceApi(invoice.id)
        toast.add({ severity: 'success', summary: t('invoices.deleted'), life: 3000 })
        await loadInvoices()
      } catch {
        toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
      }
    },
  })
}

onMounted(() => {
  loadInvoices()
  loadContacts()
})
</script>
