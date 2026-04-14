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
          :value="kpis?.unpaid_count ?? 0"
          :caption="kpis ? formatAmount(kpis.unpaid_total) : '—'"
        />
        <AppStatCard
          :label="t('dashboard.overdue_invoices')"
          :value="kpis?.overdue_count ?? 0"
          :caption="kpis ? formatAmount(kpis.overdue_total) : '—'"
          :tone="(kpis?.overdue_count ?? 0) > 0 ? 'danger' : 'warn'"
        />
        <AppStatCard :label="t('dashboard.undeposited')" :value="kpis?.undeposited_count ?? 0" />
        <AppStatCard :label="t('dashboard.current_fy')" :value="kpis?.current_fy_name ?? '—'" />
        <AppStatCard
          :label="t('dashboard.resultat')"
          :value="kpis?.current_resultat != null ? formatAmount(kpis.current_resultat) : '—'"
          :tone="(kpis?.current_resultat ?? 0) < 0 ? 'danger' : 'success'"
        />
      </section>

      <div class="dashboard-grid">
        <AppPanel :title="t('dashboard.chart_title')" dense>
          <template #actions>
            <Select
              v-model="chartYear"
              :options="yearOptions"
              class="dashboard-year-select"
              @change="loadChart"
            />
          </template>
          <div v-if="chartData.length === 0" class="app-empty-state">—</div>
          <div v-else class="dashboard-table-wrap">
            <table class="dashboard-table">
              <thead>
                <tr>
                  <th>{{ t('dashboard.chart_month') }}</th>
                  <th>{{ t('dashboard.chart_charges') }}</th>
                  <th>{{ t('dashboard.chart_produits') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in chartData" :key="row.month">
                  <td>{{ row.month }}</td>
                  <td>{{ formatAmount(row.charges) }}</td>
                  <td>{{ formatAmount(row.produits) }}</td>
                </tr>
              </tbody>
            </table>
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
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Select from 'primevue/select'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import AppStatCard from '../components/ui/AppStatCard.vue'
import { getDashboardApi, getMonthlyChartApi } from '../api/accounting'
import type { DashboardKPIs, MonthlyChartRow } from '../api/accounting'

const { t } = useI18n()

const loading = ref(true)
const kpis = ref<DashboardKPIs | null>(null)
const chartData = ref<MonthlyChartRow[]>([])
const chartYear = ref(new Date().getFullYear())

const yearOptions = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i)

function formatAmount(v: number | null | undefined): string {
  if (v == null) {
    return '—'
  }
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
.dashboard-loading {
  display: flex;
  justify-content: center;
  padding: 4rem 0;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: var(--app-space-5);
}

.dashboard-year-select {
  width: 8rem;
}

.dashboard-table-wrap {
  overflow-x: auto;
}

.dashboard-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.94rem;
}

.dashboard-table th,
.dashboard-table td {
  padding: 0.8rem 0.6rem;
  border-bottom: 1px solid var(--app-surface-border);
}

.dashboard-table th {
  text-align: left;
  color: var(--p-text-muted-color);
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.dashboard-table td:nth-child(2),
.dashboard-table td:nth-child(3),
.dashboard-table th:nth-child(2),
.dashboard-table th:nth-child(3) {
  text-align: right;
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
}
</style>
