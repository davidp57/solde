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
        <p class="app-dialog-intro__text">
          {{ form.type === 'especes' ? t('bank.deposit_especes_intro') : t('bank.deposit_intro') }}
        </p>
      </section>
      <section class="app-dialog-section">
        <div class="app-form-grid">
          <div class="app-field">
            <label class="app-field__label">{{ t('bank.deposit_date') }}</label>
            <AppDatePicker v-model="form.date" />
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

      <!-- ESPECES: montant + détail billets -->
      <template v-if="form.type === 'especes'">
        <section class="app-dialog-section">
          <div class="app-form-grid">
            <div class="app-field app-field--full">
              <label class="app-field__label">{{ t('bank.deposit_amount') }}</label>
              <InputNumber
                v-model="form.total_amount"
                :min="0.01"
                :min-fraction-digits="2"
                :max-fraction-digits="2"
                locale="fr-FR"
              />
            </div>
          </div>
        </section>
        <section class="app-dialog-section">
          <div class="app-dialog-section__header">
            <h3 class="app-dialog-section__title">
              {{ t('bank.deposit_denomination_title') }}
            </h3>
            <p class="app-dialog-section__copy">
              {{ t('bank.deposit_denomination_subtitle') }}
            </p>
          </div>
          <div class="bank-denomination-list">
            <div
              v-for="(line, idx) in form.denominations"
              :key="idx"
              class="bank-denomination-row"
            >
              <InputNumber
                v-model="form.denominations[idx].value"
                :min="0"
                :max-fraction-digits="2"
                :min-fraction-digits="2"
                locale="fr-FR"
                :placeholder="t('bank.deposit_denomination_value')"
                class="bank-denomination-row__value"
              />
              <span class="bank-denomination-row__sep">×</span>
              <InputNumber
                v-model="form.denominations[idx].count"
                :min="0"
                :max-fraction-digits="0"
                :placeholder="t('bank.deposit_denomination_count')"
                class="bank-denomination-row__count"
              />
              <Button
                icon="pi pi-times"
                text
                severity="secondary"
                size="small"
                @click="removeDenomination(idx)"
              />
            </div>
          </div>
          <Button
            :label="t('bank.deposit_denomination_add')"
            icon="pi pi-plus"
            text
            size="small"
            class="bank-denomination-add"
            @click="addDenomination"
          />
          <p v-if="denominationTotal > 0" class="bank-denomination-total">
            {{ t('bank.deposit_denomination_total', { amount: formatAmount(denominationTotal) }) }}
          </p>
        </section>
      </template>

      <!-- CHEQUES: liste des paiements -->
      <template v-else>
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
            <div class="bank-deposit-select-all">
              <Button
                :label="allSelected ? t('bank.deposit_deselect_all') : t('bank.deposit_select_all')"
                severity="secondary"
                text
                size="small"
                @click="toggleSelectAll"
              />
            </div>
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
                <span class="app-dialog-list__caption">{{
                  t(`payments.methods.${p.method}`)
                }}</span>
              </span>
            </label>
          </div>
        </section>
      </template>

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
          :disabled="!canSubmit"
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
import AppDatePicker from '@/components/ui/AppDatePicker.vue'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Select from 'primevue/select'
import { useToast } from 'primevue/usetoast'
import { createDeposit, type CashCountPrefill, type DenominationLine, type Payment } from '@/api/bank'
import { formatDisplayDate } from '@/utils/format'

const props = defineProps<{
  visible: boolean
  payments: Payment[]
  prefillFromCount?: CashCountPrefill | null
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
  total_amount: null as number | null,
  denominations: [] as DenominationLine[],
})

const depositTypeOptions = [
  { label: t('bank.deposit_types.cheques'), value: 'cheques' },
  { label: t('bank.deposit_types.especes'), value: 'especes' },
]

const availablePayments = computed(() => {
  return props.payments.filter((p) => p.method === 'cheque')
})

const allSelected = computed(
  () =>
    availablePayments.value.length > 0 &&
    availablePayments.value.every((p) => form.value.payment_ids.includes(p.id)),
)

function toggleSelectAll(): void {
  if (allSelected.value) {
    form.value.payment_ids = []
  } else {
    form.value.payment_ids = availablePayments.value.map((p) => p.id)
  }
}

const denominationTotal = computed(() =>
  form.value.denominations.reduce(
    (sum, l) => sum + (l.value ?? 0) * (l.count ?? 0),
    0,
  ),
)

const canSubmit = computed(() => {
  if (form.value.type === 'especes') {
    return (form.value.total_amount ?? 0) > 0
  }
  return form.value.payment_ids.length > 0
})

function formatAmount(value: string | number): string {
  return `${parseFloat(String(value)).toFixed(2)} €`
}

function toIsoDate(d: Date | string): string {
  if (typeof d === 'string') return d
  return d.toISOString().slice(0, 10)
}

function addDenomination(): void {
  form.value.denominations.push({ value: 0, count: 0 })
}

function removeDenomination(idx: number): void {
  form.value.denominations.splice(idx, 1)
}

watch(
  () => form.value.type,
  () => {
    form.value.payment_ids = []
    form.value.total_amount = null
    form.value.denominations = []
  },
)

watch(
  () => props.visible,
  (vis) => {
    if (!vis || !props.prefillFromCount) return
    const p = props.prefillFromCount
    form.value = {
      date: new Date(p.date + 'T00:00:00'),
      type: 'especes',
      bank_reference: '',
      payment_ids: [],
      total_amount: p.total_amount,
      denominations: [...p.denominations],
    }
  },
)

async function submit(): Promise<void> {
  saving.value = true
  try {
    if (form.value.type === 'especes') {
      const denomDetails =
        form.value.denominations.length > 0
          ? JSON.stringify(
              form.value.denominations.filter((l) => (l.value ?? 0) > 0 && (l.count ?? 0) > 0),
            )
          : null
      await createDeposit({
        date: toIsoDate(form.value.date),
        type: 'especes',
        total_amount: String(form.value.total_amount ?? 0),
        denomination_details: denomDetails,
        bank_reference: form.value.bank_reference || null,
      })
    } else {
      await createDeposit({
        date: toIsoDate(form.value.date),
        type: 'cheques',
        payment_ids: form.value.payment_ids,
        bank_reference: form.value.bank_reference || null,
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

.bank-deposit-select-all {
  display: flex;
  justify-content: flex-end;
  margin-bottom: var(--app-space-1);
}

.bank-denomination-list {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-2);
  margin-bottom: var(--app-space-2);
}

.bank-denomination-row {
  display: flex;
  align-items: center;
  gap: var(--app-space-2);
}

.bank-denomination-row__value {
  width: 8rem;
}

.bank-denomination-row__count {
  width: 6rem;
}

.bank-denomination-row__sep {
  color: var(--p-text-muted-color);
  font-weight: 600;
}

.bank-denomination-add {
  align-self: flex-start;
}

.bank-denomination-total {
  margin-top: var(--app-space-2);
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}
</style>
