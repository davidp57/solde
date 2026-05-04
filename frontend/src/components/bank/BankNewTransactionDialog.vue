<template>
  <Dialog
    :visible="visible"
    :header="editTransaction ? t('bank.edit_transaction') : t('bank.new_transaction')"
    modal
    class="app-dialog app-dialog--medium"
    @update:visible="$emit('update:visible', $event)"
  >
    <form class="app-dialog-form bank-form" @submit.prevent="submit">
      <section class="app-dialog-intro">
        <p class="app-dialog-intro__eyebrow">{{ t('bank.transactions_title') }}</p>
        <p class="app-dialog-intro__text">{{ t('bank.transaction_intro') }}</p>
      </section>
      <section class="app-dialog-section">
        <div class="app-form-grid">
          <div class="app-field">
            <label class="app-field__label">{{ t('bank.tx_date') }}</label>
            <AppDatePicker v-model="form.date" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('bank.tx_amount') }}</label>
            <InputNumber
              v-model="form.amount"
              mode="decimal"
              :min-fraction-digits="2"
              :max-fraction-digits="2"
            />
          </div>
          <div class="app-field app-field--full">
            <label class="app-field__label">{{ t('bank.tx_description') }}</label>
            <InputText v-model="form.description" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('bank.tx_reference') }}</label>
            <InputText v-model="form.reference" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('bank.tx_account') }}</label>
            <Select
              v-model="form.bank_account"
              :options="[
                { label: t('bank.filter_account_courant'), value: 'courant' },
                { label: t('bank.filter_account_epargne'), value: 'epargne' },
              ]"
              option-label="label"
              option-value="value"
              class="w-full"
            />
          </div>
        </div>
      </section>
      <div class="app-form-actions">
        <Button
          :label="t('common.cancel')"
          severity="secondary"
          text
          @click="$emit('update:visible', false)"
        />
        <Button type="submit" :label="t('common.save')" :loading="saving" />
      </div>
    </form>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import AppDatePicker from '@/components/ui/AppDatePicker.vue'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import { useToast } from 'primevue/usetoast'
import Select from 'primevue/select'
import { addTransaction, updateTransaction, type BankAccountType, type BankTransaction } from '@/api/bank'

const props = defineProps<{ visible: boolean; editTransaction?: BankTransaction | null; defaultBankAccount?: BankAccountType | null }>()
const emit = defineEmits<{
  'update:visible': [val: boolean]
  saved: []
}>()

const { t } = useI18n()
const toast = useToast()
const saving = ref(false)
const form = ref({
  date: new Date(),
  amount: 0,
  description: '',
  reference: '',
  bank_account: 'courant' as BankAccountType,
})

watch(
  [() => props.editTransaction, () => props.visible],
  ([tx]) => {
    if (!props.visible) return
    if (tx) {
      form.value = {
        date: new Date(tx.date + 'T12:00:00'),
        amount: parseFloat(tx.amount),
        description: tx.description,
        reference: tx.reference ?? '',
        bank_account: tx.bank_account,
      }
    } else {
      form.value = {
        date: new Date(),
        amount: 0,
        description: '',
        reference: '',
        bank_account: (props.defaultBankAccount ?? 'courant') as BankAccountType,
      }
    }
  },
  { immediate: true },
)

function toIsoDate(d: Date | string): string {
  if (typeof d === 'string') return d
  return d.toISOString().slice(0, 10)
}

async function submit(): Promise<void> {
  saving.value = true
  try {
    if (props.editTransaction) {
      await updateTransaction(props.editTransaction.id, {
        date: toIsoDate(form.value.date),
        amount: String(form.value.amount),
        description: form.value.description,
        reference: form.value.reference || null,
        bank_account: form.value.bank_account,
      })
    } else {
      await addTransaction({
        date: toIsoDate(form.value.date),
        amount: String(form.value.amount),
        description: form.value.description,
        reference: form.value.reference || null,
        bank_account: form.value.bank_account,
      })
    }
    emit('update:visible', false)
    emit('saved')
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    saving.value = false
  }
}
</script>
