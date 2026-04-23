<script setup lang="ts">
import { RouterView } from 'vue-router'
import Toast from 'primevue/toast'
import AppOfflineBanner from './components/ui/AppOfflineBanner.vue'
import AppSessionWarning from './components/ui/AppSessionWarning.vue'
</script>

<template>
  <RouterView />
  <Toast />
  <AppOfflineBanner />
  <AppSessionWarning />
</template>
