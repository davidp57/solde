<template>
  <Dialog
    :visible="visible"
    :header="invoice ? t('invoices.record_payment') : ''"
    modal
    class="app-dialog app-dialog--medium"
    @update:visible="(value: boolean) => emit('update:visible', value)"
  >
    <form class="app-dialog-form" @submit.prevent="submitPayment">
      <section v-if="invoice" class="app-dialog-intro">
        <p class="app-dialog-intro__eyebrow">{{ invoice.number }}</p>
        <p v-if="introSubtitle" class="app-dialog-intro__text">{{ introSubtitle }}</p>
        <p class="app-dialog-intro__text">
          {{ t('invoices.total') }} : <strong>{{ formatCurrency(invoice.total_amount) }}</strong>
          <template v-if="invoice.due_date">
            &nbsp;·&nbsp; {{ t('invoices.due_date') }} : {{ formatDisplayDate(invoice.due_date) }}
          </template>
        </p>
      </section>
      <section class="app-dialog-section">
        <div class="invoice-payment-dialog__summary">
          <div class="invoice-payment-dialog__metric">
            <div class="invoice-payment-dialog__label">{{ t('invoices.remaining') }}</div>
            <div class="invoice-payment-dialog__value">{{ formatCurrency(paymentRemaining) }}</div>
          </div>
        </div>
        <div class="app-form-grid">
          <div class="app-field">
            <label class="app-field__label">{{ t('payments.date') }}</label>
            <AppDatePicker v-model="form.date" />
            <AppFiscalYearDateWarning :date="form.date" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('payments.amount') }}</label>
            <InputNumber
              v-model="form.amount"
              mode="decimal"
              :min="0.01"
              :min-fraction-digits="2"
              :max-fraction-digits="2"
            />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('payments.method') }}</label>
            <Select
              v-model="form.method"
              :options="paymentMethodOptions"
              option-label="label"
              option-value="value"
            />
          </div>
          <div v-if="form.method === 'cheque'" class="app-field">
            <label class="app-field__label">{{ t('payments.cheque_number') }}</label>
            <InputText v-model="form.cheque_number" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('payments.reference') }}</label>
            <InputText v-model="form.reference" />
          </div>
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('payments.notes') }}</label>
            <Textarea v-model="form.notes" rows="3" />
          </div>
        </div>
      </section>
      <div class="app-form-actions">
        <Button
          :label="t('common.cancel')"
          severity="secondary"
          text
          type="button"
          @click="emit('update:visible', false)"
        />
        <Button type="submit" :label="t('common.save')" :loading="saving" />
      </div>
    </form>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import { useToast } from 'primevue/usetoast'
import AppDatePicker from '../ui/AppDatePicker.vue'
import AppFiscalYearDateWarning from '../ui/AppFiscalYearDateWarning.vue'
import { createPayment, suggestChequeNumber } from '../../api/payments'
import type { Invoice } from '../../api/invoices'
import { remainingForInvoice } from '../../composables/useInvoiceMetrics'
import { formatCurrency, formatDisplayDate } from '@/utils/format'

const props = defineProps<{
  visible: boolean
  invoice: Invoice | null
  /** Optional contact name shown in the dialog intro. */
  contactName?: string
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  paid: [invoiceId: number]
}>()

const { t } = useI18n()
const toast = useToast()

const paymentMethodOptions = [
  { label: t('payments.methods.especes'), value: 'especes' },
  { label: t('payments.methods.cheque'), value: 'cheque' },
]

const saving = ref(false)
const form = ref({
  date: new Date() as Date,
  amount: 0,
  method: 'cheque' as 'especes' | 'cheque',
  cheque_number: '',
  reference: '',
  notes: '',
})

const paymentRemaining = computed(() =>
  props.invoice ? remainingForInvoice(props.invoice) : 0,
)

const introSubtitle = computed(() => {
  const parts: string[] = []
  if (props.contactName) parts.push(props.contactName)
  if (props.invoice?.description) parts.push(props.invoice.description)
  return parts.join(' — ')
})

function applyChequeSuggestion(): void {
  void suggestChequeNumber().then((n) => {
    if (form.value.method === 'cheque' && !form.value.cheque_number) {
      form.value.cheque_number = n
    }
  })
}

// Initialise the form when the dialog opens, mirroring the previous openPaymentDialog().
watch(
  () => props.visible,
  (visible) => {
    if (!visible || !props.invoice) return
    form.value = {
      date: new Date(),
      amount: remainingForInvoice(props.invoice),
      method: 'cheque',
      cheque_number: '',
      reference: '',
      notes: '',
    }
    applyChequeSuggestion()
  },
)

watch(
  () => form.value.method,
  (method) => {
    if (props.visible && method === 'cheque' && !form.value.cheque_number) {
      applyChequeSuggestion()
    }
  },
)

function toIsoDate(value: Date | string): string {
  return typeof value === 'string' ? value : value.toISOString().slice(0, 10)
}

async function submitPayment(): Promise<void> {
  if (!props.invoice) return

  const amount = Number(form.value.amount)
  if (!(amount > 0)) {
    toast.add({ severity: 'warn', summary: t('payments.errors.amount_positive'), life: 3500 })
    return
  }
  if (amount - paymentRemaining.value > 0.001) {
    toast.add({
      severity: 'warn',
      summary: t('payments.errors.amount_exceeds_remaining'),
      life: 3500,
    })
    return
  }
  if (form.value.method === 'cheque' && form.value.cheque_number.trim().length === 0) {
    toast.add({ severity: 'warn', summary: t('payments.errors.cheque_number_required'), life: 3500 })
    return
  }

  const invoiceId = props.invoice.id
  saving.value = true
  try {
    await createPayment({
      invoice_id: invoiceId,
      contact_id: props.invoice.contact_id,
      amount: amount.toFixed(2),
      date: toIsoDate(form.value.date),
      method: form.value.method,
      cheque_number:
        form.value.method === 'cheque' ? form.value.cheque_number.trim() || null : null,
      reference: form.value.reference.trim() || null,
      notes: form.value.notes.trim() || null,
    })
    toast.add({ severity: 'success', summary: t('payments.created'), life: 3000 })
    emit('update:visible', false)
    emit('paid', invoiceId)
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.invoice-payment-dialog__summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--app-space-3);
  padding-bottom: var(--app-space-4);
  border-bottom: 1px solid var(--app-surface-border);
}

.invoice-payment-dialog__metric {
  padding: var(--app-space-3);
  border-radius: var(--app-surface-radius-sm);
  background: color-mix(in srgb, var(--app-surface-bg) 85%, transparent 15%);
}

.invoice-payment-dialog__label {
  color: var(--p-text-muted-color);
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.invoice-payment-dialog__value {
  margin-top: var(--app-space-2);
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--p-orange-500);
}

@media (max-width: 767px) {
  .invoice-payment-dialog__summary {
    grid-template-columns: 1fr;
  }
}
</style>
