<template>
  <Dialog
    :visible="visible"
    :header="t('bank.deposit_actions_title')"
    modal
    class="app-dialog app-dialog--medium"
    @update:visible="$emit('update:visible', $event)"
  >
    <div class="app-dialog-form bank-form">
      <section class="app-dialog-intro">
        <p class="app-dialog-intro__eyebrow">
          {{ t(`bank.deposit_types.${deposit.type}`) }} · {{ formatDisplayDate(deposit.date) }}
        </p>
        <p class="app-dialog-intro__text">
          {{ t('bank.deposit_actions_intro') }}
        </p>
      </section>

      <!-- Cheques: list of payments with removal checkboxes -->
      <template v-if="deposit.type === 'cheques'">
        <section class="app-dialog-section">
          <div class="app-dialog-section__header">
            <h3 class="app-dialog-section__title">{{ t('bank.deposit_selection_title') }}</h3>
            <p class="app-dialog-section__copy">{{ t('bank.deposit_actions_cheques_hint') }}</p>
          </div>
          <Message v-if="loadingPayments" severity="secondary">{{ t('common.loading') }}</Message>
          <div v-else-if="paymentRows.length > 0" class="app-dialog-list">
            <label
              v-for="row in paymentRows"
              :key="row.id"
              class="app-dialog-list__item bank-payment-option"
            >
              <Checkbox v-model="selectedIds" :value="row.id" />
              <span class="app-dialog-list__meta">
                <span class="app-dialog-list__title">
                  {{ formatDisplayDate(row.date) }} — {{ formatAmount(row.amount) }}
                </span>
                <span class="app-dialog-list__caption">
                  {{ row.cheque_number ? t('bank.deposit_actions_cheque_num', { n: row.cheque_number }) : t(`payments.methods.${row.method}`) }}
                </span>
              </span>
            </label>
          </div>
          <Message v-else severity="warn">{{ t('bank.deposit_empty') }}</Message>
        </section>
        <p v-if="selectedIds.length > 0" class="bank-deposit-actions__total app-money">
          {{ t('bank.deposit_actions_selected_total', { amount: formatAmount(selectedTotal) }) }}
        </p>
        <Message v-if="selectedIds.length === 0 && !loadingPayments" severity="warn">
          {{ t('bank.deposit_actions_empty_warning') }}
        </Message>
      </template>

      <!-- Espèces: denomination details -->
      <template v-else>
        <section class="app-dialog-section">
          <div class="app-dialog-section__header">
            <h3 class="app-dialog-section__title">{{ t('bank.deposit_denomination_title') }}</h3>
            <p class="app-dialog-section__copy">{{ t('bank.deposit_denomination_subtitle') }}</p>
          </div>
          <div class="bank-denomination-list">
            <div
              v-for="(line, idx) in espForm.denominations"
              :key="idx"
              class="bank-denomination-row"
            >
              <InputNumber
                v-model="espForm.denominations[idx].value"
                :min="0"
                :max-fraction-digits="2"
                :min-fraction-digits="2"
                locale="fr-FR"
                :placeholder="t('bank.deposit_denomination_value')"
                class="bank-denomination-row__value"
              />
              <span class="bank-denomination-row__sep">×</span>
              <InputNumber
                v-model="espForm.denominations[idx].count"
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

      <!-- Action buttons -->
      <div class="bank-deposit-actions__footer">
        <!-- Left group: cancel changes / cancel deposit -->
        <div class="bank-deposit-actions__left">
          <Button
            :label="t('bank.deposit_actions_cancel_changes')"
            severity="secondary"
            text
            :disabled="saving"
            @click="$emit('update:visible', false)"
          />
          <Button
            :label="t('bank.deposit_actions_cancel_deposit')"
            severity="danger"
            outlined
            :loading="saving === 'delete'"
            :disabled="!!saving && saving !== 'delete'"
            @click="cancelDeposit"
          />
        </div>
        <!-- Right group: save / confirm -->
        <div class="bank-deposit-actions__right">
          <Button
            :label="t('bank.deposit_actions_save_changes')"
            severity="secondary"
            :loading="saving === 'save'"
            :disabled="!canSave || (!!saving && saving !== 'save')"
            @click="saveChanges"
          />
          <Button
            :label="t('bank.deposit_confirm')"
            severity="success"
            icon="pi pi-check"
            :loading="saving === 'confirm'"
            :disabled="!canSave || (!!saving && saving !== 'confirm')"
            @click="confirmDeposit"
          />
        </div>
      </div>
    </div>
    <ConfirmDialog />
  </Dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import ConfirmDialog from 'primevue/confirmdialog'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import Message from 'primevue/message'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import {
  confirmDeposit as apiConfirmDeposit,
  deleteDeposit as apiDeleteDeposit,
  updateDeposit as apiUpdateDeposit,
  type Deposit,
  type DenominationLine,
} from '@/api/bank'
import { listPayments, type Payment } from '@/api/payments'
import { formatDisplayDate } from '@/utils/format'
import { getErrorDetail } from '@/utils/errorUtils'

const props = defineProps<{
  visible: boolean
  deposit: Deposit
}>()

const emit = defineEmits<{
  'update:visible': [val: boolean]
  /** Emitted after any mutation (save, confirm, cancel) so the parent reloads */
  updated: []
  cancelled: []
}>()

const { t } = useI18n()
const confirm = useConfirm()
const toast = useToast()

// --- cheques state ---
const loadingPayments = ref(false)
const allPayments = ref<Payment[]>([])
const selectedIds = ref<number[]>([...props.deposit.payment_ids])

// --- espèces state ---
interface EspForm {
  denominations: DenominationLine[]
}

function parseDenominations(raw: string | null): DenominationLine[] {
  if (!raw) return []
  try {
    return JSON.parse(raw) as DenominationLine[]
  } catch {
    return []
  }
}

const espForm = ref<EspForm>({
  denominations: parseDenominations(props.deposit.denomination_details),
})

// --- saving state ---
const saving = ref<false | 'save' | 'confirm' | 'delete'>(false)

// --- load payments for cheques deposit ---
watch(
  () => props.visible,
  async (vis) => {
    if (!vis) return
    // Reset form from current deposit
    selectedIds.value = [...props.deposit.payment_ids]
    espForm.value = {
      denominations: parseDenominations(props.deposit.denomination_details),
    }
    if (props.deposit.type !== 'cheques') return
    loadingPayments.value = true
    try {
      // Load all cheque payments that are either in this deposit or still free
      const all = await listPayments({ method: 'cheque', limit: 1000 })
      allPayments.value = all.filter(
        (p) =>
          props.deposit.payment_ids.includes(p.id) ||
          (!p.deposited && !p.in_deposit),
      )
    } finally {
      loadingPayments.value = false
    }
  },
  { immediate: true },
)

const paymentRows = computed(() => {
  // Show only payments that are currently in this deposit (may have been removed by user)
  // plus free cheque payments
  return allPayments.value
})

const selectedTotal = computed(() => {
  return allPayments.value
    .filter((p) => selectedIds.value.includes(p.id))
    .reduce((sum, p) => sum + parseFloat(p.amount), 0)
})

/** Sum of valid denomination lines (value × count). Zero when no lines are set. */
const denominationTotal = computed(() =>
  espForm.value.denominations.reduce((sum, l) => sum + (l.value ?? 0) * (l.count ?? 0), 0),
)

const canSave = computed(() => {
  if (props.deposit.type === 'cheques') {
    return selectedIds.value.length > 0
  }
  return denominationTotal.value > 0
})

function formatAmount(value: string | number): string {
  return `${parseFloat(String(value)).toFixed(2)} €`
}

function addDenomination(): void {
  espForm.value.denominations.push({ value: 0, count: 0 })
}

function removeDenomination(idx: number): void {
  espForm.value.denominations.splice(idx, 1)
}

function buildUpdatePayload() {
  if (props.deposit.type === 'cheques') {
    return { payment_ids: selectedIds.value }
  }
  const validLines = espForm.value.denominations.filter(
    (l) => (l.value ?? 0) > 0 && (l.count ?? 0) > 0,
  )
  return {
    total_amount: String(denominationTotal.value.toFixed(2)),
    denomination_details: validLines.length > 0 ? JSON.stringify(validLines) : null,
  }
}

async function saveChanges(): Promise<void> {
  saving.value = 'save'
  try {
    await apiUpdateDeposit(props.deposit.id, buildUpdatePayload())
    toast.add({ severity: 'success', summary: t('bank.deposit_actions_saved'), life: 3000 })
    emit('update:visible', false)
    emit('updated')
  } catch (err) {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), detail: getErrorDetail(err), life: 5000 })
  } finally {
    saving.value = false
  }
}

function confirmDeposit(): void {
  confirm.require({
    message: t('bank.deposit_confirm_confirm_msg'),
    header: t('bank.deposit_confirm'),
    icon: 'pi pi-check-circle',
    acceptSeverity: 'success',
    acceptLabel: t('bank.deposit_confirm'),
    rejectLabel: t('common.cancel'),
    accept: async () => {
      saving.value = 'confirm'
      try {
        // First apply pending changes, then confirm
        await apiUpdateDeposit(props.deposit.id, buildUpdatePayload())
        await apiConfirmDeposit(props.deposit.id)
        toast.add({ severity: 'success', summary: t('bank.deposit_confirmed_success'), life: 3000 })
        emit('update:visible', false)
        emit('updated')
      } catch (err) {
        toast.add({ severity: 'error', summary: t('common.error.unknown'), detail: getErrorDetail(err), life: 5000 })
      } finally {
        saving.value = false
      }
    },
  })
}

function cancelDeposit(): void {
  confirm.require({
    message: t('bank.deposit_cancel_confirm_msg'),
    header: t('bank.deposit_actions_cancel_deposit'),
    icon: 'pi pi-exclamation-triangle',
    acceptSeverity: 'danger',
    acceptLabel: t('bank.deposit_actions_cancel_deposit'),
    rejectLabel: t('common.cancel'),
    accept: async () => {
      saving.value = 'delete'
      try {
        await apiDeleteDeposit(props.deposit.id)
        toast.add({ severity: 'success', summary: t('bank.deposit_actions_cancelled'), life: 3000 })
        emit('update:visible', false)
        emit('cancelled')
      } catch (err) {
        toast.add({ severity: 'error', summary: t('common.error.unknown'), detail: getErrorDetail(err), life: 5000 })
      } finally {
        saving.value = false
      }
    },
  })
}
</script>

<style scoped>
.bank-deposit-actions__footer {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--p-surface-200);
  margin-top: 1rem;
}

.bank-deposit-actions__left,
.bank-deposit-actions__right {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.bank-deposit-actions__total {
  font-size: 0.9rem;
  color: var(--p-text-muted-color);
  margin-top: 0.25rem;
}
</style>
