<template>
  <Dialog
    :visible="visible"
    :header="t('bank.new_deposit')"
    modal
    class="app-dialog app-dialog--medium"
    @update:visible="$emit('update:visible', $event)"
  >
    <div class="app-dialog-form bank-form">
      <section class="app-dialog-intro">
        <p class="app-dialog-intro__eyebrow">{{ t('bank.deposits_title') }}</p>
        <p class="app-dialog-intro__text">{{ t('bank.deposit_intro') }}</p>
      </section>
      <section class="app-dialog-section">
        <div class="app-form-grid">
          <div class="app-field">
            <label class="app-field__label">{{ t('bank.deposit_date') }}</label>
            <DatePicker v-model="form.date" date-format="yy-mm-dd" show-icon />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('bank.deposit_type') }}</label>
            <Select
              v-model="form.type"
              :options="depositTypeOptions"
              option-label="label"
              option-value="value"
            />
          </div>
          <div class="app-field app-field--full">
            <label class="app-field__label">{{ t('bank.deposit_bank_ref') }}</label>
            <InputText v-model="form.bank_reference" />
          </div>
        </div>
      </section>
      <section class="app-dialog-section">
        <div class="app-dialog-section__header">
          <h3 class="app-dialog-section__title">{{ t('bank.deposit_selection_title') }}</h3>
          <p class="app-dialog-section__copy">{{ t('bank.deposit_selection_subtitle') }}</p>
        </div>
        <Message v-if="availablePayments.length === 0" severity="warn">
          {{ t('bank.deposit_empty') }}
        </Message>
        <p v-if="availablePayments.length === 0" class="app-dialog-note">
          {{ t('bank.deposit_empty_hint') }}
        </p>
        <div v-else class="app-dialog-list">
          <label
            v-for="p in availablePayments"
            :key="p.id"
            class="app-dialog-list__item bank-payment-option"
          >
            <Checkbox v-model="form.payment_ids" :value="p.id" />
            <span class="app-dialog-list__meta">
              <span class="app-dialog-list__title">
                {{ formatDisplayDate(p.date) }} — {{ formatAmount(p.amount) }}
              </span>
              <span class="app-dialog-list__caption">{{ t(`payments.methods.${p.method}`) }}</span>
            </span>
          </label>
        </div>
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
          :disabled="form.payment_ids.length === 0"
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
import DatePicker from 'primevue/datepicker'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Select from 'primevue/select'
import { useToast } from 'primevue/usetoast'
import { createDeposit, type Payment } from '@/api/bank'
import { formatDisplayDate } from '@/utils/format'

const props = defineProps<{
  visible: boolean
  payments: Payment[]
}>()
const emit = defineEmits<{
  'update:visible': [val: boolean]
  saved: []
}>()

const { t } = useI18n()
const toast = useToast()
const saving = ref(false)
const form = ref({
  date: new Date(),
  type: 'cheques' as 'cheques' | 'especes',
  bank_reference: '',
  payment_ids: [] as number[],
})

const depositTypeOptions = [
  { label: t('bank.deposit_types.cheques'), value: 'cheques' },
  { label: t('bank.deposit_types.especes'), value: 'especes' },
]

const availablePayments = computed(() => {
  const expectedMethod = form.value.type === 'cheques' ? 'cheque' : 'especes'
  return props.payments.filter((p) => p.method === expectedMethod)
})

function formatAmount(value: string | number): string {
  return `${parseFloat(String(value)).toFixed(2)} €`
}

function toIsoDate(d: Date | string): string {
  if (typeof d === 'string') return d
  return d.toISOString().slice(0, 10)
}

watch(
  () => form.value.type,
  () => {
    form.value.payment_ids = []
  },
)

async function submit(): Promise<void> {
  saving.value = true
  try {
    await createDeposit({
      date: toIsoDate(form.value.date),
      type: form.value.type,
      payment_ids: form.value.payment_ids,
      bank_reference: form.value.bank_reference || null,
    })
    emit('update:visible', false)
    emit('saved')
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
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

.bank-payment-option {
  cursor: pointer;
}

.bank-payment-option :deep(.p-checkbox) {
  margin-top: 0.15rem;
}
</style>
