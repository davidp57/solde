<template>
  <Dialog
    :visible="visible"
    :header="t('bank.link_client_payment_title')"
    modal
    class="app-dialog app-dialog--medium"
    @update:visible="$emit('update:visible', $event)"
  >
    <div class="app-dialog-form bank-form">
      <section class="app-dialog-intro">
        <p class="app-dialog-intro__eyebrow">{{ t('bank.link_client_payment') }}</p>
        <p class="app-dialog-intro__text">{{ t('bank.link_client_payment_intro') }}</p>
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
          <label class="app-field__label">{{ t('bank.link_client_payment_payments') }}</label>
          <div
            v-if="!loading && selections.length > 0"
            class="app-dialog-list bank-allocation-list"
          >
            <div
              v-for="sel in selections"
              :key="sel.payment_id"
              class="app-dialog-list__item bank-allocation-item"
            >
              <div class="bank-allocation-item__summary">
                <Checkbox v-model="sel.selected" binary />
                <span class="app-dialog-list__meta">
                  <span class="app-dialog-list__title">{{ sel.title }}</span>
                  <span class="app-dialog-list__caption">{{ sel.caption }}</span>
                </span>
              </div>
              <strong class="bank-allocation-item__fixed-amount">{{
                formatAmount(sel.amount)
              }}</strong>
            </div>
          </div>
        </div>
        <Message v-if="!loading && selections.length === 0" severity="warn">
          {{ t('bank.link_client_payment_no_payment') }}
        </Message>
        <Message
          v-else-if="!loading"
          :severity="Math.abs(remainingToMatch) < 0.005 ? 'info' : 'warn'"
        >
          {{
            Math.abs(remainingToMatch) < 0.005
              ? t('bank.link_client_payment_ready_to_confirm')
              : t('bank.link_client_payment_remaining_to_match', {
                  amount: formatAmount(remainingToMatch),
                })
          }}
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
          :disabled="loading || !canSubmit"
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
import Checkbox from 'primevue/checkbox'
import Dialog from 'primevue/dialog'
import Message from 'primevue/message'
import { useToast } from 'primevue/usetoast'
import { listContactsApi, type Contact } from '@/api/contacts'
import {
  linkClientPaymentToTransaction,
  linkClientPaymentsToTransaction,
  type BankTransaction,
} from '@/api/bank'
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

interface SelectionDraft {
  payment_id: number
  title: string
  caption: string
  amount: number
  selected: boolean
}

const loading = ref(false)
const saving = ref(false)
const payments = ref<Payment[]>([])
const contacts = ref<Contact[]>([])
const selections = ref<SelectionDraft[]>([])

const txAmount = computed(() =>
  props.transaction ? parseFloat(props.transaction.amount) : 0,
)

function formatAmount(value: string | number): string {
  return `${parseFloat(String(value)).toFixed(2)} €`
}

function contactName(contactId: number): string {
  const c = contacts.value.find((x) => x.id === contactId)
  return c ? formatContactDisplayName(c) : `#${contactId}`
}

const sortedPayments = computed(() => {
  const amount = txAmount.value
  return payments.value
    .filter(
      (p) =>
        p.method === 'virement' && parseFloat(p.amount) <= amount + 0.0001,
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
})

function buildSelections(): SelectionDraft[] {
  let remaining = txAmount.value
  return sortedPayments.value.map((p) => {
    const amount = parseFloat(p.amount)
    const reference = p.reference ? ` · ${p.reference}` : ''
    const selected = amount <= remaining + 0.0001
    if (selected) remaining = Number((remaining - amount).toFixed(2))
    return {
      payment_id: p.id,
      title: `${p.invoice_number || `#${p.invoice_id}`} · ${contactName(p.contact_id)}`,
      caption: `${formatDisplayDate(p.date)}${reference}`,
      amount,
      selected,
    }
  })
}

const selectedTotal = computed(() =>
  selections.value.reduce((sum, s) => sum + (s.selected ? s.amount : 0), 0),
)
const remainingToMatch = computed(() =>
  Number((txAmount.value - selectedTotal.value).toFixed(2)),
)
const canSubmit = computed(
  () =>
    selections.value.some((s) => s.selected) && Math.abs(remainingToMatch.value) < 0.005,
)

watch(
  () => props.visible,
  async (isVisible) => {
    if (!isVisible || !props.transaction) return
    selections.value = []
    loading.value = true
    try {
      const [pmts, conts] = await Promise.all([
        listPayments({ invoice_type: 'client' }),
        listContactsApi({ active_only: true }),
      ])
      payments.value = pmts
      contacts.value = conts
      selections.value = buildSelections()
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
  if (!props.transaction || !canSubmit.value) return
  saving.value = true
  try {
    const ids = selections.value.filter((s) => s.selected).map((s) => s.payment_id)
    const [first] = ids
    if (ids.length === 1 && first !== undefined) {
      await linkClientPaymentToTransaction(props.transaction.id, first)
    } else {
      await linkClientPaymentsToTransaction(props.transaction.id, ids)
    }
    emit('update:visible', false)
    toast.add({
      severity: 'success',
      summary: t('bank.link_client_payment_success', { count: ids.length }),
      life: 3000,
    })
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

.bank-allocation-list {
  gap: var(--app-space-3);
}

.bank-allocation-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--app-space-4);
}

.bank-allocation-item__summary {
  display: flex;
  align-items: flex-start;
  gap: var(--app-space-3);
  min-width: 0;
}

.bank-allocation-item__fixed-amount {
  white-space: nowrap;
}

@media (max-width: 768px) {
  .bank-allocation-item {
    flex-direction: column;
  }
}
</style>
