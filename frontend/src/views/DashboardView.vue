<template>
  <AppPage width="wide">
    <AppPageHeader :eyebrow="t('ui.page.collection_eyebrow')" :title="t('dashboard.title')" />

    <div v-if="loading" class="dashboard-loading">
      <ProgressSpinner />
    </div>

    <template v-else>
      <section class="app-stat-grid">
        <AppStatCard
          :label="t('dashboard.bank_balance')"
          :value="kpis ? formatAmount(kpis.bank_balance) : '—'"
        />
        <AppStatCard
          :label="t('dashboard.cash_balance')"
          :value="kpis ? formatAmount(kpis.cash_balance) : '—'"
        />
        <AppStatCard
          :label="t('dashboard.unpaid_invoices')"
          :value="kpis ? kpis.unpaid_count : '—'"
          :caption="kpis ? formatAmount(kpis.unpaid_total) : '—'"
        />
        <AppStatCard
          :label="t('dashboard.overdue_invoices')"
          :value="kpis ? kpis.overdue_count : '—'"
          :caption="kpis ? formatAmount(kpis.overdue_total) : '—'"
          :tone="(kpis?.overdue_count ?? 0) > 0 ? 'danger' : 'warn'"
        />
        <AppStatCard
          :label="t('dashboard.undeposited')"
          :value="kpis ? kpis.undeposited_count : '—'"
        />
        <AppStatCard :label="t('dashboard.current_fy')" :value="kpis?.current_fy_name ?? '—'" />
        <AppStatCard
          :label="t('dashboard.resultat')"
          :value="kpis?.current_resultat != null ? formatAmount(kpis.current_resultat) : '—'"
          :tone="(kpis?.current_resultat ?? 0) < 0 ? 'danger' : 'success'"
        />
      </section>

      <AppPanel :title="t('dashboard.resources_title')" dense>
        <p class="dashboard-panel-intro">{{ t('dashboard.resources_formula') }}</p>
        <TrendLineChart
          :data="resourcesChartData"
          :series="resourcesChartSeries"
          :empty-label="t('dashboard.resources_empty')"
          :ariaLabel="t('dashboard.resources_title')"
        />
      </AppPanel>

      <div class="dashboard-grid">
        <AppPanel :title="t('dashboard.chart_title')" dense>
          <template #actions>
            <Select
              v-model="chartFiscalYearId"
              :options="fiscalYears"
              option-label="name"
              option-value="id"
              class="dashboard-year-select"
              @change="loadChart"
            />
          </template>
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

        <AppPanel :title="t('dashboard.alerts_title')" dense>
          <div v-if="!kpis || kpis.alerts.length === 0" class="app-empty-state">
            {{ t('dashboard.no_alerts') }}
          </div>
          <div v-else class="dashboard-alerts">
            <Message
              v-for="(alert, idx) in kpis.alerts"
              :key="idx"
              :severity="alert.type === 'overdue' ? 'warn' : 'info'"
            >
              {{ alert.message }}
            </Message>
          </div>
        </AppPanel>
      </div>
    </template>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Select from 'primevue/select'
import TrendLineChart, {
  type TrendLineChartSeries,
} from '../components/charts/TrendLineChart.vue'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import AppStatCard from '../components/ui/AppStatCard.vue'
import { getDashboardApi, getMonthlyChartApi, getResourcesChartApi } from '../api/accounting'
import type {
  DashboardKPIs,
  DashboardResourcesChartRow,
  MonthlyChartRow,
} from '../api/accounting'
import { useFiscalYearStore } from '../stores/fiscalYear'

const { t } = useI18n()
const fiscalYearStore = useFiscalYearStore()

const loading = ref(true)
const kpis = ref<DashboardKPIs | null>(null)
const chartData = ref<MonthlyChartRow[]>([])
const resourcesChartData = ref<DashboardResourcesChartRow[]>([])
const fiscalYears = computed(() => fiscalYearStore.fiscalYears)
const chartFiscalYearId = computed({
  get: () => fiscalYearStore.selectedFiscalYearId,
  set: (value: number | undefined) => fiscalYearStore.setSelectedFiscalYear(value),
})

const chartBars = computed(() => {
  const maxValue = Math.max(
    1,
    ...chartData.value.flatMap((row) => [row.charges, row.produits]),
  )
  return chartData.value.map((row) => ({
    ...row,
    chargesHeight: Math.max((row.charges / maxValue) * 100, row.charges > 0 ? 4 : 0),
    produitsHeight: Math.max((row.produits / maxValue) * 100, row.produits > 0 ? 4 : 0),
  }))
})

const resourcesChartSeries = computed<TrendLineChartSeries[]>(() => [
  {
    key: 'net_resources',
    label: t('dashboard.resources_total'),
    color: '#0f766e',
    fill: true,
  },
  {
    key: 'liquidities',
    label: t('dashboard.resources_liquidities'),
    color: '#2563eb',
  },
  {
    key: 'client_receivables',
    label: t('dashboard.resources_receivables'),
    color: '#ea580c',
  },
  {
    key: 'undeposited_cheques',
    label: t('dashboard.resources_undeposited_cheques'),
    color: '#ca8a04',
    dashed: true,
  },
  {
    key: 'supplier_payables',
    label: t('dashboard.resources_supplier_payables'),
    color: '#dc2626',
    dashed: true,
  },
])

function formatAmount(v: number | null | undefined): string {
  if (v == null) {
    return '—'
  }
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(v)
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

function formatChartMonth(value: string): string {
  const [yearPart, monthPart] = value.split('-')
  const year = Number(yearPart)
  const month = Number(monthPart)
  const parsed = new Date(Number.isFinite(year) ? year : 2000, (Number.isFinite(month) ? month : 1) - 1, 1)
  return new Intl.DateTimeFormat('fr-FR', { month: 'short' }).format(parsed)
}

async function loadChart() {
  if (!chartFiscalYearId.value) {
    chartData.value = []
    return
  }
  try {
    chartData.value = await getMonthlyChartApi(chartFiscalYearId.value)
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
  await Promise.all([loadChart(), loadResourcesChart()])
})
</script>

<style scoped>
.dashboard-panel-intro {
  margin: 0 0 var(--app-space-4);
  color: var(--p-text-muted-color);
}

.dashboard-loading {
  display: flex;
  justify-content: center;
  padding: 4rem 0;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: var(--app-space-5);
  margin-top: var(--app-space-5);
}

.dashboard-year-select {
  min-width: 12rem;
}

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

.dashboard-alerts {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
}

@media (max-width: 900px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .dashboard-chart {
    grid-template-columns: repeat(auto-fit, minmax(4rem, 1fr));
  }
}
</style>
