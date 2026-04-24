<template>
  <Dialog
    :visible="visible"
    :header="t('bank.link_supplier_payment_title')"
    modal
    class="app-dialog app-dialog--medium"
    @update:visible="$emit('update:visible', $event)"
  >
    <div class="app-dialog-form bank-form">
      <section class="app-dialog-intro">
        <p class="app-dialog-intro__eyebrow">{{ t('bank.link_supplier_payment') }}</p>
        <p class="app-dialog-intro__text">{{ t('bank.link_supplier_payment_intro') }}</p>
      </section>
      <section class="app-dialog-section">
        <p v-if="transaction" class="app-dialog-note">
          {{
            t('bank.create_client_payment_tx_summary', {
              date: formatDisplayDate(transaction.date),
              amount: formatAmount(transaction.amount),
              description: transaction.description || transaction.reference || '-',
            })
          }}
        </p>
        <div class="app-field">
          <label class="app-field__label">{{ t('bank.link_supplier_payment_payment') }}</label>
          <Select
            v-model="selectedPaymentId"
            :options="paymentOptions"
            option-label="label"
            option-value="value"
            :loading="loading"
            :placeholder="loading ? t('common.loading') : t('bank.link_supplier_payment_payment')"
            filter
            show-clear
          />
        </div>
        <Message v-if="!loading && paymentOptions.length === 0" severity="warn">
          {{ t('bank.link_supplier_payment_no_payment') }}
        </Message>
        <Message v-else-if="!loading && selectedPaymentId !== null" severity="info">
          {{ t('bank.suggested_candidate_hint') }}
        </Message>
      </section>
      <div class="app-form-actions">
        <Button
          :label="t('common.cancel')"
          severity="secondary"
          text
          @click="$emit('update:visible', false)"
        />
        <Button
          :label="t('common.confirm')"
          :loading="saving"
          :disabled="selectedPaymentId === null || loading"
          @click="submit"
        />
      </div>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Message from 'primevue/message'
import Select from 'primevue/select'
import { useToast } from 'primevue/usetoast'
import { listContactsApi, type Contact } from '@/api/contacts'
import { linkSupplierPaymentToTransaction, type BankTransaction } from '@/api/bank'
import { listPayments, type Payment } from '@/api/payments'
import { scorePaymentSuggestion } from '@/utils/bankReconciliation'
import { formatContactDisplayName } from '@/utils/contact'
import { formatDisplayDate } from '@/utils/format'

const props = defineProps<{
  visible: boolean
  transaction: BankTransaction | null
}>()
const emit = defineEmits<{
  'update:visible': [val: boolean]
  saved: []
}>()

const { t } = useI18n()
const toast = useToast()

const loading = ref(false)
const saving = ref(false)
const payments = ref<Payment[]>([])
const contacts = ref<Contact[]>([])
const selectedPaymentId = ref<number | null>(null)

const txAmount = computed(() =>
  props.transaction ? Math.abs(parseFloat(props.transaction.amount)) : 0,
)

function formatAmount(value: string | number): string {
  return `${parseFloat(String(value)).toFixed(2)} €`
}

function contactName(contactId: number): string {
  const c = contacts.value.find((x) => x.id === contactId)
  return c ? formatContactDisplayName(c) : `#${contactId}`
}

const paymentOptions = computed(() => {
  const amount = txAmount.value
  return payments.value
    .filter(
      (p) =>
        p.method === 'virement' && Math.abs(parseFloat(p.amount) - amount) < 0.0001,
    )
    .sort((a, b) => {
      const scoreA = scorePaymentSuggestion({
        transactionAmount: amount,
        transactionDate: props.transaction?.date ?? '',
        transactionDescription: props.transaction?.description ?? '',
        transactionReference: props.transaction?.reference,
        candidateInvoiceNumber: a.invoice_number,
        candidateReference: a.reference,
        candidateContactName: contactName(a.contact_id),
        candidateDate: a.date,
        candidateAmount: parseFloat(a.amount),
      })
      const scoreB = scorePaymentSuggestion({
        transactionAmount: amount,
        transactionDate: props.transaction?.date ?? '',
        transactionDescription: props.transaction?.description ?? '',
        transactionReference: props.transaction?.reference,
        candidateInvoiceNumber: b.invoice_number,
        candidateReference: b.reference,
        candidateContactName: contactName(b.contact_id),
        candidateDate: b.date,
        candidateAmount: parseFloat(b.amount),
      })
      if (scoreA !== scoreB) return scoreB - scoreA
      return b.date.localeCompare(a.date)
    })
    .map((p) => {
      const ref = p.reference ? ` · ${p.reference}` : ''
      return {
        label: `${p.invoice_number || `#${p.invoice_id}`} · ${contactName(p.contact_id)} · ${formatAmount(p.amount)} · ${formatDisplayDate(p.date)}${ref}`,
        value: p.id,
      }
    })
})

watch(
  () => props.visible,
  async (isVisible) => {
    if (!isVisible || !props.transaction) return
    selectedPaymentId.value = null
    loading.value = true
    try {
      const [pmts, conts] = await Promise.all([
        listPayments({ invoice_type: 'fournisseur' }),
        listContactsApi({ active_only: true }),
      ])
      payments.value = pmts
      contacts.value = conts
      selectedPaymentId.value = paymentOptions.value[0]?.value ?? null
    } catch (error) {
      const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
      toast.add({
        severity: 'error',
        summary: typeof detail === 'string' ? detail : t('common.error.unknown'),
        life: 3000,
      })
    } finally {
      loading.value = false
    }
  },
)

async function submit(): Promise<void> {
  if (!props.transaction || selectedPaymentId.value === null) return
  saving.value = true
  try {
    await linkSupplierPaymentToTransaction(props.transaction.id, selectedPaymentId.value)
    emit('update:visible', false)
    toast.add({ severity: 'success', summary: t('bank.link_supplier_payment_success'), life: 3000 })
    emit('saved')
  } catch (error) {
    const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
    toast.add({
      severity: 'error',
      summary: typeof detail === 'string' ? detail : t('common.error.unknown'),
      life: 3000,
    })
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.bank-form {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}
</style>
