<template>
  <AppPage width="wide">
    <AppPageHeader
      :eyebrow="t('dashboard.title')"
      :title="t('dashboard.overview')"
      :subtitle="overviewSubtitle"
    >
      <template #actions>
        <Button :label="t('invoices.new')" icon="pi pi-plus" @click="invoiceWizardVisible = true" />
      </template>
    </AppPageHeader>

    <section v-if="loading" class="app-stat-grid" aria-busy="true">
      <Skeleton v-for="n in 4" :key="n" height="132px" border-radius="12px" />
    </section>

    <template v-else>
      <!-- Net treasury hero -->
      <AppPanel>
        <div class="dashboard-hero">
          <div class="dashboard-hero__main">
            <p class="dashboard-hero__eyebrow">{{ t('dashboard.net_treasury') }}</p>
            <p class="dashboard-hero__amount">{{ formatAmount(netTreasury) }}</p>
            <div class="dashboard-hero__delta-row">
              <span
                v-if="treasuryDelta != null"
                class="dashboard-hero__delta"
                :class="treasuryDelta >= 0 ? 'dashboard-hero__delta--up' : 'dashboard-hero__delta--down'"
              >
                {{ treasuryDelta >= 0 ? '+' : '' }}{{ formatPercent(treasuryDelta) }}
              </span>
              <span class="dashboard-hero__delta-label">{{ t('dashboard.vs_last_month') }}</span>
            </div>
            <svg
              v-if="sparklinePath"
              class="dashboard-hero__sparkline"
              viewBox="0 0 100 32"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              <path :d="sparklineAreaPath" class="dashboard-hero__spark-area" />
              <path :d="sparklinePath" class="dashboard-hero__spark-line" />
            </svg>
          </div>
          <ul class="dashboard-hero__breakdown">
            <li>
              <span>{{ t('dashboard.bank_balance') }}</span>
              <strong>{{ formatAmount(kpis?.bank_balance) }}</strong>
            </li>
            <li>
              <span>{{ t('dashboard.bank_epargne_balance') }}</span>
              <strong>{{ formatAmount(kpis?.bank_epargne_balance) }}</strong>
            </li>
            <li>
              <span>{{ t('dashboard.cash_balance') }}</span>
              <strong>{{ formatAmount(kpis?.cash_balance) }}</strong>
            </li>
          </ul>
        </div>
      </AppPanel>

      <!-- Worklist + quick actions -->
      <div class="dashboard-grid">
        <AppPanel dense>
          <AppWorklist
            :title="t('dashboard.worklist_title')"
            :items="worklistItems"
            :count-severity="worklistItems.length ? 'danger' : 'default'"
            :empty-label="t('dashboard.worklist_empty')"
          />
        </AppPanel>

        <AppPanel :title="t('dashboard.quick_actions_title')" dense>
          <section class="dashboard-quick-actions" :aria-label="t('dashboard.quick_actions_title')">
            <button class="dashboard-action-card" @click="invoiceWizardVisible = true">
              <span class="dashboard-action-card__icon"><i class="pi pi-file-plus" /></span>
              <span class="dashboard-action-card__body">
                <span class="dashboard-action-card__title">{{ t('dashboard.quick_actions.new_invoice') }}</span>
                <span class="dashboard-action-card__desc">{{ t('dashboard.quick_actions.new_invoice_desc') }}</span>
              </span>
              <i class="pi pi-chevron-right dashboard-action-card__arrow" />
            </button>
            <button class="dashboard-action-card" @click="paymentWizardVisible = true">
              <span class="dashboard-action-card__icon"><i class="pi pi-credit-card" /></span>
              <span class="dashboard-action-card__body">
                <span class="dashboard-action-card__title">{{ t('dashboard.quick_actions.new_payment') }}</span>
                <span class="dashboard-action-card__desc">{{ t('dashboard.quick_actions.new_payment_desc') }}</span>
              </span>
              <i class="pi pi-chevron-right dashboard-action-card__arrow" />
            </button>
            <button class="dashboard-action-card" @click="router.push({ name: 'cash', query: { create: '1' } })">
              <span class="dashboard-action-card__icon"><i class="pi pi-wallet" /></span>
              <span class="dashboard-action-card__body">
                <span class="dashboard-action-card__title">{{ t('dashboard.quick_actions.new_cash') }}</span>
                <span class="dashboard-action-card__desc">{{ t('dashboard.quick_actions.new_cash_desc') }}</span>
              </span>
              <i class="pi pi-chevron-right dashboard-action-card__arrow" />
            </button>
          </section>
        </AppPanel>
      </div>

      <BankPendingDepositsPanel
        v-if="pendingDeposits.length"
        :deposits="pendingDeposits"
        @refresh="refreshDeposits"
      />

      <!-- Calm reference figures (non-clickable) -->
      <section class="app-stat-grid dashboard-reference">
        <AppStatCard
          :label="t('dashboard.resultat')"
          :value="kpis?.current_resultat != null ? formatAmount(kpis.current_resultat) : '—'"
          :tone="(kpis?.current_resultat ?? 0) < 0 ? 'danger' : 'success'"
        />
        <AppStatCard :label="t('dashboard.month_income')" :value="formatAmount(lastMonth.produits)" tone="success" />
        <AppStatCard :label="t('dashboard.month_expense')" :value="formatAmount(lastMonth.charges)" />
        <AppStatCard :label="t('dashboard.current_fy')" :value="kpis?.current_fy_name ?? '—'" />
      </section>

      <!-- Single chart: products & charges -->
      <AppPanel :title="t('dashboard.chart_title')" dense>
        <div v-if="chartData.length === 0" class="app-empty-state">
          {{ t('dashboard.chart_empty') }}
        </div>
        <div v-else class="dashboard-chart-card">
          <div class="dashboard-chart-legend">
            <span class="dashboard-chart-legend__item">
              <span class="dashboard-chart-legend__swatch dashboard-chart-legend__swatch--charges" />
              {{ t('dashboard.chart_legend_charges') }}
            </span>
            <span class="dashboard-chart-legend__item">
              <span class="dashboard-chart-legend__swatch dashboard-chart-legend__swatch--produits" />
              {{ t('dashboard.chart_legend_produits') }}
            </span>
          </div>

          <div class="dashboard-chart" role="img" :aria-label="t('dashboard.chart_title')">
            <div v-for="row in chartBars" :key="row.month" class="dashboard-chart__column">
              <div class="dashboard-chart__values">
                <span>{{ formatCompactAmount(row.charges) }}</span>
                <span>{{ formatCompactAmount(row.produits) }}</span>
              </div>
              <div class="dashboard-chart__bars">
                <span
                  class="dashboard-chart__bar dashboard-chart__bar--charges"
                  :style="{ height: `${row.chargesHeight}%` }"
                  :title="`${t('dashboard.chart_charges')} : ${formatAmount(row.charges)}`"
                />
                <span
                  class="dashboard-chart__bar dashboard-chart__bar--produits"
                  :style="{ height: `${row.produitsHeight}%` }"
                  :title="`${t('dashboard.chart_produits')} : ${formatAmount(row.produits)}`"
                />
              </div>
              <span class="dashboard-chart__month">{{ formatChartMonth(row.month) }}</span>
            </div>
          </div>
        </div>
      </AppPanel>
    </template>

    <QuickPaymentWizard v-model:visible="paymentWizardVisible" />
    <QuickInvoiceWizard v-model:visible="invoiceWizardVisible" />
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import Skeleton from 'primevue/skeleton'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import AppStatCard from '../components/ui/AppStatCard.vue'
import AppWorklist, { type WorklistItem } from '../components/ui/AppWorklist.vue'
import QuickPaymentWizard from '../components/QuickPaymentWizard.vue'
import QuickInvoiceWizard from '../components/QuickInvoiceWizard.vue'
import BankPendingDepositsPanel from '../components/bank/BankPendingDepositsPanel.vue'
import { getDashboardApi, getMonthlyChartApi, getResourcesChartApi } from '../api/accounting'
import type { DashboardKPIs, DashboardResourcesChartRow, MonthlyChartRow } from '../api/accounting'
import { listDeposits } from '../api/bank'
import type { Deposit } from '../api/bank'
import { useFiscalYearStore } from '../stores/fiscalYear'
import { formatCurrency } from '../utils/format'

const { t } = useI18n()
const router = useRouter()
const fiscalYearStore = useFiscalYearStore()

const invoiceWizardVisible = ref(false)
const paymentWizardVisible = ref(false)

const loading = ref(true)
const kpis = ref<DashboardKPIs | null>(null)
const chartData = ref<MonthlyChartRow[]>([])
const resourcesChartData = ref<DashboardResourcesChartRow[]>([])
const pendingDeposits = ref<Deposit[]>([])

// API monetary fields can arrive as Decimal strings — coerce defensively.
function toNum(value: unknown): number {
  const n = typeof value === 'number' ? value : parseFloat(String(value ?? ''))
  return Number.isFinite(n) ? n : 0
}

const netTreasury = computed(
  () =>
    toNum(kpis.value?.bank_balance) +
    toNum(kpis.value?.bank_epargne_balance) +
    toNum(kpis.value?.cash_balance),
)

const sparkValues = computed(() =>
  resourcesChartData.value.map((row) => Number(row.net_resources)).filter((v) => Number.isFinite(v)),
)

const treasuryDelta = computed<number | null>(() => {
  const vals = sparkValues.value
  if (vals.length < 2) return null
  const prev = vals[vals.length - 2]
  const last = vals[vals.length - 1]
  if (!prev) return null
  return ((last - prev) / Math.abs(prev)) * 100
})

const sparklinePath = computed(() => {
  const vals = sparkValues.value
  if (vals.length < 2) return ''
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  const range = max - min || 1
  const stepX = 100 / (vals.length - 1)
  return vals
    .map((v, i) => `${i === 0 ? 'M' : 'L'} ${(i * stepX).toFixed(2)} ${(30 - ((v - min) / range) * 28).toFixed(2)}`)
    .join(' ')
})

const sparklineAreaPath = computed(() =>
  sparklinePath.value ? `${sparklinePath.value} L 100 32 L 0 32 Z` : '',
)

// "Recettes/Dépenses du mois" = the current calendar month. chartData spans the whole
// fiscal year, so its last row is the year's final month (often still in the future and
// empty). Target the current month explicitly, falling back to the last row when the
// displayed fiscal year doesn't contain it (e.g. a past year is selected).
const lastMonth = computed(() => {
  const rows = chartData.value
  if (rows.length === 0) return { month: '', charges: 0, produits: 0 }
  const now = new Date()
  const currentKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  return rows.find((row) => row.month === currentKey) ?? rows.at(-1)!
})

const overviewSubtitle = computed(() => {
  const fy = kpis.value?.current_fy_name ?? fiscalYearStore.selectedFiscalYear?.name ?? '—'
  const date = new Intl.DateTimeFormat('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(new Date())
  return t('dashboard.overview_subtitle', { fy, date })
})

const worklistItems = computed<WorklistItem[]>(() => {
  const k = kpis.value
  if (!k) return []
  const items: WorklistItem[] = []
  if (k.unpaid_count > 0) {
    items.push({
      key: 'unpaid',
      icon: 'pi-file',
      label: t('dashboard.unpaid_invoices'),
      sublabel: t('dashboard.worklist_unpaid_sub', { count: k.unpaid_count }),
      value: formatAmount(k.unpaid_total),
      severity: 'danger',
      to: { name: 'invoices-client', query: { unpaid: '1' } },
    })
  }
  if (k.overdue_count > 0) {
    items.push({
      key: 'overdue',
      icon: 'pi-clock',
      label: t('dashboard.overdue_invoices'),
      sublabel: t('dashboard.worklist_overdue_sub', { count: k.overdue_count }),
      value: formatAmount(k.overdue_total),
      severity: 'danger',
      to: { name: 'invoices-client', query: { status: 'overdue' } },
    })
  }
  if (k.undeposited_count > 0) {
    items.push({
      key: 'undeposited',
      icon: 'pi-wallet',
      label: t('dashboard.undeposited'),
      sublabel: t('dashboard.worklist_undeposited_sub', { count: k.undeposited_count }),
      value: k.undeposited_count,
      severity: 'warn',
      to: { name: 'payments', query: { undeposited: '1' } },
    })
  }
  if (k.to_reconcile_count > 0) {
    items.push({
      key: 'to_reconcile',
      icon: 'pi-building-columns',
      label: t('dashboard.to_reconcile'),
      sublabel: t('dashboard.worklist_reconcile_sub', { count: k.to_reconcile_count }),
      value: k.to_reconcile_count,
      severity: 'warn',
      to: { name: 'bank', query: { reconcile: '1' } },
    })
  }
  return items
})

const chartBars = computed(() => {
  const maxValue = Math.max(1, ...chartData.value.flatMap((row) => [row.charges, row.produits]))
  return chartData.value.map((row) => ({
    ...row,
    chargesHeight: Math.max((row.charges / maxValue) * 100, row.charges > 0 ? 4 : 0),
    produitsHeight: Math.max((row.produits / maxValue) * 100, row.produits > 0 ? 4 : 0),
  }))
})

function formatAmount(v: number | string | null | undefined): string {
  return formatCurrency(v)
}

function formatCompactAmount(v: number): string {
  if (v === 0) {
    return '0 €'
  }
  return new Intl.NumberFormat('fr-FR', {
    notation: 'compact',
    compactDisplay: 'short',
    maximumFractionDigits: 1,
  }).format(v)
}

function formatPercent(v: number): string {
  return `${new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 1 }).format(v)} %`
}

function formatChartMonth(value: string): string {
  const [yearPart, monthPart] = value.split('-')
  const year = Number(yearPart)
  const month = Number(monthPart)
  const parsed = new Date(
    Number.isFinite(year) ? year : 2000,
    (Number.isFinite(month) ? month : 1) - 1,
    1,
  )
  return new Intl.DateTimeFormat('fr-FR', { month: 'short' }).format(parsed)
}

async function loadChart() {
  const fyId = fiscalYearStore.selectedFiscalYearId
  if (!fyId) {
    chartData.value = []
    return
  }
  try {
    chartData.value = await getMonthlyChartApi(fyId)
  } catch {
    chartData.value = []
  }
}

async function loadResourcesChart() {
  try {
    resourcesChartData.value = await getResourcesChartApi(12)
  } catch {
    resourcesChartData.value = []
  }
}

function refreshDeposits() {
  listDeposits({ confirmed: false })
    .then((d) => (pendingDeposits.value = d))
    .catch((e) => console.error('Failed to refresh deposits', e))
}

watch(
  () => fiscalYearStore.selectedFiscalYearId,
  (newId, oldId) => {
    if (!fiscalYearStore.initialized || newId === oldId) return
    void loadChart()
  },
)

onMounted(async () => {
  try {
    await fiscalYearStore.initialize()
    kpis.value = await getDashboardApi()
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
  await Promise.all([
    loadChart(),
    loadResourcesChart(),
    listDeposits({ confirmed: false })
      .then((d) => (pendingDeposits.value = d))
      .catch((e) => console.error('Failed to load deposits', e)),
  ])
})
</script>

<style scoped>
.dashboard-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: var(--app-space-5);
}

.dashboard-reference {
  margin-top: 0;
}

/* ── Treasury hero ─────────────────────────────────────────── */
.dashboard-hero {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: var(--app-space-6);
  align-items: center;
}

.dashboard-hero__eyebrow {
  margin: 0;
  color: var(--p-text-muted-color);
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.dashboard-hero__amount {
  margin: var(--app-space-2) 0 0;
  font-size: 2.75rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  font-variant-numeric: tabular-nums;
}

.dashboard-hero__delta-row {
  display: flex;
  align-items: center;
  gap: var(--app-space-2);
  margin-top: var(--app-space-2);
}

.dashboard-hero__delta {
  display: inline-flex;
  align-items: center;
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.dashboard-hero__delta--up {
  background: color-mix(in srgb, var(--p-green-500, #22c55e) 16%, transparent);
  color: var(--p-green-600, #16a34a);
}

.dashboard-hero__delta--down {
  background: color-mix(in srgb, var(--p-red-500, #ef4444) 16%, transparent);
  color: var(--p-red-500, #dc2626);
}

.dashboard-hero__delta-label {
  color: var(--p-text-muted-color);
  font-size: 0.82rem;
}

.dashboard-hero__sparkline {
  width: 100%;
  height: 3rem;
  margin-top: var(--app-space-4);
  overflow: visible;
}

.dashboard-hero__spark-line {
  fill: none;
  stroke: var(--p-primary-color, #10b981);
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
  vector-effect: non-scaling-stroke;
}

.dashboard-hero__spark-area {
  fill: color-mix(in srgb, var(--p-primary-color, #10b981) 16%, transparent);
  stroke: none;
}

.dashboard-hero__breakdown {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
  margin: 0;
  padding: 0 0 0 var(--app-space-6);
  list-style: none;
  border-left: 1px solid var(--app-surface-border);
}

.dashboard-hero__breakdown li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-3);
}

.dashboard-hero__breakdown span {
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
}

.dashboard-hero__breakdown strong {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
}

/* ── Single chart ──────────────────────────────────────────── */
.dashboard-chart-card {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.dashboard-chart-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--app-space-4);
}

.dashboard-chart-legend__item {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--p-text-muted-color);
  font-size: 0.88rem;
  font-weight: 600;
}

.dashboard-chart-legend__swatch {
  width: 0.85rem;
  height: 0.85rem;
  border-radius: 999px;
}

.dashboard-chart-legend__swatch--charges {
  background: linear-gradient(180deg, #ea580c 0%, #fb923c 100%);
}

.dashboard-chart-legend__swatch--produits {
  background: linear-gradient(180deg, #15803d 0%, #4ade80 100%);
}

.dashboard-chart {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(4.6rem, 1fr));
  gap: var(--app-space-3);
  align-items: end;
  min-height: 18rem;
}

.dashboard-chart__column {
  display: grid;
  gap: 0.5rem;
}

.dashboard-chart__values {
  display: grid;
  gap: 0.15rem;
  font-size: 0.73rem;
  color: var(--p-text-muted-color);
}

.dashboard-chart__bars {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: end;
  gap: 0.4rem;
  min-height: 13rem;
  padding: 0.75rem 0.55rem;
  border-radius: var(--app-surface-radius-sm);
  background:
    linear-gradient(to top, color-mix(in srgb, var(--app-surface-border) 70%, transparent) 1px, transparent 1px)
      0 0 / 100% 25%,
    color-mix(in srgb, var(--app-surface-muted) 82%, transparent 18%);
  border: 1px solid var(--app-surface-border);
}

.dashboard-chart__bar {
  display: block;
  width: 100%;
  min-height: 0;
  border-radius: 999px 999px 0 0;
}

.dashboard-chart__bar--charges {
  background: linear-gradient(180deg, #ea580c 0%, #fb923c 100%);
}

.dashboard-chart__bar--produits {
  background: linear-gradient(180deg, #15803d 0%, #4ade80 100%);
}

.dashboard-chart__month {
  text-align: center;
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: capitalize;
}

/* ── Quick actions ─────────────────────────────────────────── */
.dashboard-quick-actions {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
}

.dashboard-action-card {
  display: flex;
  align-items: center;
  gap: var(--app-space-3);
  padding: var(--app-space-4);
  border: 1px solid var(--app-surface-border);
  border-radius: var(--app-surface-radius-sm);
  background: color-mix(in srgb, var(--app-surface-bg) 88%, transparent 12%);
  cursor: pointer;
  text-align: left;
  transition:
    background 0.15s,
    border-color 0.15s,
    box-shadow 0.15s;
  width: 100%;
}

.dashboard-action-card:hover {
  border-color: var(--p-primary-400);
  box-shadow: var(--app-surface-shadow);
}

.dashboard-action-card:focus-visible {
  outline: 2px solid var(--p-primary-500);
  outline-offset: 2px;
}

.dashboard-action-card__icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  background: color-mix(in srgb, var(--p-primary-100) 70%, transparent);
  color: var(--p-primary-600);
  font-size: 1.15rem;
}

html.dark-mode .dashboard-action-card__icon {
  background: color-mix(in srgb, var(--p-primary-500) 22%, transparent);
  color: var(--p-primary-300);
}

.dashboard-action-card__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 0;
}

.dashboard-action-card__title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--p-text-color);
}

.dashboard-action-card__desc {
  font-size: 0.8rem;
  color: var(--p-text-muted-color);
  line-height: 1.35;
}

.dashboard-action-card__arrow {
  flex-shrink: 0;
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
}

@media (max-width: 900px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .dashboard-hero {
    grid-template-columns: 1fr;
    gap: var(--app-space-4);
  }

  .dashboard-hero__breakdown {
    padding-left: 0;
    border-left: none;
    border-top: 1px solid var(--app-surface-border);
    padding-top: var(--app-space-4);
  }

  .dashboard-chart {
    grid-template-columns: repeat(auto-fit, minmax(4rem, 1fr));
  }
}
</style>
