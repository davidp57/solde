<template>
  <div class="dashboard-view p-4">
    <h2 class="text-2xl font-semibold mb-6">{{ t('dashboard.title') }}</h2>

    <!-- KPI cards -->
    <div v-if="loading" class="flex justify-center py-10">
      <ProgressSpinner />
    </div>
    <div v-else class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      <Card class="kpi-card">
        <template #title>{{ t('dashboard.bank_balance') }}</template>
        <template #content>
          <div class="kpi-value">
            {{ kpis?.bank_balance != null ? formatAmount(kpis.bank_balance) : '—' }}
          </div>
        </template>
      </Card>
      <Card class="kpi-card">
        <template #title>{{ t('dashboard.cash_balance') }}</template>
        <template #content>
          <div class="kpi-value">
            {{ kpis?.cash_balance != null ? formatAmount(kpis.cash_balance) : '—' }}
          </div>
        </template>
      </Card>
      <Card class="kpi-card">
        <template #title>{{ t('dashboard.unpaid_invoices') }}</template>
        <template #content>
          <div class="kpi-value">{{ kpis?.unpaid_count ?? 0 }}</div>
          <div class="kpi-sub">{{ kpis ? formatAmount(kpis.unpaid_total) : '—' }}</div>
        </template>
      </Card>
      <Card class="kpi-card" :class="{ 'kpi-card--alert': (kpis?.overdue_count ?? 0) > 0 }">
        <template #title>{{ t('dashboard.overdue_invoices') }}</template>
        <template #content>
          <div class="kpi-value">{{ kpis?.overdue_count ?? 0 }}</div>
          <div class="kpi-sub">{{ kpis ? formatAmount(kpis.overdue_total) : '—' }}</div>
        </template>
      </Card>
    </div>

    <!-- Second row -->
    <div v-if="!loading" class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
      <Card class="kpi-card">
        <template #title>{{ t('dashboard.undeposited') }}</template>
        <template #content>
          <div class="kpi-value">{{ kpis?.undeposited_count ?? 0 }}</div>
        </template>
      </Card>
      <Card class="kpi-card">
        <template #title>{{ t('dashboard.current_fy') }}</template>
        <template #content>
          <div class="kpi-value text-base">{{ kpis?.current_fy_name ?? '—' }}</div>
        </template>
      </Card>
      <Card class="kpi-card" :class="{ 'kpi-card--neg': (kpis?.current_resultat ?? 0) < 0 }">
        <template #title>{{ t('dashboard.resultat') }}</template>
        <template #content>
          <div class="kpi-value">
            {{ kpis?.current_resultat != null ? formatAmount(kpis.current_resultat) : '—' }}
          </div>
        </template>
      </Card>
    </div>

    <!-- Alerts -->
    <div v-if="!loading && kpis && kpis.alerts.length > 0" class="mb-8">
      <h3 class="text-lg font-medium mb-2">{{ t('dashboard.alerts_title') }}</h3>
      <Message
        v-for="(alert, idx) in kpis.alerts"
        :key="idx"
        :severity="alert.type === 'overdue' ? 'warn' : 'info'"
        class="mb-1"
      >
        {{ alert.message }}
      </Message>
    </div>

    <!-- Monthly chart -->
    <Card v-if="!loading" class="mb-4">
      <template #title>
        <div class="flex items-center gap-4">
          {{ t('dashboard.chart_title') }}
          <Select
            v-model="chartYear"
            :options="yearOptions"
            class="w-28 text-sm"
            @change="loadChart"
          />
        </div>
      </template>
      <template #content>
        <div v-if="chartData.length === 0" class="text-center text-gray-400 py-6">—</div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full text-sm">
            <thead>
              <tr>
                <th class="text-left pr-4 py-1">Mois</th>
                <th class="text-right pr-4 py-1">{{ t('dashboard.chart_charges') }}</th>
                <th class="text-right py-1">{{ t('dashboard.chart_produits') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in chartData"
                :key="row.month"
                class="border-t border-surface-200"
              >
                <td class="pr-4 py-1">{{ row.month }}</td>
                <td class="text-right pr-4 py-1">{{ formatAmount(row.charges) }}</td>
                <td class="text-right py-1">{{ formatAmount(row.produits) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { getDashboardApi, getMonthlyChartApi } from '../api/accounting'
import type { DashboardKPIs, MonthlyChartRow } from '../api/accounting'

const { t } = useI18n()

const loading = ref(true)
const kpis = ref<DashboardKPIs | null>(null)
const chartData = ref<MonthlyChartRow[]>([])
const chartYear = ref(new Date().getFullYear())

const yearOptions = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i)

function formatAmount(v: number): string {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(v)
}

async function loadChart() {
  try {
    chartData.value = await getMonthlyChartApi(chartYear.value)
  } catch {
    // non-blocking
  }
}

onMounted(async () => {
  try {
    kpis.value = await getDashboardApi()
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
  await loadChart()
})
</script>

<style scoped>
.kpi-card {
  min-width: 0;
}
.kpi-value {
  font-size: 1.5rem;
  font-weight: 700;
  margin-top: 0.25rem;
}
.kpi-sub {
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
  margin-top: 0.125rem;
}
.kpi-card--alert :deep(.p-card-title) {
  color: var(--p-orange-500);
}
.kpi-card--neg .kpi-value {
  color: var(--p-red-500);
}
</style>

