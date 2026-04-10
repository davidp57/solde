<template>
  <section :class="['app-panel', { 'app-panel--dense': dense }]">
    <div v-if="title || subtitle || $slots.actions" class="app-panel__header">
      <div class="app-panel__copy">
        <h2 v-if="title" class="app-panel__title">{{ title }}</h2>
        <p v-if="subtitle" class="app-panel__subtitle">{{ subtitle }}</p>
      </div>
      <div v-if="$slots.actions" class="app-panel__actions">
        <slot name="actions" />
      </div>
    </div>
    <div class="app-panel__body">
      <slot />
    </div>
  </section>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    title?: string
    subtitle?: string
    dense?: boolean
  }>(),
  {
    title: undefined,
    subtitle: undefined,
    dense: false,
  },
)
</script>