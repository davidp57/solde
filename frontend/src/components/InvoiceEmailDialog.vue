<template>
  <Dialog
    v-model:visible="visible"
    :header="t('invoices.email_dialog_title')"
    modal
    class="app-dialog app-dialog--large"
    :style="{ width: 'min(95vw, 1180px)' }"
    @hide="onHide"
  >
    <div v-if="loading" class="invoice-email-dialog__loading">
      <Skeleton height="2rem" border-radius="4px" class="mb-2" />
      <Skeleton height="2rem" border-radius="4px" class="mb-2" />
      <Skeleton height="8rem" border-radius="4px" />
    </div>

    <div v-else class="invoice-email-dialog__layout">
      <!-- Form column -->
      <div class="invoice-email-dialog__form">
        <div class="app-field">
          <label class="app-field__label">{{ t('invoices.email_recipients') }}</label>
          <!-- Single recipient: read-only field -->
          <InputText v-if="recipients.length <= 1" :value="recipients[0] ?? ''" disabled class="w-full" />
          <!-- Multiple recipients: checkboxes -->
          <div v-else class="invoice-email-dialog__recipients">
            <div
              v-for="addr in recipients"
              :key="addr"
              class="invoice-email-dialog__recipient-row"
            >
              <Checkbox
                v-model="selectedRecipients"
                :input-id="`recipient-${addr}`"
                :value="addr"
              />
              <label :for="`recipient-${addr}`">{{ addr }}</label>
            </div>
            <small v-if="selectedRecipients.length === 0" class="p-error">
              {{ t('invoices.email_select_recipients') }}
            </small>
          </div>
        </div>
        <div class="app-field">
          <label for="email-subject" class="app-field__label">{{ t('invoices.email_subject') }}</label>
          <InputText
            id="email-subject"
            v-model="subject"
            class="w-full"
            :placeholder="t('invoices.email_subject')"
          />
        </div>
        <div class="app-field">
          <label for="email-body" class="app-field__label">{{ t('invoices.email_body') }}</label>
          <Textarea
            id="email-body"
            v-model="body"
            class="w-full"
            rows="9"
            auto-resize
            :placeholder="t('invoices.email_body')"
          />
        </div>
      </div>

      <!-- PDF preview column -->
      <div class="invoice-email-dialog__preview">
        <p class="invoice-email-dialog__preview-label">{{ t('invoices.email_preview') }}</p>
        <Skeleton v-if="pdfLoading" class="invoice-email-dialog__embed" border-radius="4px" />
        <object
          v-else-if="pdfBlobUrl"
          :data="pdfBlobUrl"
          type="application/pdf"
          class="invoice-email-dialog__embed"
          :aria-label="t('invoices.email_preview_title')"
        />
        <div v-else class="invoice-email-dialog__preview-empty">
          <i class="pi pi-file-pdf" />
          <span>{{ t('invoices.email_preview_unavailable') }}</span>
        </div>
      </div>
    </div>

    <template #footer>
      <Button
        :label="t('common.cancel')"
        severity="secondary"
        outlined
        :disabled="sending"
        @click="visible = false"
      />
      <Button
        :label="t('invoices.email_send')"
        icon="pi pi-send"
        :loading="sending"
        :disabled="loading || !subject.trim() || !body.trim() || selectedRecipients.length === 0"
        @click="send"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Skeleton from 'primevue/skeleton'
import Textarea from 'primevue/textarea'
import {
  downloadInvoicePdfApi,
  getInvoiceEmailPreviewApi,
  sendInvoiceEmailApi,
} from '@/api/invoices'

const props = defineProps<{ invoiceId: number | null }>()
const emit = defineEmits<{
  sent: []
  close: []
}>()

const visible = ref(false)
const loading = ref(false)
const pdfLoading = ref(false)
const sending = ref(false)

const recipients = ref<string[]>([])
const selectedRecipients = ref<string[]>([])
const subject = ref('')
const body = ref('')
const pdfBlobUrl = ref<string | null>(null)

const toast = useToast()
const { t } = useI18n()

watch(
  () => props.invoiceId,
  async (id) => {
    if (id === null) return
    visible.value = true
    loading.value = true
    subject.value = ''
    body.value = ''
    recipients.value = []
    selectedRecipients.value = []
    revokePdfUrl()

    try {
      const preview = await getInvoiceEmailPreviewApi(id)
      subject.value = preview.subject
      body.value = preview.body
      recipients.value = preview.recipients
      selectedRecipients.value = [...preview.recipients]
    } catch {
      toast.add({ severity: 'error', summary: t('common.error.title'), life: 4000 })
      visible.value = false
    } finally {
      loading.value = false
    }

    // Load PDF preview in parallel (non-blocking)
    pdfLoading.value = true
    downloadInvoicePdfApi(id)
      .then((blob) => {
        pdfBlobUrl.value = URL.createObjectURL(blob)
      })
      .catch(() => {
        // PDF preview failure is non-critical, just skip it
      })
      .finally(() => {
        pdfLoading.value = false
      })
  },
)

watch(visible, (v) => {
  if (!v) emit('close')
})

async function send(): Promise<void> {
  if (props.invoiceId === null) return
  sending.value = true
  try {
    await sendInvoiceEmailApi(props.invoiceId, {
      subject: subject.value,
      body: body.value,
      recipients: selectedRecipients.value,
    })
    toast.add({ severity: 'success', summary: t('invoices.email_sent'), life: 3000 })
    visible.value = false
    emit('sent')
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.title'), life: 4000 })
  } finally {
    sending.value = false
  }
}

function revokePdfUrl(): void {
  if (pdfBlobUrl.value) {
    URL.revokeObjectURL(pdfBlobUrl.value)
    pdfBlobUrl.value = null
  }
}

function onHide(): void {
  revokePdfUrl()
}
</script>

<style scoped>
.invoice-email-dialog__loading {
  padding: 0.5rem 0;
}

.invoice-email-dialog__layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  align-items: stretch;
  min-height: 480px;
}

@media (max-width: 700px) {
  .invoice-email-dialog__layout {
    grid-template-columns: 1fr;
  }
}

.invoice-email-dialog__form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.invoice-email-dialog__recipients {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.invoice-email-dialog__recipient-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.invoice-email-dialog__preview {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-height: 480px;
}

.invoice-email-dialog__preview-label {
  font-size: 0.85rem;
  color: var(--p-text-muted-color, #6c757d);
  margin: 0;
  flex-shrink: 0;
}

.invoice-email-dialog__embed {
  width: 100%;
  flex: 1;
  min-height: 440px;
  border: 1px solid var(--p-content-border-color, #dee2e6);
  border-radius: 4px;
  display: block;
}

.invoice-email-dialog__preview-empty {
  flex: 1;
  min-height: 440px;
  border: 1px solid var(--p-content-border-color, #dee2e6);
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  color: var(--p-text-muted-color, #6c757d);
  font-size: 0.9rem;
}

.invoice-email-dialog__preview-empty .pi {
  font-size: 2.5rem;
  opacity: 0.4;
}
</style>
