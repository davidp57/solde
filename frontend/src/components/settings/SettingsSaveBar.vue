<template>
  <div class="settings-save-bar">
    <span class="settings-save-bar__status" :class="dirty ? 'is-dirty' : 'is-clean'">
      <i :class="dirty ? 'pi pi-circle-fill' : 'pi pi-check-circle'" aria-hidden="true" />
      {{ dirty ? t('settings.unsaved') : t('settings.up_to_date') }}
    </span>
    <div class="settings-save-bar__actions">
      <Button
        type="button"
        :label="t('common.cancel')"
        severity="secondary"
        outlined
        size="small"
        :disabled="!dirty || loading"
        @click="emit('cancel')"
      />
      <Button
        type="button"
        :label="t('common.save')"
        icon="pi pi-check"
        size="small"
        :disabled="!dirty"
        :loading="loading"
        @click="emit('save')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'

defineProps<{
  dirty: boolean
  loading?: boolean
}>()

const emit = defineEmits<{
  save: []
  cancel: []
}>()

const { t } = useI18n()
</script>

<style scoped>
.settings-save-bar {
  position: sticky;
  bottom: 0;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-3);
  padding: var(--app-space-3) var(--app-space-4);
  border: 1px solid var(--app-surface-border);
  border-radius: var(--app-surface-radius-sm);
  background: color-mix(in srgb, var(--app-surface-bg) 92%, transparent);
  backdrop-filter: blur(6px);
  box-shadow: var(--app-surface-shadow);
}

.settings-save-bar__status {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.85rem;
  font-weight: 600;
}

.settings-save-bar__status .pi {
  font-size: 0.7rem;
}

.settings-save-bar__status.is-dirty {
  color: var(--p-amber-600, #b45309);
}

.settings-save-bar__status.is-clean {
  color: var(--p-green-600, #16a34a);
}

.settings-save-bar__actions {
  display: inline-flex;
  gap: var(--app-space-2);
}
</style>
