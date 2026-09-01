<template>
  <Dialog
    :visible="visible"
    :header="t('bank.merge_deposit_title')"
    modal
    class="app-dialog app-dialog--medium"
    @update:visible="$emit('update:visible', $event)"
  >
    <div class="app-dialog-form bank-form">
      <section class="app-dialog-intro">
        <p class="app-dialog-intro__eyebrow">{{ t('bank.merge_deposit') }}</p>
        <p class="app-dialog-intro__text">{{ t('bank.merge_deposit_intro') }}</p>
      </section>
      <section class="app-dialog-section">
        <p v-if="transaction" class="app-dialog-note">
          {{
            t('bank.create_client_payment_tx_summary', {
              date: formatDisplayDate(transaction.date),
              amount: formatAmount(transaction.amount),
              description: transaction.description || '-',
            })
          }}
        </p>
        <div class="app-field">
          <label class="app-field__label">{{ t('bank.merge_deposit_slip') }}</label>
          <Select
            v-model="selectedTxId"
            :options="candidateOptions"
            option-label="label"
            option-value="value"
            :loading="loading"
            :placeholder="loading ? t('common.loading') : t('bank.merge_deposit_slip')"
            filter
            show-clear
          />
        </div>
        <Message v-if="!loading && candidateOptions.length === 0" severity="warn">
          {{ t('bank.merge_deposit_no_candidate') }}
        </Message>
        <Message v-else-if="!loading" severity="info">
          {{ t('bank.merge_deposit_hint') }}
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
          :disabled="selectedTxId === null || loading"
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
import {
  listDepositMergeCandidates,
  mergeDepositTransaction,
  type BankTransaction,
} from '@/api/bank'
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
const candidates = ref<BankTransaction[]>([])
const selectedTxId = ref<number | null>(null)

function formatAmount(value: string | number): string {
  return `${parseFloat(String(value)).toFixed(2)} €`
}

// The API already returns the candidates closest in date first.
const candidateOptions = computed(() =>
  candidates.value.map((c) => ({
    label: `${c.description} · ${formatDisplayDate(c.date)} · ${formatAmount(c.amount)}`,
    value: c.id,
  })),
)

watch(
  () => props.visible,
  async (isVisible) => {
    if (!isVisible || !props.transaction) return
    selectedTxId.value = null
    candidates.value = []
    loading.value = true
    try {
      candidates.value = await listDepositMergeCandidates(props.transaction.id)
      selectedTxId.value = candidates.value[0]?.id ?? null
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
  if (!props.transaction || selectedTxId.value === null) return
  saving.value = true
  try {
    await mergeDepositTransaction(props.transaction.id, selectedTxId.value)
    emit('update:visible', false)
    toast.add({ severity: 'success', summary: t('bank.merge_deposit_success'), life: 3000 })
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
