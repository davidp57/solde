<template>
  <Transition name="session-warning">
    <div v-if="isExpiringSoon" class="session-warning" role="alert" aria-live="polite">
      <i class="pi pi-clock session-warning__icon" />
      <span class="session-warning__text">{{ t('auth.session_expiring_soon') }}</span>
      <Button
        :label="t('auth.session_extend')"
        size="small"
        severity="contrast"
        outlined
        @click="extendSession"
      />
      <Button
        icon="pi pi-times"
        size="small"
        severity="contrast"
        text
        :aria-label="t('common.cancel')"
        @click="dismissWarning"
      />
    </div>
  </Transition>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import { useI18n } from 'vue-i18n'
import { useSessionExpiry } from '../../composables/useSessionExpiry'

const { t } = useI18n()
const { isExpiringSoon, dismissWarning, extendSession } = useSessionExpiry()
</script>

<style scoped>
.session-warning {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 9998;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 1.25rem;
  background: var(--p-amber-600);
  color: #fff;
  font-size: 0.875rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.session-warning__icon {
  flex-shrink: 0;
  font-size: 1rem;
}

.session-warning__text {
  flex: 1;
}

.session-warning-enter-active,
.session-warning-leave-active {
  transition: transform 0.25s ease;
}

.session-warning-enter-from,
.session-warning-leave-to {
  transform: translateY(-100%);
}
</style>
