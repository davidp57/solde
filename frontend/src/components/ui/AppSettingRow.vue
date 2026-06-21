<template>
  <div class="app-setting-row">
    <div class="app-setting-row__copy">
      <label v-if="htmlFor" :for="htmlFor" class="app-setting-row__label">{{ label }}</label>
      <span v-else class="app-setting-row__label">{{ label }}</span>
      <p v-if="description" class="app-setting-row__description">{{ description }}</p>
      <p v-if="warning" class="app-setting-row__warning">
        <i class="pi pi-exclamation-triangle" aria-hidden="true" />
        {{ warning }}
      </p>
    </div>
    <div class="app-setting-row__control">
      <slot name="control" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  description?: string
  warning?: string
  htmlFor?: string
}>()
</script>

<style scoped>
.app-setting-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--app-space-5);
  padding: var(--app-space-4) 0;
  border-bottom: 1px solid var(--app-surface-border);
}

.app-setting-row:last-child {
  border-bottom: none;
}

.app-setting-row__copy {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  max-width: 46ch;
}

.app-setting-row__label {
  font-weight: 700;
  font-size: 0.95rem;
}

.app-setting-row__description {
  margin: 0;
  color: var(--p-text-muted-color);
  font-size: 0.85rem;
  line-height: 1.45;
}

.app-setting-row__warning {
  margin: 0.15rem 0 0;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--p-amber-600, #b45309);
  font-size: 0.82rem;
}

.app-setting-row__control {
  flex: none;
  width: clamp(10rem, 26vw, 19rem);
  display: flex;
  flex-direction: column;
  align-items: stretch;
}

/* The control fills its column. */
.app-setting-row__control :deep(.p-inputtext),
.app-setting-row__control :deep(.p-select),
.app-setting-row__control :deep(.p-inputnumber),
.app-setting-row__control :deep(.p-password),
.app-setting-row__control :deep(.p-textarea) {
  width: 100%;
}

@media (max-width: 767px) {
  .app-setting-row {
    flex-direction: column;
    gap: var(--app-space-2);
  }

  .app-setting-row__copy {
    max-width: none;
  }

  .app-setting-row__control {
    width: 100%;
  }
}
</style>
