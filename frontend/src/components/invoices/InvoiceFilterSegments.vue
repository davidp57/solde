<template>
  <div class="invoice-segments" role="tablist" :aria-label="ariaLabel">
    <button
      v-for="segment in segments"
      :key="segment.key"
      type="button"
      role="tab"
      :aria-selected="segment.key === modelValue"
      :class="[
        'invoice-segments__chip',
        { 'invoice-segments__chip--active': segment.key === modelValue },
      ]"
      @click="emit('update:modelValue', segment.key)"
    >
      <span class="invoice-segments__label">{{ segment.label }}</span>
      <span class="invoice-segments__count">{{ segment.count }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
export interface InvoiceFilterSegment {
  key: string
  label: string
  count: number
}

defineProps<{
  segments: InvoiceFilterSegment[]
  modelValue: string
  ariaLabel?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [key: string]
}>()
</script>

<style scoped>
.invoice-segments {
  display: flex;
  gap: var(--app-space-2);
  overflow-x: auto;
  padding-bottom: var(--app-space-1);
  scrollbar-width: thin;
}

.invoice-segments__chip {
  flex: none;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.85rem;
  border: 1px solid var(--app-surface-border);
  border-radius: 999px;
  background: var(--app-surface-bg);
  color: var(--p-text-color);
  font-size: 0.86rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition:
    background 0.15s,
    border-color 0.15s,
    color 0.15s;
}

.invoice-segments__chip:hover {
  border-color: var(--p-primary-400);
}

.invoice-segments__chip:focus-visible {
  outline: 2px solid var(--p-primary-500);
  outline-offset: 2px;
}

/* Active = dark slate fill in light mode. */
.invoice-segments__chip--active {
  background: var(--p-text-color);
  border-color: var(--p-text-color);
  color: var(--app-surface-bg);
}

/* In dark mode a light fill is too harsh — use a subtle emerald-tinted surface. */
html.dark-mode .invoice-segments__chip--active {
  background: color-mix(in srgb, var(--p-primary-500) 20%, var(--app-surface-bg));
  border-color: var(--p-primary-500);
  color: var(--p-text-color);
}

.invoice-segments__count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.4rem;
  height: 1.4rem;
  padding: 0 0.4rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--app-surface-border) 55%, transparent);
  font-size: 0.76rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.invoice-segments__chip--active .invoice-segments__count {
  background: color-mix(in srgb, var(--app-surface-bg) 28%, transparent);
  color: var(--app-surface-bg);
}

html.dark-mode .invoice-segments__chip--active .invoice-segments__count {
  background: color-mix(in srgb, var(--p-primary-500) 30%, transparent);
  color: var(--p-text-color);
}
</style>
