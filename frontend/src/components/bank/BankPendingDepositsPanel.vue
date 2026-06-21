<template>
  <AppPanel
    v-if="deposits.length > 0"
    :title="t('bank.pending_deposits_title')"
    :subtitle="t('bank.pending_deposits_subtitle')"
  >
    <div class="bank-pending-deposits">
      <div
        v-for="deposit in deposits"
        :key="deposit.id"
        class="bank-pending-deposit-row"
      >
        <div class="bank-pending-deposit-row__left">
          <div class="bank-pending-deposit-row__top">
            <Tag
              :value="t(`bank.deposit_types.${deposit.type}`)"
              :severity="deposit.type === 'cheques' ? 'info' : 'warn'"
            />
            <span class="bank-pending-deposit-row__date">{{ formatDisplayDate(deposit.date) }}</span>
          </div>
          <Button
            :label="t('bank.deposit_actions_btn')"
            icon="pi pi-ellipsis-h"
            severity="secondary"
            size="small"
            class="bank-pending-deposit-row__btn"
            @click="openActions(deposit)"
          />
        </div>
        <div v-if="deposit.type !== 'cheques' && especeLines(deposit).length" class="bank-pending-deposit-row__denom">
          <span
            v-for="line in especeLines(deposit)"
            :key="line"
            class="bank-pending-deposit-row__denom-line"
          >{{ line }}</span>
          <span class="bank-pending-deposit-row__amount app-money">{{ formatAmount(deposit.total_amount) }}</span>
        </div>
        <div v-else-if="deposit.type !== 'cheques'" class="bank-pending-deposit-row__denom">
          <span class="bank-pending-deposit-row__amount app-money">{{ formatAmount(deposit.total_amount) }}</span>
        </div>
        <div v-else class="bank-pending-deposit-row__denom">
          <span class="bank-pending-deposit-row__denom-line">{{ t('bank.deposit_cheques_summary', { count: deposit.payment_ids.length }) }}</span>
          <span class="bank-pending-deposit-row__amount app-money">{{ formatAmount(deposit.total_amount) }}</span>
        </div>
      </div>
    </div>

    <BankDepositActionsDialog
      v-if="actionsTarget"
      v-model:visible="actionsVisible"
      :deposit="actionsTarget"
      @updated="emit('refresh')"
      @cancelled="emit('refresh')"
    />
  </AppPanel>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import AppPanel from '@/components/ui/AppPanel.vue'
import BankDepositActionsDialog from './BankDepositActionsDialog.vue'
import type { Deposit } from '@/api/bank'
import { formatCurrency, formatDisplayDate } from '@/utils/format'

defineProps<{ deposits: Deposit[] }>()
const emit = defineEmits<{ refresh: [] }>()

const { t } = useI18n()

const actionsVisible = ref(false)
const actionsTarget = ref<Deposit | null>(null)

function openActions(deposit: Deposit): void {
  actionsTarget.value = deposit
  actionsVisible.value = true
}

function formatAmount(value: string | number): string {
  return formatCurrency(value)
}

function especeLines(deposit: Deposit): string[] {
  if (!deposit.denomination_details) return []
  try {
    const lines: { value: number; count: number }[] = JSON.parse(deposit.denomination_details)
    return lines
      .filter((l) => l.count > 0)
      .map(
        (l) =>
          `${l.count}\u00d7${l.value % 1 === 0 ? l.value : l.value.toFixed(2)}\u00a0\u20ac`,
      )
  } catch {
    return []
  }
}
</script>

<style scoped>
.bank-pending-deposits {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
}

.bank-pending-deposit-row {
  display: flex;
  align-items: stretch;
  gap: var(--app-space-4);
  padding: var(--app-space-3) var(--app-space-4);
  background: var(--app-surface-muted);
  border: 1px solid var(--app-surface-border);
  border-radius: var(--app-radius);
}

.bank-pending-deposit-row__left {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: var(--app-space-3);
  flex: 1;
  min-width: 0;
}

.bank-pending-deposit-row__top {
  display: contents;
}

.bank-pending-deposit-row__btn {
  margin-left: auto;
  flex-shrink: 0;
  white-space: nowrap;
}

.bank-pending-deposit-row__date {
  font-variant-numeric: tabular-nums;
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
}

.bank-pending-deposit-row__amount {
  font-weight: 700;
  font-size: 0.82rem;
  text-align: left;
  color: var(--p-green-500);
  white-space: nowrap;
}

.bank-pending-deposit-row__denom {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: var(--app-space-2);
  border-left: 2px solid var(--app-surface-border);
  padding-left: var(--app-space-3);
  flex: 0 0 22rem;
}

.bank-pending-deposit-row__denom-line {
  font-size: 0.82rem;
  font-variant-numeric: tabular-nums;
  color: var(--p-text-muted-color);
  white-space: nowrap;
}

@media (max-width: 767px) {
  .bank-pending-deposit-row__left {
    flex-direction: column;
    align-items: stretch;
    gap: var(--app-space-2);
  }

  .bank-pending-deposit-row__top {
    display: flex;
    align-items: center;
    gap: var(--app-space-2);
    flex-wrap: wrap;
  }

  .bank-pending-deposit-row__btn {
    margin-left: 0;
  }

  .bank-pending-deposit-row__btn :deep(.p-button) {
    width: 100%;
    justify-content: center;
  }

  .bank-pending-deposit-row__denom {
    flex-direction: column;
    align-items: flex-start;
    flex-wrap: nowrap;
    gap: 0.15rem;
    flex: 0 0 auto;
    min-width: 6.5rem;
  }

  .bank-pending-deposit-row__amount {
    padding-top: 0.25rem;
  }
}
</style>
