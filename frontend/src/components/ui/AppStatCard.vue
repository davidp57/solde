<template>
  <article :class="['app-stat-card', `app-stat-card--${tone}`]">
    <p class="app-stat-card__label">{{ label }}</p>
    <p class="app-stat-card__value">{{ value }}</p>
    <p v-if="caption" class="app-stat-card__caption">{{ caption }}</p>
  </article>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    label: string
    value: string | number
    caption?: string
    tone?: 'default' | 'success' | 'warn' | 'danger'
  }>(),
  {
    caption: undefined,
    tone: 'default',
  },
)
</script>