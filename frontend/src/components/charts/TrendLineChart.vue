<template>
  <div v-if="rows.length === 0" class="app-empty-state">{{ emptyLabel }}</div>
  <div v-else class="trend-chart-card">
    <div class="trend-chart-legend">
      <span v-for="item in series" :key="item.key" class="trend-chart-legend__item">
        <span class="trend-chart-legend__swatch" :style="swatchStyle(item)" />
        <span class="trend-chart-legend__label">{{ item.label }}</span>
        <strong class="trend-chart-legend__value">{{ formatAmount(latestValue(item.key)) }}</strong>
      </span>
    </div>

    <div class="trend-chart-layout">
      <div class="trend-chart__y-axis" aria-hidden="true">
        <span v-for="tick in yAxisTicks" :key="tick.index" class="trend-chart__y-axis-label">
          {{ tick.label }}
        </span>
      </div>

      <div class="trend-chart" role="img" :aria-label="ariaLabel">
        <svg class="trend-chart__svg" viewBox="0 0 100 100" preserveAspectRatio="none">
          <defs>
            <linearGradient
              v-for="item in series"
              :id="gradientId(item.key)"
              :key="gradientId(item.key)"
              x1="0"
              y1="0"
              x2="0"
              y2="1"
            >
              <stop offset="0%" :stop-color="item.color" stop-opacity="0.26" />
              <stop offset="100%" :stop-color="item.color" stop-opacity="0.02" />
            </linearGradient>
          </defs>

          <line
            v-for="gridLine in gridLines"
            :key="gridLine"
            class="trend-chart__grid-line"
            x1="0"
            :y1="gridLine"
            x2="100"
            :y2="gridLine"
          />

          <path
            v-for="item in filledSeries"
            :key="`${item.key}-area`"
            class="trend-chart__area"
            :d="areaPath(item.key)"
            :fill="`url(#${gradientId(item.key)})`"
          />

          <path
            v-for="item in series"
            :key="`${item.key}-line`"
            class="trend-chart__line"
            :class="{ 'trend-chart__line--dashed': item.dashed }"
            :d="linePath(item.key)"
            :stroke="item.color"
          />

          <circle
            v-for="point in circlePoints"
            :key="`${point.key}-${point.month}`"
            class="trend-chart__point"
            :cx="point.x"
            :cy="point.y"
            r="1.2"
            :fill="point.color"
          />
        </svg>
      </div>
    </div>

    <div class="trend-chart__months-layout">
      <span class="trend-chart__months-spacer" aria-hidden="true" />
      <div class="trend-chart__months">
        <span v-for="row in rows" :key="row.month" class="trend-chart__month">
          {{ formatMonth(row.month) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export interface TrendLineChartSeries {
  key: string
  label: string
  color: string
  fill?: boolean
  dashed?: boolean
}

type TrendLineChartRow = {
  month: string
} & Record<string, number | string>

const props = withDefaults(
  defineProps<{
    data: TrendLineChartRow[]
    series: TrendLineChartSeries[]
    emptyLabel: string
    ariaLabel: string
  }>(),
  {},
)

const rows = computed(() => props.data)

const gridLines = [8, 29, 50, 71, 92]

const filledSeries = computed(() => props.series.filter((item) => item.fill))

const yAxisTicks = computed(() => {
  const { min, max } = chartRange.value
  return gridLines.map((_, index) => {
    const ratio = index / Math.max(gridLines.length - 1, 1)
    const value = max - (max - min) * ratio
    return {
      index,
      label: formatAxisAmount(value),
    }
  })
})

const numericValues = computed(() =>
  rows.value.flatMap((row) =>
    props.series.map((item) => Number(row[item.key] ?? 0)).filter((value) => Number.isFinite(value)),
  ),
)

const chartRange = computed(() => {
  if (numericValues.value.length === 0) {
    return { min: 0, max: 1 }
  }
  const rawMin = Math.min(...numericValues.value)
  const rawMax = Math.max(...numericValues.value)
  const min = rawMin >= 0 ? 0 : rawMin
  if (rawMin === rawMax) {
    return { min, max: rawMax === 0 ? 1 : rawMax * 1.2 }
  }
  const padding = (rawMax - min) * 0.08
  return { min, max: rawMax + padding }
})

const circlePoints = computed(() =>
  props.series.flatMap((item) =>
    rows.value.map((row, index) => ({
      key: item.key,
      month: row.month,
      x: pointX(index),
      y: pointY(Number(row[item.key] ?? 0)),
      color: item.color,
    })),
  ),
)

function pointX(index: number): number {
  if (rows.value.length <= 1) {
    return 50
  }
  return (index / (rows.value.length - 1)) * 100
}

function pointY(value: number): number {
  const { min, max } = chartRange.value
  const ratio = (value - min) / Math.max(max - min, 1)
  return 92 - ratio * 84
}

function linePath(key: string): string {
  return rows.value
    .map((row, index) => `${index === 0 ? 'M' : 'L'} ${pointX(index)} ${pointY(Number(row[key] ?? 0))}`)
    .join(' ')
}

function areaPath(key: string): string {
  if (rows.value.length === 0) {
    return ''
  }
  const firstX = pointX(0)
  const lastX = pointX(rows.value.length - 1)
  return `${linePath(key)} L ${lastX} 92 L ${firstX} 92 Z`
}

function formatAmount(value: number): string {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(value)
}

function formatAxisAmount(value: number): string {
  if (Math.abs(value) >= 1000) {
    return `${new Intl.NumberFormat('fr-FR', {
      notation: 'compact',
      compactDisplay: 'short',
      maximumFractionDigits: 1,
    }).format(value)} €`
  }
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(value)
}

function formatMonth(value: string): string {
  const [yearPart, monthPart] = value.split('-')
  const year = Number(yearPart)
  const month = Number(monthPart)
  const parsed = new Date(year, month - 1, 1)
  return new Intl.DateTimeFormat('fr-FR', { month: 'short' }).format(parsed)
}

function latestValue(key: string): number {
  return Number(rows.value.at(-1)?.[key] ?? 0)
}

function gradientId(key: string): string {
  return `trend-gradient-${key}`
}

function swatchStyle(item: TrendLineChartSeries): { background: string } {
  return {
    background: item.fill
      ? `linear-gradient(180deg, ${item.color} 0%, color-mix(in srgb, ${item.color} 65%, white 35%) 100%)`
      : item.color,
  }
}
</script>

<style scoped>
.trend-chart-card {
  --trend-chart-axis-width: 4.5rem;

  display: grid;
  gap: var(--app-space-4);
}

.trend-chart-layout,
.trend-chart__months-layout {
  display: grid;
  grid-template-columns: var(--trend-chart-axis-width) minmax(0, 1fr);
  gap: 0.75rem;
}

.trend-chart__y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 17rem;
  padding: 0.9rem 0 0.55rem;
}

.trend-chart__y-axis-label {
  color: var(--p-text-muted-color);
  font-size: 0.74rem;
  font-weight: 700;
  line-height: 1;
}

.trend-chart-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.trend-chart-legend__item {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--app-surface-border);
  border-radius: 999px;
  background: color-mix(in srgb, var(--app-surface-muted) 74%, transparent 26%);
}

.trend-chart-legend__swatch {
  width: 0.8rem;
  height: 0.8rem;
  border-radius: 999px;
  flex: none;
}

.trend-chart-legend__label {
  color: var(--p-text-muted-color);
  font-size: 0.82rem;
  font-weight: 600;
}

.trend-chart-legend__value {
  font-size: 0.84rem;
}

.trend-chart {
  position: relative;
  min-height: 17rem;
  padding: 0.9rem 0.75rem 0.55rem;
  border-radius: var(--app-surface-radius-sm);
  border: 1px solid var(--app-surface-border);
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--app-surface-muted) 80%, transparent 20%), transparent 44%),
    color-mix(in srgb, var(--app-surface-bg) 88%, var(--app-surface-muted) 12%);
}

.trend-chart__svg {
  width: 100%;
  height: 16rem;
  overflow: visible;
}

.trend-chart__grid-line {
  stroke: color-mix(in srgb, var(--app-surface-border) 82%, transparent 18%);
  stroke-width: 0.4;
  stroke-dasharray: 1.6 1.8;
}

.trend-chart__area {
  opacity: 1;
}

.trend-chart__line {
  fill: none;
  stroke-width: 1.9;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.trend-chart__line--dashed {
  stroke-dasharray: 3 2;
}

.trend-chart__point {
  filter: drop-shadow(0 0 0.2rem rgba(15, 23, 42, 0.2));
}

.trend-chart__months {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(0, 1fr));
  gap: 0.35rem;
}

.trend-chart__month {
  text-align: center;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: capitalize;
  color: var(--p-text-muted-color);
}

.trend-chart__months-spacer {
  display: block;
}

@media (max-width: 720px) {
  .trend-chart-card {
    --trend-chart-axis-width: 3.75rem;
  }

  .trend-chart {
    min-height: 14rem;
  }

  .trend-chart__y-axis {
    min-height: 14rem;
  }

  .trend-chart__svg {
    height: 13rem;
  }

  .trend-chart-legend__item {
    width: 100%;
    justify-content: space-between;
  }
}
</style>