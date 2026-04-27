<template>
  <Dialog
    :visible="visible"
    :header="t('bank.create_supplier_payment_title')"
    modal
    class="app-dialog app-dialog--medium"
    @update:visible="$emit('update:visible', $event)"
  >
    <div class="app-dialog-form bank-form">
      <section class="app-dialog-intro">
        <p class="app-dialog-intro__eyebrow">{{ t('bank.create_supplier_payment') }}</p>
        <p class="app-dialog-intro__text">{{ t('bank.create_supplier_payment_intro') }}</p>
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
          <label class="app-field__label">{{ t('bank.create_supplier_payment_invoice') }}</label>
          <Select
            v-model="selectedInvoiceId"
            :options="invoiceOptions"
            option-label="label"
            option-value="value"
            :loading="loading"
            :placeholder="loading ? t('common.loading') : t('bank.create_supplier_payment_invoice')"
            filter
            show-clear
          />
        </div>
        <Message v-if="!loading && invoiceOptions.length === 0" severity="warn">
          {{ t('bank.create_supplier_payment_no_invoice') }}
        </Message>
        <Message v-else-if="!loading && selectedInvoiceId !== null" severity="info">
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
          :label="t('common.save')"
          :loading="saving"
          :disabled="selectedInvoiceId === null || loading"
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
import { createSupplierPaymentFromTransaction, type BankTransaction } from '@/api/bank'
import { listInvoicesApi, type Invoice } from '@/api/invoices'
import { scoreInvoiceSuggestion } from '@/utils/bankReconciliation'
import { formatContactDisplayName } from '@/utils/contact'
import { formatDisplayDate } from '@/utils/format'
import { getErrorDetail } from '@/utils/errorUtils'

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
const invoices = ref<Invoice[]>([])
const contacts = ref<Contact[]>([])
const selectedInvoiceId = ref<number | null>(null)

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

function invoiceRemaining(invoice: Invoice): number {
  return Math.max(0, parseFloat(invoice.total_amount) - parseFloat(invoice.paid_amount))
}

const invoiceOptions = computed(() => {
  const amount = txAmount.value
  return invoices.value
    .filter(
      (inv) =>
        ['sent', 'partial', 'overdue'].includes(inv.status) && invoiceRemaining(inv) > 0,
    )
    .sort((a, b) => {
      const scoreA = scoreInvoiceSuggestion({
        transactionAmount: amount,
        transactionDate: props.transaction?.date ?? '',
        transactionDescription: props.transaction?.description ?? '',
        transactionReference: props.transaction?.reference,
        candidateNumber: a.number,
        candidateReference: a.reference,
        candidateContactName: contactName(a.contact_id),
        candidateDate: a.date,
        candidateRemainingAmount: invoiceRemaining(a),
      })
      const scoreB = scoreInvoiceSuggestion({
        transactionAmount: amount,
        transactionDate: props.transaction?.date ?? '',
        transactionDescription: props.transaction?.description ?? '',
        transactionReference: props.transaction?.reference,
        candidateNumber: b.number,
        candidateReference: b.reference,
        candidateContactName: contactName(b.contact_id),
        candidateDate: b.date,
        candidateRemainingAmount: invoiceRemaining(b),
      })
      if (scoreA !== scoreB) return scoreB - scoreA
      return b.date.localeCompare(a.date)
    })
    .map((inv) => ({
      label: `${inv.number} · ${contactName(inv.contact_id)} · ${t('bank.remaining_amount', { amount: formatAmount(invoiceRemaining(inv)) })}`,
      value: inv.id,
    }))
})

watch(
  () => props.visible,
  async (isVisible) => {
    if (!isVisible || !props.transaction) return
    selectedInvoiceId.value = null
    loading.value = true
    try {
      const [inv, cont] = await Promise.all([
        listInvoicesApi({ invoice_type: 'fournisseur' }),
        listContactsApi({ active_only: true }),
      ])
      invoices.value = inv
      contacts.value = cont
      selectedInvoiceId.value = invoiceOptions.value[0]?.value ?? null
    } catch (error) {
      toast.add({
        severity: 'error',
        summary: getErrorDetail(error, t('common.error.unknown')),
        life: 3000,
      })
    } finally {
      loading.value = false
    }
  },
)

async function submit(): Promise<void> {
  if (!props.transaction || selectedInvoiceId.value === null) return
  saving.value = true
  try {
    await createSupplierPaymentFromTransaction(props.transaction.id, selectedInvoiceId.value)
    emit('update:visible', false)
    toast.add({ severity: 'success', summary: t('bank.create_supplier_payment_success'), life: 3000 })
    emit('saved')
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: getErrorDetail(error, t('common.error.unknown')),
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
