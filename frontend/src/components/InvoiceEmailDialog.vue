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
          <label class="app-field__label">{{ t('invoices.email_to') }}</label>
          <InputText :value="recipient" disabled class="w-full" />
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
        <embed
          v-else-if="pdfBlobUrl"
          :src="pdfBlobUrl"
          type="application/pdf"
          class="invoice-email-dialog__embed"
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
        :disabled="loading || !subject.trim() || !body.trim()"
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

const recipient = ref('')
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
    recipient.value = ''
    revokePdfUrl()

    try {
      const preview = await getInvoiceEmailPreviewApi(id)
      subject.value = preview.subject
      body.value = preview.body
      recipient.value = preview.recipient
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
    await sendInvoiceEmailApi(props.invoiceId, { subject: subject.value, body: body.value })
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
