<template>
  <section class="app-worklist">
    <header v-if="title || $slots.title" class="app-worklist__header">
      <div class="app-worklist__heading">
        <h2 class="app-worklist__title">
          <slot name="title">{{ title }}</slot>
        </h2>
        <p v-if="subtitle" class="app-worklist__subtitle">{{ subtitle }}</p>
      </div>
      <span class="app-worklist__count" :class="`app-worklist__count--${countSeverity}`">{{ items.length }}</span>
    </header>

    <p v-if="items.length === 0" class="app-empty-state app-worklist__empty">
      {{ emptyLabel }}
    </p>

    <ul v-else class="app-worklist__items">
      <li v-for="item in items" :key="item.key">
        <component
          :is="item.to ? RouterLink : 'div'"
          :to="item.to"
          :class="[
            'app-worklist__item',
            `app-worklist__item--${item.severity ?? 'default'}`,
            { 'app-worklist__item--link': item.to },
          ]"
        >
          <span class="app-worklist__icon">
            <i :class="`pi ${item.icon}`" aria-hidden="true" />
          </span>
          <span class="app-worklist__body">
            <span class="app-worklist__label">{{ item.label }}</span>
            <span v-if="item.sublabel" class="app-worklist__sublabel">{{ item.sublabel }}</span>
          </span>
          <span v-if="item.value != null" class="app-worklist__value">{{ item.value }}</span>
          <i v-if="item.to" class="pi pi-chevron-right app-worklist__chevron" aria-hidden="true" />
        </component>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import type { RouteLocationRaw } from 'vue-router'

export type WorklistSeverity = 'danger' | 'warn' | 'info' | 'success' | 'default'

export interface WorklistItem {
  key: string
  icon: string
  label: string
  sublabel?: string
  value?: string | number
  severity?: WorklistSeverity
  to?: RouteLocationRaw
}

withDefaults(
  defineProps<{
    items: WorklistItem[]
    title?: string
    subtitle?: string
    emptyLabel?: string
    countSeverity?: WorklistSeverity
  }>(),
  {
    title: undefined,
    subtitle: undefined,
    emptyLabel: '',
    countSeverity: 'default',
  },
)
</script>

<style scoped>
.app-worklist {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.app-worklist__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--app-space-3);
}

.app-worklist__title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 800;
  letter-spacing: -0.01em;
}

.app-worklist__subtitle {
  margin: var(--app-space-1) 0 0;
  color: var(--p-text-muted-color);
  font-size: 0.88rem;
}

.app-worklist__count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.6rem;
  height: 1.6rem;
  padding: 0 0.45rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--app-surface-border) 60%, transparent);
  font-size: 0.8rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.app-worklist__count--danger {
  background: color-mix(in srgb, var(--p-red-500, #ef4444) 18%, transparent);
  color: var(--p-red-500, #dc2626);
}

.app-worklist__count--warn {
  background: color-mix(in srgb, var(--p-amber-500, #f59e0b) 20%, transparent);
  color: var(--p-amber-600, #b45309);
}

.app-worklist__items {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
  margin: 0;
  padding: 0;
  list-style: none;
}

.app-worklist__item {
  display: flex;
  align-items: center;
  gap: var(--app-space-3);
  padding: var(--app-space-3) var(--app-space-4);
  border: 1px solid var(--app-surface-border);
  border-radius: var(--app-surface-radius-sm);
  background: color-mix(in srgb, var(--app-surface-bg) 90%, transparent);
  color: inherit;
  text-decoration: none;
}

.app-worklist__item--link {
  cursor: pointer;
  transition:
    border-color 0.15s,
    box-shadow 0.15s,
    transform 0.15s;
}

.app-worklist__item--link:hover {
  box-shadow: var(--app-surface-shadow);
}

.app-worklist__item--danger.app-worklist__item--link:hover {
  border-color: var(--p-red-500, #ef4444);
}

.app-worklist__item--warn.app-worklist__item--link:hover {
  border-color: var(--p-amber-500, #f59e0b);
}

.app-worklist__item--info.app-worklist__item--link:hover {
  border-color: var(--p-blue-500, #3b82f6);
}

.app-worklist__icon {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  font-size: 1.05rem;
  background: color-mix(in srgb, var(--app-surface-border) 45%, transparent);
  color: var(--p-text-muted-color);
}

.app-worklist__item--danger .app-worklist__icon {
  background: color-mix(in srgb, var(--p-red-500, #ef4444) 16%, transparent);
  color: var(--p-red-500, #dc2626);
}

.app-worklist__item--warn .app-worklist__icon {
  background: color-mix(in srgb, var(--p-amber-500, #f59e0b) 18%, transparent);
  color: var(--p-amber-600, #b45309);
}

.app-worklist__item--info .app-worklist__icon {
  background: color-mix(in srgb, var(--p-blue-500, #3b82f6) 16%, transparent);
  color: var(--p-blue-500, #2563eb);
}

.app-worklist__item--success .app-worklist__icon {
  background: color-mix(in srgb, var(--p-green-500, #22c55e) 16%, transparent);
  color: var(--p-green-600, #16a34a);
}

.app-worklist__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.app-worklist__label {
  font-weight: 700;
  font-size: 0.92rem;
}

.app-worklist__sublabel {
  color: var(--p-text-muted-color);
  font-size: 0.82rem;
}

.app-worklist__value {
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.app-worklist__item--danger .app-worklist__value {
  color: var(--p-red-500, #dc2626);
}

.app-worklist__item--warn .app-worklist__value {
  color: var(--p-amber-600, #b45309);
}

.app-worklist__chevron {
  flex: none;
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
}
</style>
