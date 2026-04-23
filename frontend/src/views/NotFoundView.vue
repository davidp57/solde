<template>
  <div class="not-found-page">
    <div class="not-found-content">
      <i class="pi pi-exclamation-circle not-found-icon" aria-hidden="true" />
      <h1 class="not-found-title">{{ t('not_found.title') }}</h1>
      <p class="not-found-subtitle">{{ t('not_found.subtitle') }}</p>
      <Button :label="t('not_found.back')" icon="pi pi-home" @click="router.push('/dashboard')" />
    </div>
  </div>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

const { t } = useI18n()
const router = useRouter()
</script>

<style scoped>
.not-found-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 2rem;
}

.not-found-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
  text-align: center;
  max-width: 28rem;
}

.not-found-icon {
  font-size: 4rem;
  color: var(--p-text-muted-color);
}

.not-found-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0;
}

.not-found-subtitle {
  color: var(--p-text-muted-color);
  margin: 0;
}
</style>
