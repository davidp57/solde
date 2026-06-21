<template>
  <AppPanel class="invoice-funnel">
    <div class="invoice-funnel__layout">
      <div class="invoice-funnel__headline">
        <p class="invoice-funnel__eyebrow">{{ remainingLabel }}</p>
        <p class="invoice-funnel__amount">{{ formatAmount(remaining) }}</p>
        <p class="invoice-funnel__summary">
          {{ t('invoices.funnel.summary', { total: formatAmount(totalInvoiced), count: invoiceCount }) }}
        </p>
      </div>

      <div class="invoice-funnel__breakdown">
        <div class="invoice-funnel__bar" role="img" :aria-label="remainingLabel">
          <span
            v-if="collected > 0"
            class="invoice-funnel__segment invoice-funnel__segment--collected"
            :style="{ width: `${pct(collected)}%` }"
          />
          <span
            v-if="upcoming > 0"
            class="invoice-funnel__segment invoice-funnel__segment--upcoming"
            :style="{ width: `${pct(upcoming)}%` }"
          />
          <span
            v-if="overdue > 0"
            class="invoice-funnel__segment invoice-funnel__segment--overdue"
            :style="{ width: `${pct(overdue)}%` }"
          />
        </div>
        <ul class="invoice-funnel__legend">
          <li class="invoice-funnel__legend-item">
            <span class="invoice-funnel__dot invoice-funnel__dot--collected" />
            <span class="invoice-funnel__legend-label">{{ collectedLabel }}</span>
            <strong class="invoice-funnel__legend-value">{{ formatAmount(collected) }}</strong>
          </li>
          <li class="invoice-funnel__legend-item">
            <span class="invoice-funnel__dot invoice-funnel__dot--upcoming" />
            <span class="invoice-funnel__legend-label">{{ t('invoices.funnel.upcoming') }}</span>
            <strong class="invoice-funnel__legend-value">{{ formatAmount(upcoming) }}</strong>
          </li>
          <li class="invoice-funnel__legend-item">
            <span class="invoice-funnel__dot invoice-funnel__dot--overdue" />
            <span class="invoice-funnel__legend-label">{{ t('invoices.funnel.overdue') }}</span>
            <strong class="invoice-funnel__legend-value">{{ formatAmount(overdue) }}</strong>
          </li>
        </ul>
      </div>
    </div>
  </AppPanel>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import AppPanel from '../ui/AppPanel.vue'

const props = defineProps<{
  type: 'client' | 'supplier'
  totalInvoiced: number
  collected: number
  remaining: number
  overdue: number
  invoiceCount: number
}>()

const { t } = useI18n()

const remainingLabel = computed(() =>
  props.type === 'client'
    ? t('invoices.funnel.remaining_client')
    : t('invoices.funnel.remaining_supplier'),
)

const collectedLabel = computed(() =>
  props.type === 'client'
    ? t('invoices.funnel.collected_client')
    : t('invoices.funnel.collected_supplier'),
)

// "Upcoming" is the open balance that is not yet overdue.
const upcoming = computed(() => Math.max(0, props.remaining - props.overdue))

const currencyFormatter = new Intl.NumberFormat('fr-FR', {
  style: 'currency',
  currency: 'EUR',
})

function formatAmount(value: number): string {
  return currencyFormatter.format(value)
}

function pct(value: number): number {
  if (props.totalInvoiced <= 0) return 0
  return Math.min(100, Math.max(0, (value / props.totalInvoiced) * 100))
}
</script>

<style scoped>
.invoice-funnel__layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr);
  gap: var(--app-space-5);
  align-items: center;
}

.invoice-funnel__eyebrow {
  margin: 0;
  color: var(--p-text-muted-color);
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.invoice-funnel__amount {
  margin: var(--app-space-2) 0 0;
  font-size: 2.4rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
  color: var(--p-orange-600, #b45309);
}

.invoice-funnel__summary {
  margin: var(--app-space-2) 0 0;
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
  font-variant-numeric: tabular-nums;
}

.invoice-funnel__breakdown {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.invoice-funnel__bar {
  display: flex;
  width: 100%;
  height: 1.1rem;
  border-radius: 999px;
  overflow: hidden;
  background: color-mix(in srgb, var(--app-surface-border) 60%, transparent);
}

.invoice-funnel__segment {
  display: block;
  height: 100%;
}

.invoice-funnel__segment--collected {
  background: var(--p-green-500, #16a34a);
}

.invoice-funnel__segment--upcoming {
  background: var(--p-yellow-400, #fcd34d);
}

.invoice-funnel__segment--overdue {
  background: var(--p-red-500, #ef4444);
}

.invoice-funnel__legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--app-space-4);
  margin: 0;
  padding: 0;
  list-style: none;
}

.invoice-funnel__legend-item {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.invoice-funnel__legend-label {
  color: var(--p-text-muted-color);
}

.invoice-funnel__legend-value {
  font-variant-numeric: tabular-nums;
}

.invoice-funnel__dot {
  width: 0.7rem;
  height: 0.7rem;
  border-radius: 999px;
  flex: none;
}

.invoice-funnel__dot--collected {
  background: var(--p-green-500, #16a34a);
}

.invoice-funnel__dot--upcoming {
  background: var(--p-yellow-400, #fcd34d);
}

.invoice-funnel__dot--overdue {
  background: var(--p-red-500, #ef4444);
}

@media (max-width: 900px) {
  .invoice-funnel__layout {
    grid-template-columns: 1fr;
    gap: var(--app-space-4);
  }
}
</style>
