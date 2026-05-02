<template>
  <Dialog
    :visible="visible"
    :header="t('dashboard.invoice_wizard.title')"
    modal
    :closable="true"
    class="app-dialog app-dialog--large"
    @update:visible="onClose"
  >
    <!-- Step 1 — invoice form -->
    <template v-if="step === 1">
      <div v-if="loadingContacts" class="qiw-loading">
        <i class="pi pi-spin pi-spinner" />
        <span>{{ t('dashboard.invoice_wizard.loading') }}</span>
      </div>
      <ClientInvoiceForm
        v-else
        :key="formKey"
        :invoice="null"
        :contacts="contacts"
        @saved="onSaved"
        @cancel="onClose(false)"
      />
    </template>

    <!-- Step 2 — result -->
    <template v-else-if="step === 2">
      <div class="qiw-result">
        <div class="qiw-result__icon qiw-result__icon--success">
          <i class="pi pi-check-circle" />
        </div>
        <p class="qiw-result__title">{{ t('dashboard.invoice_wizard.success_title') }}</p>
        <p class="qiw-result__msg">{{ t('dashboard.invoice_wizard.success_msg', { number: savedInvoiceNumber }) }}</p>
        <p v-if="savedContactName" class="qiw-result__contact">
          {{ t('dashboard.invoice_wizard.success_contact', { contact: savedContactName }) }}
        </p>
        <Tag
          v-if="emailSent"
          :value="t('dashboard.invoice_wizard.email_sent_badge')"
          severity="success"
          icon="pi pi-send"
          class="qiw-result__email-badge"
        />
        <div class="qiw-result__actions">
          <Button
            :label="t('dashboard.invoice_wizard.send_email')"
            icon="pi pi-envelope"
            severity="secondary"
            outlined
            @click="openEmailDialog"
          />
          <Button
            :label="t('dashboard.invoice_wizard.create_another')"
            severity="secondary"
            outlined
            @click="restart"
          />
          <Button :label="t('dashboard.invoice_wizard.close')" @click="onClose(false)" />
        </div>
      </div>
    </template>
  </Dialog>

  <InvoiceEmailDialog
    :invoice-id="emailInvoiceId"
    @sent="onEmailSent"
    @close="emailInvoiceId = null"
  />
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Tag from 'primevue/tag'
import ClientInvoiceForm from './ClientInvoiceForm.vue'
import InvoiceEmailDialog from './InvoiceEmailDialog.vue'
import { listContactsApi, type Contact } from '../api/contacts'
import type { Invoice } from '../api/invoices'
import { formatContactDisplayName } from '../utils/contact'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ (e: 'update:visible', v: boolean): void }>()

const { t } = useI18n()

// ── state ──────────────────────────────────────────────────────────────────
const step = ref<1 | 2>(1)
const loadingContacts = ref(false)
const contacts = ref<Contact[]>([])
const formKey = ref(0)
const savedInvoiceNumber = ref<string | null>(null)
const savedInvoiceId = ref<number | null>(null)
const savedContactName = ref<string | null>(null)
const emailInvoiceId = ref<number | null>(null)
const emailSent = ref(false)

// ── data loading ───────────────────────────────────────────────────────────
async function loadContacts() {
  loadingContacts.value = true
  try {
    contacts.value = (await listContactsApi({ active_only: false })).filter(
      (c) => c.type === 'client' || c.type === 'les_deux',
    )
  } catch {
    contacts.value = []
  } finally {
    loadingContacts.value = false
  }
}

// ── lifecycle ──────────────────────────────────────────────────────────────
watch(
  () => props.visible,
  (val) => {
    if (val) {
      step.value = 1
      formKey.value++
      void loadContacts()
    }
  },
)

// ── actions ────────────────────────────────────────────────────────────────
function onSaved(invoice: Invoice) {
  savedInvoiceNumber.value = invoice.number
  savedInvoiceId.value = invoice.id
  const contact = contacts.value.find((c) => c.id === invoice.contact_id)
  savedContactName.value = contact ? formatContactDisplayName(contact) : null
  emailSent.value = false
  step.value = 2
}

function openEmailDialog() {
  // Reset to null first so the watch in InvoiceEmailDialog fires on re-open
  emailInvoiceId.value = null
  void nextTick(() => {
    emailInvoiceId.value = savedInvoiceId.value
  })
}

function onEmailSent() {
  emailSent.value = true
  emailInvoiceId.value = null
}

function restart() {
  step.value = 1
  formKey.value++
}

function onClose(val: boolean) {
  emit('update:visible', val)
}
</script>

<style scoped>
.qiw-loading {
  display: flex;
  align-items: center;
  gap: var(--app-space-3);
  padding: var(--app-space-5) 0;
  color: var(--p-text-muted-color);
  font-size: 0.95rem;
}

.qiw-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--app-space-6) var(--app-space-4);
  gap: var(--app-space-4);
}

.qiw-result__icon {
  font-size: 3rem;
  line-height: 1;
}

.qiw-result__icon--success {
  color: var(--p-green-500);
}

.qiw-result__title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
}

.qiw-result__msg {
  margin: 0;
  color: var(--p-text-muted-color);
}

.qiw-result__contact {
  margin: 0;
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
}

.qiw-result__email-badge {
  margin-top: var(--app-space-1);
}

.qiw-result__actions {
  display: flex;
  gap: var(--app-space-3);
  margin-top: var(--app-space-2);
  flex-wrap: wrap;
  justify-content: center;
}
</style>
