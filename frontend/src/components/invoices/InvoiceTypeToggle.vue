<template>
  <div class="invoice-type-toggle" role="group" :aria-label="t('invoices.type_toggle.label')">
    <RouterLink
      :to="{ name: 'invoices-client' }"
      :aria-current="type === 'client' ? 'page' : undefined"
      :class="['invoice-type-toggle__tab', { 'invoice-type-toggle__tab--active': type === 'client' }]"
    >
      <i class="pi pi-users" aria-hidden="true" />
      <span>{{ t('invoices.type_toggle.client') }}</span>
    </RouterLink>
    <RouterLink
      :to="{ name: 'invoices-supplier' }"
      :aria-current="type === 'supplier' ? 'page' : undefined"
      :class="['invoice-type-toggle__tab', { 'invoice-type-toggle__tab--active': type === 'supplier' }]"
    >
      <i class="pi pi-building-columns" aria-hidden="true" />
      <span>{{ t('invoices.type_toggle.supplier') }}</span>
    </RouterLink>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'

defineProps<{
  type: 'client' | 'supplier'
}>()

const { t } = useI18n()
</script>

<style scoped>
.invoice-type-toggle {
  display: inline-flex;
  gap: 0.25rem;
  padding: 0.25rem;
  border: 1px solid var(--app-surface-border);
  border-radius: 999px;
  background: var(--app-surface-bg);
}

.invoice-type-toggle__tab {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 1rem;
  border-radius: 999px;
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
  transition:
    background 0.15s,
    color 0.15s;
}

.invoice-type-toggle__tab:hover {
  color: var(--p-text-color);
}

.invoice-type-toggle__tab--active {
  background: var(--p-text-color);
  color: var(--app-surface-bg);
}

html.dark-mode .invoice-type-toggle__tab--active {
  background: color-mix(in srgb, var(--p-primary-500) 20%, var(--app-surface-bg));
  color: var(--p-text-color);
}
</style>
