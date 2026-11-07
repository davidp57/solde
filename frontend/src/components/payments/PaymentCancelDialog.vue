<template>
  <Dialog
    :visible="visible"
    :header="t('payments.cancel_title')"
    modal
    class="app-dialog app-dialog--medium"
    @update:visible="emit('update:visible', $event)"
  >
    <div class="app-dialog-form" data-testid="payment-cancel-body">
      <p v-if="previewLoading">{{ t('payments.cancel_loading') }}</p>
      <template v-else-if="preview && preview.can_cancel">
        <p>{{ introText }}</p>
        <p v-if="depositText">{{ depositText }}</p>
        <p class="app-dialog-hint">{{ t('payments.cancel_hint') }}</p>
      </template>
      <Message v-else-if="preview" severity="warn">{{ refusalText }}</Message>
    </div>
    <template #footer>
      <Button :label="t('common.close')" text @click="emit('update:visible', false)" />
      <Button
        v-if="preview?.can_cancel"
        data-testid="payment-cancel-confirm"
        :label="t('payments.cancel_confirm')"
        icon="pi pi-trash"
        severity="danger"
        :loading="cancelling"
        @click="confirm"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
/**
 * Cancel a payment entered by mistake (admin only, enforced by the API).
 *
 * Shows what cancelling would touch — or why it is refused — before anything is
 * done. Shared by the Payments screen (client payments) and the supplier invoice
 * detail, the only place supplier payments are listed.
 */
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Message from 'primevue/message'
import { useToast } from 'primevue/usetoast'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  cancelPayment,
  getPaymentCancelPreview,
  type Payment,
  type PaymentCancelPreview,
} from '@/api/payments'
import { getErrorDetail } from '@/utils/errorUtils'
import { formatDisplayDate } from '@/utils/format'

const props = defineProps<{
  visible: boolean
  payment: Payment | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  cancelled: [payment: Payment]
}>()

const { t } = useI18n()
const toast = useToast()

const preview = ref<PaymentCancelPreview | null>(null)
const previewLoading = ref(false)
const cancelling = ref(false)

function formatAmount(value: string | number): string {
  return `${parseFloat(String(value)).toFixed(2)} €`
}

async function loadPreview(payment: Payment): Promise<void> {
  preview.value = null
  previewLoading.value = true
  try {
    preview.value = await getPaymentCancelPreview(payment.id)
  } catch (err: unknown) {
    emit('update:visible', false)
    toast.add({ severity: 'error', summary: getErrorDetail(err, t('common.error.unknown')), life: 3000 })
  } finally {
    previewLoading.value = false
  }
}

watch(
  () => [props.visible, props.payment] as const,
  ([visible, payment]) => {
    if (visible && payment) void loadPreview(payment)
  },
  { immediate: true },
)

const introText = computed(() => {
  if (!preview.value) return ''
  return t('payments.cancel_intro', {
    amount: formatAmount(preview.value.amount),
    date: formatDisplayDate(preview.value.date),
  })
})

const depositText = computed(() => {
  const current = preview.value
  if (!current || current.deposit_id === null) return ''
  const depositDate = formatDisplayDate(current.deposit_date ?? '')
  if (current.deposit_will_be_deleted) {
    return t('payments.cancel_deposit_deleted', { date: depositDate })
  }
  return t('payments.cancel_deposit_kept', {
    date: depositDate,
    before: formatAmount(current.deposit_total_before ?? '0'),
    after: formatAmount(current.deposit_total_after ?? '0'),
  })
})

const refusalText = computed(() => {
  const code = preview.value?.reason_code
  return code ? t(`payments.cancel_refused.${code}`) : ''
})

async function confirm(): Promise<void> {
  const payment = props.payment
  if (!payment) return
  cancelling.value = true
  try {
    await cancelPayment(payment.id)
    emit('update:visible', false)
    toast.add({ severity: 'success', summary: t('payments.cancelled'), life: 3000 })
    emit('cancelled', payment)
  } catch (err: unknown) {
    toast.add({ severity: 'error', summary: getErrorDetail(err, t('common.error.unknown')), life: 5000 })
  } finally {
    cancelling.value = false
  }
}
</script>
