<template>
  <Dialog
    :visible="visible"
    :header="t('bank.create_client_payment_title')"
    modal
    class="app-dialog app-dialog--medium"
    @update:visible="$emit('update:visible', $event)"
  >
    <div class="app-dialog-form bank-form">
      <section class="app-dialog-intro">
        <p class="app-dialog-intro__eyebrow">{{ t('bank.create_client_payment') }}</p>
        <p class="app-dialog-intro__text">{{ t('bank.create_client_payment_intro') }}</p>
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
          <label class="app-field__label">{{
            t('bank.create_client_payment_allocations')
          }}</label>
          <div
            v-if="!loading && allocations.length > 0"
            class="app-dialog-list bank-allocation-list"
          >
            <div
              v-for="allocation in allocations"
              :key="allocation.invoice_id"
              class="app-dialog-list__item bank-allocation-item"
            >
              <div class="bank-allocation-item__summary">
                <Checkbox
                  v-model="allocation.selected"
                  binary
                  @update:model-value="syncAmount(allocation)"
                />
                <span class="app-dialog-list__meta">
                  <span class="app-dialog-list__title">{{ allocation.title }}</span>
                  <span class="app-dialog-list__caption">{{ allocation.caption }}</span>
                </span>
              </div>
              <div class="bank-allocation-item__amount">
                <label class="app-field__label">{{
                  t('bank.create_client_payment_allocated_amount')
                }}</label>
                <InputNumber
                  v-model="allocation.allocated_amount"
                  mode="currency"
                  currency="EUR"
                  locale="fr-FR"
                  :min="0"
                  :max="maxAmount(allocation)"
                  :disabled="!allocation.selected"
                  fluid
                  @update:model-value="syncAmount(allocation)"
                />
              </div>
            </div>
          </div>
        </div>
        <Message v-if="!loading && allocations.length === 0" severity="warn">
          {{ t('bank.create_client_payment_no_invoice') }}
        </Message>
        <Message
          v-else-if="!loading"
          :severity="Math.abs(remainingToAllocate) < 0.005 ? 'info' : 'warn'"
        >
          {{
            Math.abs(remainingToAllocate) < 0.005
              ? t('bank.create_client_payment_ready_to_save')
              : t('bank.create_client_payment_remaining_to_allocate', {
                  amount: formatAmount(remainingToAllocate),
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
          :label="t('common.save')"
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
import InputNumber from 'primevue/inputnumber'
import Message from 'primevue/message'
import { useToast } from 'primevue/usetoast'
import { listContactsApi, type Contact } from '@/api/contacts'
import {
  createClientPaymentsFromTransaction,
  type BankTransaction,
  type BankTransactionClientPaymentAllocation,
} from '@/api/bank'
import { listInvoicesApi, type Invoice } from '@/api/invoices'
import { scoreInvoiceSuggestion } from '@/utils/bankReconciliation'
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

interface AllocationDraft {
  invoice_id: number
  title: string
  caption: string
  remaining_amount: number
  allocated_amount: number
  selected: boolean
}

const loading = ref(false)
const saving = ref(false)
const invoices = ref<Invoice[]>([])
const contacts = ref<Contact[]>([])
const allocations = ref<AllocationDraft[]>([])

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

function invoiceRemaining(invoice: Invoice): number {
  return Math.max(0, parseFloat(invoice.total_amount) - parseFloat(invoice.paid_amount))
}

const sortedInvoices = computed(() => {
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
})

function buildAllocations(): AllocationDraft[] {
  let remaining = txAmount.value
  return sortedInvoices.value.map((inv) => {
    const rem = invoiceRemaining(inv)
    const suggested = Math.min(rem, Math.max(remaining, 0))
    remaining = Number((remaining - suggested).toFixed(2))
    return {
      invoice_id: inv.id,
      title: `${inv.number} · ${contactName(inv.contact_id)}`,
      caption: `${formatDisplayDate(inv.date)} · ${t('bank.remaining_amount', { amount: formatAmount(rem) })}`,
      remaining_amount: rem,
      allocated_amount: suggested,
      selected: suggested > 0,
    }
  })
}

const selectedTotal = computed(() =>
  allocations.value.reduce(
    (sum, a) => sum + (a.selected ? Number(a.allocated_amount || 0) : 0),
    0,
  ),
)
const remainingToAllocate = computed(() =>
  Number((txAmount.value - selectedTotal.value).toFixed(2)),
)
const canSubmit = computed(
  () =>
    allocations.value.some((a) => a.selected && a.allocated_amount > 0) &&
    Math.abs(remainingToAllocate.value) < 0.005,
)

function selectedSumExcluding(invoiceId: number): number {
  return allocations.value.reduce((sum, a) => {
    if (!a.selected || a.invoice_id === invoiceId) return sum
    return sum + Number(a.allocated_amount || 0)
  }, 0)
}

function maxAmount(allocation: AllocationDraft): number {
  const remaining = txAmount.value - selectedSumExcluding(allocation.invoice_id)
  return Math.max(0, Math.min(allocation.remaining_amount, remaining))
}

function syncAmount(allocation: AllocationDraft): void {
  if (!allocation.selected) {
    allocation.allocated_amount = 0
    return
  }
  const max = maxAmount(allocation)
  const current = Number(allocation.allocated_amount || 0)
  allocation.allocated_amount = current <= 0 ? max : Math.min(current, max)
}

watch(
  () => props.visible,
  async (isVisible) => {
    if (!isVisible || !props.transaction) return
    allocations.value = []
    loading.value = true
    try {
      const [inv, cont] = await Promise.all([
        listInvoicesApi({ invoice_type: 'client' }),
        listContactsApi({ active_only: true }),
      ])
      invoices.value = inv
      contacts.value = cont
      allocations.value = buildAllocations()
    } catch {
      toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
    } finally {
      loading.value = false
    }
  },
)

async function submit(): Promise<void> {
  if (!props.transaction || !canSubmit.value) return
  saving.value = true
  try {
    const payload: BankTransactionClientPaymentAllocation[] = allocations.value
      .filter((a) => a.selected && a.allocated_amount > 0)
      .map((a) => ({ invoice_id: a.invoice_id, amount: a.allocated_amount.toFixed(2) }))
    await createClientPaymentsFromTransaction(props.transaction.id, payload)
    emit('update:visible', false)
    toast.add({
      severity: 'success',
      summary: t('bank.create_client_payment_success', { count: payload.length }),
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

.bank-allocation-item__amount {
  min-width: 12rem;
}

@media (max-width: 768px) {
  .bank-allocation-item {
    flex-direction: column;
  }

  .bank-allocation-item__amount {
    width: 100%;
    min-width: 0;
  }
}
</style>
