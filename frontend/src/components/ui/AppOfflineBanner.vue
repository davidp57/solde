<template>
  <Transition name="offline-banner">
    <div v-if="isOffline" class="offline-banner" role="status" aria-live="polite">
      <i class="pi pi-wifi offline-banner__icon" aria-hidden="true" />
      <span class="offline-banner__text">
        <strong>{{ t('offline.title') }}</strong>
        {{ t('offline.subtitle') }}
      </span>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useNetworkStatus } from '../../composables/useNetworkStatus'

const { t } = useI18n()
const { isOffline } = useNetworkStatus()
</script>

<style scoped>
.offline-banner {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.75rem 1.25rem;
  background: var(--p-red-600);
  color: #fff;
  font-size: 0.875rem;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.2);
}

.offline-banner__icon {
  flex-shrink: 0;
  font-size: 1rem;
}

.offline-banner__text {
  flex: 1;
}

.offline-banner-enter-active,
.offline-banner-leave-active {
  transition: transform 0.25s ease;
}

.offline-banner-enter-from,
.offline-banner-leave-to {
  transform: translateY(100%);
}
</style>
